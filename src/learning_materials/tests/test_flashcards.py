from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from learning_materials.models import FlashcardModel, Cardset
from learning_materials.learning_resources import Flashcard, Citation
from learning_materials.flashcards.flashcards_service import (
    generate_flashcards,
    parse_for_anki,
    FlashcardWrapper,
)

User = get_user_model()


class FlashcardGenerationTests(TestCase):
    @patch("learning_materials.flashcards.flashcards_service.ChatOpenAI")
    @patch("learning_materials.flashcards.flashcards_service.PydanticOutputParser")
    def test_generate_flashcards(self, MockParser, MockModel):
        # Mocking page data
        page = Citation(
            text="Albert Einstein was born in 1879. Water boils at 100 degrees Celsius.",
            page_num=1,
            document_name="sample.pdf",
        )

        # Mocking the model and parser
        mock_flashcard1 = Flashcard(
            front="When was Albert Einstein born?", back="1879"
        )
        mock_flashcard2 = Flashcard(
            front="At what temperature does water boil?", back="100 degrees Celsius"
        )

        # Setting document_name and page_num after instantiation
        mock_flashcard1.document_name = page.document_name
        mock_flashcard1.page_num = page.page_num
        mock_flashcard2.document_name = page.document_name
        mock_flashcard2.page_num = page.page_num

        # Create a FlashcardWrapper with the mock flashcards
        mock_wrapper = FlashcardWrapper(flashcards=[mock_flashcard1, mock_flashcard2])
        
        # Set up the parser mock to return the wrapper
        mock_parser = MockParser.return_value
        mock_parser.get_format_instructions.return_value = "Format Instructions"
        
        # Set up the chain mock
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = mock_wrapper
        
        # Make the pipe operation return our mock chain
        mock_model_instance = MockModel.return_value
        mock_model_instance.__or__.return_value = mock_chain
        mock_parser.__or__.return_value = mock_chain

        # Call the function with language parameter
        flashcards = generate_flashcards(page)
        print(flashcards)

        # Check the results
        self.assertEqual(len(flashcards), 2)
        self.assertEqual(flashcards[0].front, "When was Albert Einstein born?")
        self.assertEqual(flashcards[0].back, "1879")
        self.assertEqual(flashcards[0].page_num, 1)
        self.assertEqual(flashcards[0].document_name, "sample.pdf")
        self.assertEqual(flashcards[1].front, "What is the boiling point of water in degrees Celsius?")
        self.assertEqual(flashcards[1].back, "100")


class FlashcardReviewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.cardset = Cardset(
            name="Test Cardset",
            description="Test Description",
            subject="Test Subject",
            user=self.user,
        )
        self.flashcard = FlashcardModel(
            front="What is AI?", back="Artificial Intelligence", cardset=self.cardset
        )
        self.flashcard2 = FlashcardModel(
            front="Who invented Python?", back="Guido van Rossum", cardset=self.cardset
        )

    def test_flashcard_proficiency(self):

        flashcard = self.flashcard

        # Test the initial state
        self.assertEqual(flashcard.proficiency, 0)

        # First review
        flashcard.review(True, self.user)
        self.assertEqual(flashcard.proficiency, 1)

        # Second review
        flashcard.review(True, self.user)
        self.assertEqual(flashcard.proficiency, 2)

        # Third review
        flashcard.review(False, self.user)
        self.assertEqual(flashcard.proficiency, 0)

        # Fourth review
        flashcard.review(True, self.user)
        self.assertEqual(flashcard.proficiency, 1)


class AnkiParsingTests(TestCase):

    def test_parse_for_anki(self):
        flashcards = [
            Flashcard(front="What is AI?", back="Artificial Intelligence"),
            Flashcard(
                front="Who invented Python?",
                back="Guido van Rossum",
                page_num=1,
                document_name="sample.pdf",
            ),
        ]

        anki_text = parse_for_anki(flashcards)

        expected_text = "What is AI?:Artificial Intelligence\nWho invented Python?:Guido van Rossum\n"
        self.assertEqual(anki_text, expected_text)
