from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from learning_materials.flashcards.flashcards_service import (
    generate_flashcards,
    parse_for_anki,
)
from learning_materials.models import FlashcardModel, Cardset, MultipleChoiceQuestionModel, QuestionAnswerModel, QuizModel
from learning_materials.learning_resources import Flashcard
from learning_materials.learning_resources import Page
import re
from rest_framework import status
from learning_materials.knowledge_base.rag_service import post_context
from accounts.models import CustomUser

base = "/api/"

User = get_user_model()


class FlashcardGenerationTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

        self.url = f"{base}flashcards/create/"
        self.valid_pdf_name = "test.pdf"
        self.invalid_pdf_name = "invalid.pdf"
        self.valid_page_num_start = 0
        self.valid_page_num_end = 1
        self.context = """Revenge of the Sith is set three years after the onset of the Clone Wars as established in Attack of the Clones. The Jedi are spread across the galaxy in a full-scale war against the Separatists. The Jedi Council dispatches Jedi Master Obi-Wan Kenobi on a mission to defeat General Grievous, the head of the Separatist army and Count Dooku's former apprentice, to put an end to the war. Meanwhile, after having visions of his wife Padmé Amidala dying in childbirth, Jedi Knight Anakin Skywalker is tasked by the Council to spy on Palpatine, the Supreme Chancellor of the Galactic Republic and, secretly, a Sith Lord. Palpatine manipulates Anakin into turning to the dark side of the Force and becoming his apprentice, Darth Vader, with wide-ranging consequences for the galaxy."""

        self.user = User.objects.create_user(username='flashcardsuser', email='flashcards@example.com', password='StrongP@ss1')
        self.client.force_authenticate(user=self.user)
        
        # Populate rag database
        for i in range(self.valid_page_num_start, self.valid_page_num_end + 1):
            post_context(self.context, i, self.valid_pdf_name)

    def test_generate_flashcards(self):
        page = Page(text=self.context, page_num=self.valid_page_num_start, pdf_name=self.valid_pdf_name)
        flashcards = generate_flashcards(page)
        self.assertIsInstance(flashcards, list)
        self.assertGreater(len(flashcards), 0)
        self.assertIsInstance(flashcards[0], Flashcard)
        self.assertGreater(len(flashcards[0].front), 0)
        self.assertGreater(len(flashcards[0].back), 0)
        self.assertEqual(flashcards[0].pdf_name, self.valid_pdf_name)
        self.assertEqual(flashcards[0].page_num, self.valid_page_num_start)

    def test_parse_for_anki(self):
        page = Page(text=self.context, page_num=self.valid_page_num_start, pdf_name=self.valid_pdf_name)
        flashcards = generate_flashcards(page)
        anki_format = parse_for_anki(flashcards)
        self.assertIsInstance(anki_format, str)
        self.assertTrue(re.search("(.*:.*\n)*(.*:.*)", anki_format))


    def test_invalid_request(self):
        self.assertFalse(Cardset.objects.exists())
        invalid_payload = {}
        response = self.client.post(self.url, invalid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Cardset.objects.exists())

    def test_valid_request(self):
        self.assertFalse(Cardset.objects.exists())
        valid_response = {
            "document": self.valid_pdf_name,
            "start": self.valid_page_num_start,
            "end": self.valid_page_num_end,
            "subject": "Some subject",
        }
        response = self.client.post(self.url, valid_response, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)

        self.assertTrue(Cardset.objects.exists())
        cardset = Cardset.objects.first() 
        flashcards = FlashcardModel.objects.filter(cardset=cardset)
        self.assertGreater(flashcards.count(), 0)

    def test_invalid_end_start_index(self):
        self.assertFalse(Cardset.objects.exists())
        invalid_response = {
            "document": self.valid_pdf_name,
            "start": 1,
            "end": 0,
            "subject": "Some subject",
        }
        response = self.client.post(self.url, invalid_response, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Cardset.objects.exists())

class RagAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = f"{base}search/"
        self.valid_pdf_name = "test.pdf"
        self.invalid_pdf_name = "invalid.pdf"
        self.valid_chat_history = [
            {"role": "user", "response": "What is the capital of India?"},
            {"role": "assistant", "response": "New Delhi"},
        ]
        self.valid_user_input = "This is a user input."
        self.valid_context = "The context."

    def test_invalid_request(self):
        invalid_payload = {}
        response = self.client.post(self.url, invalid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def invalid_pdf_name(self):
        pass

    def test_valid_request_without_chat_history(self):
        valid_response = {
            "documents": [self.valid_pdf_name],
            "user_question": "What is the capital of India?",
        }
        response = self.client.post(self.url, valid_response, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class QuizGenerationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = f"{base}quiz/create/"

        # Create and authenticate a user
        self.user = CustomUser.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

        # Define valid and invalid test data
        self.valid_pdf_name = "test.pdf"
        self.invalid_pdf_name = "invalid.pdf"
        self.valid_page_num_start = 0
        self.valid_page_num_end = 1
        self.context = """
            Artificial intelligence (AI), in its broadest sense, is intelligence exhibited by machines, particularly computer systems.
            It is a field of research in computer science that develops and studies methods and software that enable machines to perceive their environment and use learning and intelligence to take actions that maximize their chances of achieving defined goals.
            [1] Such machines may be called AIs.
        """

        # Populate RAG (Retrieval-Augmented Generation) database
        for i in range(self.valid_page_num_start, self.valid_page_num_end + 1):
            post_context(self.context, i, self.valid_pdf_name)


    def test_invalid_request(self):
        """
        Test that an invalid request (empty payload) returns a 400 Bad Request
        and does not create any QuizModel instances.
        """
        # Ensure no quizzes exist before the test
        self.assertFalse(QuizModel.objects.exists())  

        invalid_payload = {}
        response = self.client.post(self.url, invalid_payload, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Ensure no quizzes are created
        self.assertFalse(QuizModel.objects.exists())  


    def test_valid_request(self):
        """
        Test that a valid request creates a QuizModel instance and returns a 200 OK.
        """
        # Ensure no quizzes exist before the test
        self.assertFalse(QuizModel.objects.exists())

        valid_payload = {
            "document": self.valid_pdf_name,
            "start": self.valid_page_num_start,
            "end": self.valid_page_num_end,
            "subject": "Some subject",
        }
        response = self.client.post(self.url, valid_payload, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ensure a quiz is created
        self.assertTrue(QuizModel.objects.exists())  

        # Retrieve the created quiz
        quiz = QuizModel.objects.first()
        self.assertEqual(quiz.document_name, self.valid_pdf_name)
        self.assertEqual(quiz.start, self.valid_page_num_start)
        self.assertEqual(quiz.end, self.valid_page_num_end)
        
        # Verify the response data
        self.assertIn('document_name', response.data)
        self.assertEqual(response.data['start'], self.valid_page_num_start)
        self.assertEqual(response.data['end'], self.valid_page_num_end)
        self.assertIn('questions', response.data)
        self.assertIsInstance(response.data['questions'], list)
        # Ensure questions are present
        self.assertGreater(len(response.data['questions']), 0)
        
        # Check that questions are created and associated with the quiz
        self.assertTrue(
            QuestionAnswerModel.objects.filter(quiz=quiz).exists() or 
            MultipleChoiceQuestionModel.objects.filter(quiz=quiz).exists()
        )

    def test_valid_request_with_learning_goals(self):
        """
        Test that a valid request with learning goals creates a QuizModel instance,
        associates it with learning goals, and returns a 200 OK.
        """
        # Ensure no quizzes exist before the test
        self.assertFalse(QuizModel.objects.exists())  

        valid_payload = {
            "document": self.valid_pdf_name,
            "start": self.valid_page_num_start,
            "end": self.valid_page_num_end,
            "subject": "Some subject",
            "learning_goals": ["goal1", "goal2"],
        }
        response = self.client.post(self.url, valid_payload, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ensure a quiz is created
        self.assertTrue(QuizModel.objects.exists())  

        # Retrieve the created quiz
        quiz = QuizModel.objects.first()
        self.assertEqual(quiz.document_name, self.valid_pdf_name)
        self.assertEqual(quiz.start, self.valid_page_num_start)
        self.assertEqual(quiz.end, self.valid_page_num_end)
        
        # Verify the response data
        self.assertEqual(response.data['document_name'], self.valid_pdf_name)
        self.assertEqual(response.data['start'], self.valid_page_num_start)
        self.assertEqual(response.data['end'], self.valid_page_num_end)
        
        self.assertIn('questions', response.data)
        self.assertIsInstance(response.data['questions'], list)
        self.assertGreater(len(response.data['questions']), 0)

        # Check that questions are created and associated with the quiz
        self.assertTrue(
            QuestionAnswerModel.objects.filter(quiz=quiz).exists() or 
            MultipleChoiceQuestionModel.objects.filter(quiz=quiz).exists()
        )
        


    def test_invalid_end_start_index(self):
        """
        Test that a request with invalid start and end indices returns a 400 Bad Request
        and does not create any QuizModel instances.
        """
        # Ensure no quizzes exist before the test
        self.assertFalse(QuizModel.objects.exists())  

        invalid_payload = {
            "document": self.valid_pdf_name,
            "start": self.valid_page_num_end,  # start is greater than end
            "end": self.valid_page_num_start,
            "subject": "Some subject",
        }
        response = self.client.post(self.url, invalid_payload, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Ensure no quizzes are created
        self.assertFalse(QuizModel.objects.exists())  

 


class QuizGradingTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = f"{base}quiz/grade/"
        self.valid_quiz_id = "Some ID"

    def test_invalid_request(self):
        invalid_payload = {}
        response = self.client.post(self.url, invalid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_request(self):
        valid_response = {
            "quiz_id": self.valid_quiz_id,
            "student_answers": ["answer1"],
        }
        response = self.client.post(self.url, valid_response, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)



class CompendiumAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = f"{base}compendium/create/"
        self.valid_document = "test.pdf"
        self.start_page = 1
        self.end_page = 10

    def test_valid_request(self):
        """Test the create_compendium endpoint with a valid request."""
        valid_payload = {
            "document": self.valid_document,
            "start": self.start_page,
            "end": self.end_page,
            "subject": "Some subject",
        }
        response = self.client.post(
            self.url, data=valid_payload, content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), dict)  # Ensuring the response is JSON

    def test_invalid_page_range(self):
        """Test the create_compendium endpoint with an invalid page range (start > end)."""
        invalid_payload = {
            "document": self.valid_document,
            "start": 10,
            "end": 1,
            "subject": "Some subject",
        }
        response = self.client.post(
            self.url, data=invalid_payload, content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_parameters(self):
        """Test the create_compendium endpoint with missing required parameters."""
        invalid_payloads = [
            {
                "document": self.valid_document,
                "start": self.start_page,
            },  # missing 'end'
            {"document": self.valid_document, "end": self.end_page},  # missing 'start'
            {"start": self.start_page, "end": self.end_page},  # missing 'document'
        ]
        for payload in invalid_payloads:
            response = self.client.post(
                self.url, data=payload, content_type="application/json"
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)