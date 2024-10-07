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
        self.valid_document_name = "test.pdf"
        self.valid_page_num_start = 0
        self.valid_page_num_end = 1
        self.context = """Revenge of the Sith is set three years after the onset of the Clone Wars as established in Attack of the Clones. The Jedi are spread across the galaxy in a full-scale war against the Separatists. The Jedi Council dispatches Jedi Master Obi-Wan Kenobi on a mission to defeat General Grievous, the head of the Separatist army and Count Dooku's former apprentice, to put an end to the war. Meanwhile, after having visions of his wife Padmé Amidala dying in childbirth, Jedi Knight Anakin Skywalker is tasked by the Council to spy on Palpatine, the Supreme Chancellor of the Galactic Republic and, secretly, a Sith Lord. Palpatine manipulates Anakin into turning to the dark side of the Force and becoming his apprentice, Darth Vader, with wide-ranging consequences for the galaxy."""

        self.user = User.objects.create_user(username='flashcardsuser', email='flashcards@example.com', password='StrongP@ss1')
        self.client.force_authenticate(user=self.user)
        
        # Populate rag database
        for i in range(self.valid_page_num_start, self.valid_page_num_end + 1):
            post_context(self.context, i, self.valid_document_name)

    def test_generate_flashcards(self):
        page = Page(text=self.context, page_num=self.valid_page_num_start, document_name=self.valid_document_name)
        flashcards = generate_flashcards(page)
        self.assertIsInstance(flashcards, list)
        self.assertGreater(len(flashcards), 0)
        self.assertIsInstance(flashcards[0], Flashcard)
        self.assertGreater(len(flashcards[0].front), 0)
        self.assertGreater(len(flashcards[0].back), 0)
        self.assertEqual(flashcards[0].document_name, self.valid_document_name)
        self.assertEqual(flashcards[0].page_num, self.valid_page_num_start)

    def test_parse_for_anki(self):
        page = Page(text=self.context, page_num=self.valid_page_num_start, document_name=self.valid_document_name)
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
            "document": self.valid_document_name,
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
            "document": self.valid_document_name,
            "start": 1,
            "end": 0,
            "subject": "Some subject",
        }
        response = self.client.post(self.url, invalid_response, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Cardset.objects.exists())




class CardsetCRUDTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create and authenticate a user
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        self.client.force_authenticate(user=self.user)
        # Create another user
        self.other_user = User.objects.create_user(username='otheruser', email='other@example.com', password='otherpassword')

    def test_create_cardset(self):
        url = '/api/cardsets/'
        data = {
            'name': 'Test Cardset',
            'description': 'This is a test cardset.',
            'subject': 'Test Subject'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cardset = Cardset.objects.get(id=response.data['id'])
        self.assertEqual(cardset.name, data['name'])
        self.assertEqual(cardset.description, data['description'])
        self.assertEqual(cardset.subject, data['subject'])
        self.assertEqual(cardset.user, self.user)


    def test_retrieve_cardset(self):
        cardset = Cardset.objects.create(name='Test Cardset', description='This is a test cardset.', subject='Test Subject', user=self.user)
        url = f'/api/cardsets/{cardset.id}/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], cardset.name)


    def test_update_cardset(self):
        cardset = Cardset.objects.create(name='Test Cardset', description='This is a test cardset.', subject='Test Subject', user=self.user)
        url = f'/api/cardsets/{cardset.id}/'
        data = {
            'name': 'Updated Cardset',
            'description': 'This is an updated cardset.',
            'subject': 'Updated Subject'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cardset.refresh_from_db()
        self.assertEqual(cardset.name, data['name'])
        self.assertEqual(cardset.description, data['description'])
        self.assertEqual(cardset.subject, data['subject'])


    def test_partial_update_cardset(self):
        cardset = Cardset.objects.create(name='Test Cardset', description='This is a test cardset.', subject='Test Subject', user=self.user)
        url = f'/api/cardsets/{cardset.id}/'
        data = {
            'name': 'Partially Updated Cardset'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cardset.refresh_from_db()
        self.assertEqual(cardset.name, data['name'])
        self.assertEqual(cardset.description, 'This is a test cardset.')  # Unchanged


    def test_delete_cardset(self):
        cardset = Cardset.objects.create(name='Test Cardset', description='This is a test cardset.', subject='Test Subject', user=self.user)
        url = f'/api/cardsets/{cardset.id}/'
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Cardset.objects.filter(id=cardset.id).exists())


    def test_list_cardsets(self):
        Cardset.objects.create(name='Cardset 1', description='First cardset', subject='Subject 1', user=self.user)
        Cardset.objects.create(name='Cardset 2', description='Second cardset', subject='Subject 2', user=self.user)
        Cardset.objects.create(name='Other User Cardset', description='Other user cardset', subject='Other Subject', user=self.other_user)
        url = '/api/cardsets/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Should only return cardsets belonging to self.user
        names = [cardset['name'] for cardset in response.data]
        self.assertIn('Cardset 1', names)
        self.assertIn('Cardset 2', names)
        self.assertNotIn('Other User Cardset', names)


    def test_cannot_access_other_users_cardset(self):
        cardset = Cardset.objects.create(name='Other User Cardset', description='Other user cardset', subject='Other Subject', user=self.other_user)
        url = f'/api/cardsets/{cardset.id}/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.put(url, {'name': 'Hacked'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class FlashcardCRUDTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create and authenticate a user
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpassword')
        self.client.force_authenticate(user=self.user)
        # Create another user
        self.other_user = User.objects.create_user(username='otheruser', email='other@example.com', password='otherpassword')
        # Create a cardset for the user
        self.cardset = Cardset.objects.create(name='Test Cardset', description='Test', subject='Test Subject', user=self.user)
        # Create a cardset for the other user
        self.other_cardset = Cardset.objects.create(name='Other User Cardset', description='Other', subject='Other Subject', user=self.other_user)

    def test_create_flashcard(self):
        url = '/api/flashcards/'
        data = {
            'front': 'What is the capital of France?',
            'back': 'Paris',
            'cardset': self.cardset.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        flashcard = FlashcardModel.objects.get(id=response.data['id'])
        self.assertEqual(flashcard.front, data['front'])
        self.assertEqual(flashcard.back, data['back'])
        self.assertEqual(flashcard.cardset, self.cardset)

    def test_retrieve_flashcard(self):
        flashcard = FlashcardModel.objects.create(front='Front', back='Back', cardset=self.cardset)
        url = f'/api/flashcards/{flashcard.id}/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['front'], flashcard.front)

    def test_update_flashcard(self):
        flashcard = FlashcardModel.objects.create(front='Front', back='Back', cardset=self.cardset)
        url = f'/api/flashcards/{flashcard.id}/'
        data = {
            'front': 'Updated Front',
            'back': 'Updated Back',
            'cardset': self.cardset.id
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        flashcard.refresh_from_db()
        self.assertEqual(flashcard.front, data['front'])
        self.assertEqual(flashcard.back, data['back'])

    def test_partial_update_flashcard(self):
        flashcard = FlashcardModel.objects.create(front='Front', back='Back', cardset=self.cardset)
        url = f'/api/flashcards/{flashcard.id}/'
        data = {
            'front': 'Partially Updated Front'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        flashcard.refresh_from_db()
        self.assertEqual(flashcard.front, data['front'])
        self.assertEqual(flashcard.back, 'Back')  # Unchanged

    def test_delete_flashcard(self):
        flashcard = FlashcardModel.objects.create(front='Front', back='Back', cardset=self.cardset)
        url = f'/api/flashcards/{flashcard.id}/'
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FlashcardModel.objects.filter(id=flashcard.id).exists())

    def test_list_flashcards(self):
        FlashcardModel.objects.create(front='Front 1', back='Back 1', cardset=self.cardset)
        FlashcardModel.objects.create(front='Front 2', back='Back 2', cardset=self.cardset)
        # Flashcard for other user
        FlashcardModel.objects.create(front='Other Front', back='Other Back', cardset=self.other_cardset)
        url = '/api/flashcards/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Should only return flashcards belonging to self.user's cardsets
        fronts = [flashcard['front'] for flashcard in response.data]
        self.assertIn('Front 1', fronts)
        self.assertIn('Front 2', fronts)
        self.assertNotIn('Other Front', fronts)

    def test_cannot_create_flashcard_in_other_users_cardset(self):
        url = '/api/flashcards/'
        data = {
            'front': 'What is the capital of Germany?',
            'back': 'Berlin',
            'cardset': self.other_cardset.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('cardset', response.data)
        self.assertEqual(FlashcardModel.objects.count(), 0)

    def test_cannot_access_other_users_flashcard(self):
        other_flashcard = FlashcardModel.objects.create(front='Other Front', back='Other Back', cardset=self.other_cardset)
        url = f'/api/flashcards/{other_flashcard.id}/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.put(url, {'front': 'Hacked', 'back': 'Hacked', 'cardset': self.cardset.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class RagAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = f"{base}search/"
        self.valid_document_name = "test.pdf"
        self.invalid_document_name = "invalid.pdf"
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

    def invalid_document_name(self):
        pass

    def test_valid_request_without_chat_history(self):
        valid_response = {
            "documents": [self.valid_document_name],
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
        self.valid_document_name = "test.pdf"
        self.invalid_document_name = "invalid.pdf"
        self.valid_page_num_start = 0
        self.valid_page_num_end = 1
        self.context = """
            Artificial intelligence (AI), in its broadest sense, is intelligence exhibited by machines, particularly computer systems.
            It is a field of research in computer science that develops and studies methods and software that enable machines to perceive their environment and use learning and intelligence to take actions that maximize their chances of achieving defined goals.
            [1] Such machines may be called AIs.
        """

        # Populate RAG (Retrieval-Augmented Generation) database
        for i in range(self.valid_page_num_start, self.valid_page_num_end + 1):
            post_context(self.context, i, self.valid_document_name)


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
            "document": self.valid_document_name,
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
        self.assertEqual(quiz.document_name, self.valid_document_name)
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
            "document": self.valid_document_name,
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
        self.assertEqual(quiz.document_name, self.valid_document_name)
        self.assertEqual(quiz.start, self.valid_page_num_start)
        self.assertEqual(quiz.end, self.valid_page_num_end)
        
        # Verify the response data
        self.assertEqual(response.data['document_name'], self.valid_document_name)
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
            "document": self.valid_document_name,
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