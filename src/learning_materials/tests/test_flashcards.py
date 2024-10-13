from django.test import TestCase
from unittest.mock import patch
from django.contrib.auth import get_user_model
from learning_materials.models import FlashcardModel, Cardset
from learning_materials.learning_resources import Flashcard, Citation
from learning_materials.flashcards.flashcards_service import generate_flashcards, parse_for_anki


User = get_user_model()

class FlashcardGenerationTests(TestCase):
    @patch('learning_materials.flashcards.flashcards_service.ChatOpenAI')  
    @patch('learning_materials.flashcards.flashcards_service.PydanticOutputParser')
    def test_generate_flashcards(self, MockParser, MockModel):
        # Mocking page data
        page = Citation(
            text="Albert Einstein was born in 1879. Water boils at 100 degrees Celsius.",
            page_num=1,
            document_name="sample.pdf"
        )

        # Mocking the model and parser
        mock_flashcard1 = Flashcard(front="Who was born in 1879?", back="Albert Einstein")
        mock_flashcard2 = Flashcard(front="At what temperature does water boil?", back="100 degrees Celsius")

        # Setting document_name and page_num after instantiation
        mock_flashcard1.document_name = page.document_name
        mock_flashcard1.page_num = page.page_num
        mock_flashcard2.document_name = page.document_name
        mock_flashcard2.page_num = page.page_num

        mock_parser = MockParser.return_value
        mock_parser.get_format_instructions.return_value = "Format Instructions"
        mock_parser.parse.return_value = [mock_flashcard1, mock_flashcard2]

        mock_model = MockModel.return_value
        mock_model.invoke.return_value = [mock_flashcard1, mock_flashcard2]

        # Call the function
        flashcards = generate_flashcards(page)

        # Check the results
        self.assertEqual(len(flashcards), 2)
        self.assertEqual(flashcards[0].front, "Who was born in 1879?")
        self.assertEqual(flashcards[0].back, "Albert Einstein")
        self.assertEqual(flashcards[0].page_num, 1)
        self.assertEqual(flashcards[0].document_name, "sample.pdf")
        self.assertEqual(flashcards[1].front, "At what temperature does water boil?")
        self.assertEqual(flashcards[1].back, "100 degrees Celsius")


class FlashcardReviewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpassword")
        self.cardset = Cardset(name="Test Cardset", description="Test Description", subject="Test Subject", user=self.user)
        self.flashcard = FlashcardModel(front="What is AI?", back="Artificial Intelligence", cardset=self.cardset)
        self.flashcard2 = FlashcardModel(front="Who invented Python?", back="Guido van Rossum", cardset=self.cardset)

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
            Flashcard(front="Who invented Python?", back="Guido van Rossum", page_num=1, document_name="sample.pdf")
        ]

        anki_text = parse_for_anki(flashcards)

        expected_text = "What is AI?:Artificial Intelligence\nWho invented Python?:Guido van Rossum\n"
        self.assertEqual(anki_text, expected_text)
