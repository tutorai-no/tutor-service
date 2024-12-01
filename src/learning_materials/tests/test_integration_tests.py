import time
import uuid
import re
from uuid import uuid4

from unittest.mock import patch
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken


from learning_materials.flashcards.flashcards_service import (
    generate_flashcards,
    parse_for_anki,
)
from learning_materials.models import (
    Chat,
    FlashcardModel,
    Cardset,
    Course,
    UserFile,
    MultipleChoiceQuestionModel,
    QuestionAnswerModel,
    QuizModel,
)
from learning_materials.learning_resources import Flashcard
from learning_materials.learning_resources import Citation
from learning_materials.knowledge_base.rag_service import post_context
from accounts.models import CustomUser

base = "/api/"

User = get_user_model()


class FlashcardGenerationTest(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()

        self.url = f"{base}flashcards/create/"
        self.valid_document_name = "test.pdf"
        self.valid_document_id = str(uuid4())
        self.valid_page_num_start = 0
        self.valid_page_num_end = 1
        self.subject = "Anakin Skywalker"
        self.context = """
            Revenge of the Sith is set three years after the onset of the Clone Wars as established in Attack of the Clones. 
            The Jedi are spread across the galaxy in a full-scale war against the Separatists. 
            The Jedi Council dispatches Jedi Master Obi-Wan Kenobi on a mission to dfefeat General Grievous, the head of the Separatist army and Count Dooku's former apprentice, to put an end to the war. 
            Meanwhile, after having visions of his wife Padmé Amidala dying in childbirth, Jedi Knight Anakin Skywalker is tasked by the Council to spy on Palpatine, the Supreme Chancellor of the Galactic Republic and, secretly, a Sith Lord.
            Palpatine manipulates Anakin into turning to the dark side of the Force and becoming his apprentice, Darth Vader, with wide-ranging consequences for the galaxy."""

        self.user = User.objects.create_user(
            username="flashcardsuser",
            email="flashcards@example.com",
            password="StrongP@ss1",
        )
        self.client.force_authenticate(user=self.user)
        # Populate rag database
        for i in range(self.valid_page_num_start, self.valid_page_num_end + 1):
            post_context(
                self.context, i, self.valid_document_name, self.valid_document_id
            )
        self.course = Course.objects.create(name="Test Course", user=self.user)

    def test_generate_flashcards(self):
        page = Citation(
            text=self.context,
            page_num=self.valid_page_num_start,
            document_name=self.valid_document_name,
        )
        flashcards = generate_flashcards(page)
        self.assertIsInstance(flashcards, list)
        self.assertGreater(len(flashcards), 0)
        self.assertIsInstance(flashcards[0], Flashcard)
        self.assertGreater(len(flashcards[0].front), 0)
        self.assertGreater(len(flashcards[0].back), 0)
        self.assertEqual(flashcards[0].document_name, self.valid_document_name)
        self.assertEqual(flashcards[0].page_num, self.valid_page_num_start)

    def test_parse_for_anki(self):
        page = Citation(
            text=self.context,
            page_num=self.valid_page_num_start,
            document_name=self.valid_document_name,
        )
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
            "id": self.valid_document_id,
            "start_page": self.valid_page_num_start,
            "end_page": self.valid_page_num_end,
            "subject": "Some subject",
        }
        response = self.client.post(self.url, valid_response, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)

        self.assertTrue(Cardset.objects.exists())
        cardset = Cardset.objects.first()
        flashcards = FlashcardModel.objects.filter(cardset=cardset)
        self.assertGreater(flashcards.count(), 0)

        # Validate Response Cardset Data
        self.assertIn("id", response.data)
        self.assertIn("flashcards", response.data)

        # Validate flashcards data
        flashcards_data = response.data["flashcards"]
        self.assertIsInstance(flashcards_data, list)
        self.assertGreater(len(flashcards_data), 0)
        self.assertIsInstance(flashcards_data[0], dict)
        self.assertIn("front", flashcards_data[0])
        self.assertIn("back", flashcards_data[0])
        self.assertIn("id", flashcards_data[0])

    def test_invalid_end_start_index(self):
        self.assertFalse(Cardset.objects.exists())
        invalid_response = {
            "id": self.valid_document_id,
            "start_page": 1,
            "end_page": 0,
            "subject": "Some subject",
        }
        response = self.client.post(self.url, invalid_response, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Cardset.objects.exists())

    def test_valid_request_with_course_id(self):
        self.assertFalse(Cardset.objects.exists())
        valid_response = {
            "id": self.valid_document_id,
            "start_page": self.valid_page_num_start,
            "end_page": self.valid_page_num_end,
            "subject": "Some subject",
            "course_id": self.course.id,
        }
        response = self.client.post(self.url, valid_response, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)

        self.assertTrue(Cardset.objects.exists())
        cardset = Cardset.objects.first()
        flashcards = FlashcardModel.objects.filter(cardset=cardset)
        self.assertGreater(flashcards.count(), 0)
        self.assertEqual(cardset.course, self.course)

        # Validate Response Cardset Data
        self.assertIn("id", response.data)
        self.assertIn("flashcards", response.data)

        # Validate flashcards data
        flashcards_data = response.data["flashcards"]
        self.assertIsInstance(flashcards_data, list)
        self.assertGreater(len(flashcards_data), 0)
        self.assertIsInstance(flashcards_data[0], dict)
        self.assertIn("front", flashcards_data[0])
        self.assertIn("back", flashcards_data[0])
        self.assertIn("id", flashcards_data[0])

    def test_invalid_end_start_index(self):
        self.assertFalse(Cardset.objects.exists())
        invalid_response = {
            "id": self.valid_document_id,
            "start_page": 1,
            "end_page": 0,
            "subject": "Some subject",
        }
        response = self.client.post(self.url, invalid_response, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Cardset.objects.exists())

    def test_no_page_range_request(self):
        self.assertFalse(Cardset.objects.exists())
        valid_request = {
            "id": self.valid_document_id,
            "subject": self.subject,
            "course_id": self.course.id,
        }
        response = self.client.post(self.url, valid_request, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(Cardset.objects.exists())


class FlashcardReviewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = f"{base}flashcards/review/"

        self.user = User.objects.create_user(
            username="flashcardsuser",
            email="flashcards@example.com",
            password="StrongP@ss1",
        )
        self.client.force_authenticate(user=self.user)

        self.other_user = User.objects.create_user(
            username="other_user", email="otheruser@example.com", password="StrongP@ss1"
        )

        self.cardset = Cardset.objects.create(name="Test Cardset", user=self.user)
        self.flashcard = FlashcardModel.objects.create(
            front="Front", back="Back", cardset=self.cardset
        )

    def test_review_flashcard_correct_answer(self):
        self.assertEqual(self.flashcard.proficiency, 0)
        response = self.client.post(
            self.url,
            data={"id": self.flashcard.id, "answer_was_correct": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.flashcard.refresh_from_db()
        self.assertEqual(self.flashcard.proficiency, 1)

    def test_review_flashcard_incorrect_answer(self):
        self.assertEqual(self.flashcard.proficiency, 0)
        response = self.client.post(
            self.url,
            data={"id": self.flashcard.id, "answer_was_correct": False},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.flashcard.refresh_from_db()
        self.assertEqual(self.flashcard.proficiency, 0)

    def test_review_other_user_flashcard(self):
        self.assertEqual(self.flashcard.proficiency, 0)
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(
            self.url,
            data={"id": self.flashcard.id, "answer_was_correct": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.flashcard.refresh_from_db()
        self.assertEqual(self.flashcard.proficiency, 0)

    def test_review_non_existent_flashcard(self):
        self.assertEqual(self.flashcard.proficiency, 0)
        response = self.client.post(
            self.url, data={"id": 999, "answer_was_correct": True}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_review_max_proficiency_flashcard(self):
        self.flashcard.proficiency = 9
        self.flashcard.save()
        response = self.client.post(
            self.url,
            data={"id": self.flashcard.id, "answer_was_correct": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.flashcard.refresh_from_db()
        self.assertEqual(self.flashcard.proficiency, 9)

    def test_streak_reset_on_incorrect_answer(self):
        self.flashcard.proficiency = 9
        self.flashcard.save()
        response = self.client.post(
            self.url,
            data={"id": self.flashcard.id, "answer_was_correct": False},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.flashcard.refresh_from_db()
        self.assertEqual(self.flashcard.proficiency, 0)


class CardsetCRUDTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create and authenticate a user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        self.client.force_authenticate(user=self.user)
        # Create another user
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="otherpassword"
        )

    def test_create_cardset(self):
        url = "/api/cardsets/"
        data = {
            "name": "Test Cardset",
            "description": "This is a test cardset.",
            "subject": "Test Subject",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        cardset = Cardset.objects.get(id=response.data["id"])
        self.assertEqual(cardset.name, data["name"])
        self.assertEqual(cardset.description, data["description"])
        self.assertEqual(cardset.subject, data["subject"])
        self.assertEqual(cardset.user, self.user)

    def test_retrieve_cardset(self):
        cardset = Cardset.objects.create(
            name="Test Cardset",
            description="This is a test cardset.",
            subject="Test Subject",
            user=self.user,
        )
        url = f"/api/cardsets/{cardset.id}/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], cardset.name)

    def test_update_cardset(self):
        cardset = Cardset.objects.create(
            name="Test Cardset",
            description="This is a test cardset.",
            subject="Test Subject",
            user=self.user,
        )
        url = f"/api/cardsets/{cardset.id}/"
        data = {
            "name": "Updated Cardset",
            "description": "This is an updated cardset.",
            "subject": "Updated Subject",
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cardset.refresh_from_db()
        self.assertEqual(cardset.name, data["name"])
        self.assertEqual(cardset.description, data["description"])
        self.assertEqual(cardset.subject, data["subject"])

    def test_partial_update_cardset(self):
        cardset = Cardset.objects.create(
            name="Test Cardset",
            description="This is a test cardset.",
            subject="Test Subject",
            user=self.user,
        )
        url = f"/api/cardsets/{cardset.id}/"
        data = {"name": "Partially Updated Cardset"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cardset.refresh_from_db()
        self.assertEqual(cardset.name, data["name"])
        self.assertEqual(cardset.description, "This is a test cardset.")  # Unchanged

    def test_delete_cardset(self):
        cardset = Cardset.objects.create(
            name="Test Cardset",
            description="This is a test cardset.",
            subject="Test Subject",
            user=self.user,
        )
        url = f"/api/cardsets/{cardset.id}/"
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Cardset.objects.filter(id=cardset.id).exists())

    def test_list_cardsets(self):
        Cardset.objects.create(
            name="Cardset 1",
            description="First cardset",
            subject="Subject 1",
            user=self.user,
        )
        Cardset.objects.create(
            name="Cardset 2",
            description="Second cardset",
            subject="Subject 2",
            user=self.user,
        )
        Cardset.objects.create(
            name="Other User Cardset",
            description="Other user cardset",
            subject="Other Subject",
            user=self.other_user,
        )
        url = "/api/cardsets/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data), 2
        )  # Should only return cardsets belonging to self.user
        names = [cardset["name"] for cardset in response.data]
        self.assertIn("Cardset 1", names)
        self.assertIn("Cardset 2", names)
        self.assertNotIn("Other User Cardset", names)

    def test_cannot_access_other_users_cardset(self):
        cardset = Cardset.objects.create(
            name="Other User Cardset",
            description="Other user cardset",
            subject="Other Subject",
            user=self.other_user,
        )
        url = f"/api/cardsets/{cardset.id}/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.put(url, {"name": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_cardset_deletes_flashcards(self):
        # Create a cardset and some flashcards
        cardset = Cardset.objects.create(
            name="Test Cardset",
            description="This is a test cardset.",
            subject="Test Subject",
            user=self.user,
        )

        # Create some flashcards
        FlashcardModel.objects.create(front="Front 1", back="Back 1", cardset=cardset)
        FlashcardModel.objects.create(front="Front 2", back="Back 2", cardset=cardset)
        # Ensure flashcards exist
        self.assertEqual(FlashcardModel.objects.filter(cardset=cardset).count(), 2)
        # Delete the cardset
        url = f"/api/cardsets/{cardset.id}/"
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Ensure flashcards are deleted
        self.assertFalse(FlashcardModel.objects.filter(cardset=cardset).exists())

    def test_filter_cardsets_by_course_id(self):
        course1 = Course.objects.create(name="Course 1", user=self.user)
        course2 = Course.objects.create(name="Course 2", user=self.user)

        cardset1 = Cardset.objects.create(
            name="Cardset for Course 1",
            description="First cardset",
            subject="Subject 1",
            user=self.user,
            course=course1,
        )

        url = f"/api/cardsets/?course_id={course1.id}"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Cardset for Course 1")


class FlashcardCRUDTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create and authenticate a user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        self.client.force_authenticate(user=self.user)
        # Create another user
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="otherpassword"
        )
        # Create a cardset for the user
        self.cardset = Cardset.objects.create(
            name="Test Cardset",
            description="Test",
            subject="Test Subject",
            user=self.user,
        )
        # Create a cardset for the other user
        self.other_cardset = Cardset.objects.create(
            name="Other User Cardset",
            description="Other",
            subject="Other Subject",
            user=self.other_user,
        )

    def test_create_flashcard(self):
        url = "/api/flashcards/"
        data = {
            "front": "What is the capital of France?",
            "back": "Paris",
            "cardset": self.cardset.id,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        flashcard = FlashcardModel.objects.get(id=response.data["id"])
        self.assertEqual(flashcard.front, data["front"])
        self.assertEqual(flashcard.back, data["back"])
        self.assertEqual(flashcard.cardset, self.cardset)

    def test_retrieve_flashcard(self):
        flashcard = FlashcardModel.objects.create(
            front="Front", back="Back", cardset=self.cardset
        )
        url = f"/api/flashcards/{flashcard.id}/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["front"], flashcard.front)

    def test_update_flashcard(self):
        flashcard = FlashcardModel.objects.create(
            front="Front", back="Back", cardset=self.cardset
        )
        url = f"/api/flashcards/{flashcard.id}/"
        data = {
            "front": "Updated Front",
            "back": "Updated Back",
            "cardset": self.cardset.id,
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        flashcard.refresh_from_db()
        self.assertEqual(flashcard.front, data["front"])
        self.assertEqual(flashcard.back, data["back"])

    def test_partial_update_flashcard(self):
        flashcard = FlashcardModel.objects.create(
            front="Front", back="Back", cardset=self.cardset
        )
        url = f"/api/flashcards/{flashcard.id}/"
        data = {"front": "Partially Updated Front"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        flashcard.refresh_from_db()
        self.assertEqual(flashcard.front, data["front"])
        self.assertEqual(flashcard.back, "Back")  # Unchanged

    def test_delete_flashcard(self):
        flashcard = FlashcardModel.objects.create(
            front="Front", back="Back", cardset=self.cardset
        )
        url = f"/api/flashcards/{flashcard.id}/"
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FlashcardModel.objects.filter(id=flashcard.id).exists())

    def test_list_flashcards(self):
        FlashcardModel.objects.create(
            front="Front 1", back="Back 1", cardset=self.cardset
        )
        FlashcardModel.objects.create(
            front="Front 2", back="Back 2", cardset=self.cardset
        )
        # Flashcard for other user
        FlashcardModel.objects.create(
            front="Other Front", back="Other Back", cardset=self.other_cardset
        )
        url = "/api/flashcards/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data), 2
        )  # Should only return flashcards belonging to self.user's cardsets
        fronts = [flashcard["front"] for flashcard in response.data]
        self.assertIn("Front 1", fronts)
        self.assertIn("Front 2", fronts)
        self.assertNotIn("Other Front", fronts)

    def test_cannot_create_flashcard_in_other_users_cardset(self):
        url = "/api/flashcards/"
        data = {
            "front": "What is the capital of Germany?",
            "back": "Berlin",
            "cardset": self.other_cardset.id,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cardset", response.data)
        self.assertEqual(FlashcardModel.objects.count(), 0)

    def test_cannot_access_other_users_flashcard(self):
        other_flashcard = FlashcardModel.objects.create(
            front="Other Front", back="Other Back", cardset=self.other_cardset
        )
        url = f"/api/flashcards/{other_flashcard.id}/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.put(
            url,
            {"front": "Hacked", "back": "Hacked", "cardset": self.cardset.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_deleting_flashcard_removes_it_from_cardset(self):
        flashcard = FlashcardModel.objects.create(
            front="Front", back="Back", cardset=self.cardset
        )
        self.assertEqual(self.cardset.flashcards.count(), 1)
        url = f"/api/flashcards/{flashcard.id}/"
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.cardset.flashcards.count(), 0)


class CardsetExportTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create and authenticate a user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        self.client.force_authenticate(user=self.user)
        # Create another user
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="otherpassword"
        )
        # Create a cardset for the user
        self.cardset = Cardset.objects.create(
            name="Test Cardset",
            description="Test",
            subject="Test Subject",
            user=self.user,
        )
        # Create some flashcards for the user's cardset
        self.flashcard1 = FlashcardModel.objects.create(
            front="What is the capital of France?", back="Paris", cardset=self.cardset
        )
        self.flashcard2 = FlashcardModel.objects.create(
            front="What is the largest planet?", back="Jupiter", cardset=self.cardset
        )
        # Create a cardset for the other user
        self.other_cardset = Cardset.objects.create(
            name="Other User Cardset",
            description="Other",
            subject="Other Subject",
            user=self.other_user,
        )

        self.non_existent_cardset_id = 9999

    def test_export_flashcards_success(self):
        url = f"/api/flashcards/export/{self.cardset.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("exportable_flashcards", response.data)
        exportable_flashcards = response.data["exportable_flashcards"]
        # Verify that the exportable flashcards content is correct
        expected_content = (
            f"{self.flashcard1.front}:{self.flashcard1.back}\n"
            f"{self.flashcard2.front}:{self.flashcard2.back}\n"
        )
        self.assertEqual(exportable_flashcards, expected_content)

    def test_export_flashcards_not_authenticated(self):
        self.client.force_authenticate(user=None)  # Log out
        url = f"/api/flashcards/export/{self.cardset.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_export_flashcards_cardset_not_found(self):
        url = f"/api/flashcards/export/{self.non_existent_cardset_id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_export_flashcards_cardset_not_owned(self):
        url = f"/api/flashcards/export/{self.other_cardset.id}/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class QuizGenerationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = f"{base}quiz/create/"

        # Create and authenticate a user
        self.user = CustomUser.objects.create_user(
            username="testuser", password="testpass"
        )
        self.client.force_authenticate(user=self.user)

        # Define valid and invalid test data
        self.valid_document_name = "test.pdf"
        self.valid_document_id = str(uuid4())
        self.invalid_document_name = "invalid.pdf"
        self.valid_page_num_start = 0
        self.valid_page_num_end = 1
        self.context = """
            Artificial intelligence (AI), in its broadest sense, is intelligence exhibited by machines, particularly computer systems.
            It is a field of research in computer science that develops and studies methods and software that enable machines to perceive their environment and use learning and intelligence to take actions that maximize their chances of achieving defined goals.
            [1] Such machines may be called AIs.
        """
        self.valid_subject = "Artificial Intelligence"

        # Populate RAG (Retrieval-Augmented Generation) database
        for i in range(self.valid_page_num_start, self.valid_page_num_end + 1):
            post_context(
                self.context, i, self.valid_document_name, self.valid_document_id
            )

        self.course = Course.objects.create(name="Test Course", user=self.user)

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
            "id": self.valid_document_id,
            "start_page": self.valid_page_num_start,
            "end_page": self.valid_page_num_end,
            "subject": "Some subject",
        }
        response = self.client.post(self.url, valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ensure a quiz is created
        self.assertTrue(QuizModel.objects.exists())

        # Retrieve the created quiz
        quiz = QuizModel.objects.first()
        self.assertEqual(quiz.document_name, self.valid_document_name)
        self.assertEqual(quiz.start_page, self.valid_page_num_start)
        self.assertEqual(quiz.end_page, self.valid_page_num_end)

        # Verify the response data
        self.assertIn("id", response.data)
        self.assertIn("document_name", response.data)
        self.assertEqual(response.data["start_page"], self.valid_page_num_start)
        self.assertEqual(response.data["end_page"], self.valid_page_num_end)
        self.assertIn("questions", response.data)
        self.assertIsInstance(response.data["questions"], list)
        # Ensure questions are present
        self.assertGreater(len(response.data["questions"]), 0)

        # Check that questions are created and associated with the quiz
        self.assertTrue(
            QuestionAnswerModel.objects.filter(quiz=quiz).exists()
            or MultipleChoiceQuestionModel.objects.filter(quiz=quiz).exists()
        )

    def test_valid_request_with_learning_goals(self):
        """
        Test that a valid request with learning goals creates a QuizModel instance,
        associates it with learning goals, and returns a 200 OK.
        """
        # Ensure no quizzes exist before the test
        self.assertFalse(QuizModel.objects.exists())

        valid_payload = {
            "id": self.valid_document_id,
            "start_page": self.valid_page_num_start,
            "end_page": self.valid_page_num_end,
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
        self.assertEqual(quiz.start_page, self.valid_page_num_start)
        self.assertEqual(quiz.end_page, self.valid_page_num_end)

        # Verify the response data
        self.assertIn("id", response.data)
        self.assertEqual(response.data["document_name"], self.valid_document_name)
        self.assertEqual(response.data["start_page"], self.valid_page_num_start)
        self.assertEqual(response.data["end_page"], self.valid_page_num_end)

        self.assertIn("questions", response.data)
        self.assertIsInstance(response.data["questions"], list)
        self.assertGreater(len(response.data["questions"]), 0)

        # Check that questions are created and associated with the quiz
        self.assertTrue(
            QuestionAnswerModel.objects.filter(quiz=quiz).exists()
            or MultipleChoiceQuestionModel.objects.filter(quiz=quiz).exists()
        )

    def test_valid_request_with_course_id(self):
        """
        Test that a valid request creates a QuizModel instance and returns a 200 OK.
        """
        # Ensure no quizzes exist before the test
        self.assertFalse(QuizModel.objects.exists())

        valid_payload = {
            "id": self.valid_document_id,
            "start_page": self.valid_page_num_start,
            "end_page": self.valid_page_num_end,
            "subject": "Some subject",
            "course_id": self.course.id,
        }
        response = self.client.post(self.url, valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ensure a quiz is created
        self.assertTrue(QuizModel.objects.exists())

        # Retrieve the created quiz
        quiz = QuizModel.objects.first()
        self.assertEqual(quiz.document_name, self.valid_document_name)
        self.assertEqual(quiz.start_page, self.valid_page_num_start)
        self.assertEqual(quiz.end_page, self.valid_page_num_end)
        self.assertEqual(quiz.course, self.course)

        # Verify the response data
        self.assertIn("id", response.data)
        self.assertIn("document_name", response.data)
        self.assertEqual(response.data["start_page"], self.valid_page_num_start)
        self.assertEqual(response.data["end_page"], self.valid_page_num_end)
        self.assertIn("questions", response.data)
        self.assertIsInstance(response.data["questions"], list)
        # Ensure questions are present
        self.assertGreater(len(response.data["questions"]), 0)

        # Check that questions are created and associated with the quiz
        self.assertTrue(
            QuestionAnswerModel.objects.filter(quiz=quiz).exists()
            or MultipleChoiceQuestionModel.objects.filter(quiz=quiz).exists()
        )

    def test_invalid_end_start_index(self):
        """
        Test that a request with invalid start and end indices returns a 400 Bad Request
        and does not create any QuizModel instances.
        """
        # Ensure no quizzes exist before the test
        self.assertFalse(QuizModel.objects.exists())

        invalid_payload = {
            "id": self.valid_document_id,
            "start_page": self.valid_page_num_end,  # start is greater than end
            "end_page": self.valid_page_num_start,
            "subject": "Some subject",
        }
        response = self.client.post(self.url, invalid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Ensure no quizzes are created
        self.assertFalse(QuizModel.objects.exists())

    def test_valid_request_for_semantic_creation_of_quizzed(self):
        self.assertFalse(QuizModel.objects.exists())

        valid_payload = {
            "id": self.valid_document_id,
            "subject": self.valid_subject,
        }

        response = self.client.post(self.url, valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(QuizModel.objects.exists())

        # Verify the response data
        self.assertIn("id", response.data)
        self.assertEqual(response.data["document_name"], self.valid_document_name)

        self.assertIn("questions", response.data)
        self.assertIsInstance(response.data["questions"], list)
        self.assertGreater(len(response.data["questions"]), 0)

        quiz = QuizModel.objects.first()
        self.assertEqual(quiz.subject, self.valid_subject)
        # Check that questions are created and associated with the quiz
        self.assertTrue(
            QuestionAnswerModel.objects.filter(quiz=quiz).exists()
            or MultipleChoiceQuestionModel.objects.filter(quiz=quiz).exists()
        )


class QuizGradingTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = f"{base}quiz/grade/"

        self.user = User.objects.create_user(
            username="testuser", email="grading@gmail.com", password="testpassword"
        )
        self.valid_document_name = "test.pdf"
        # Add user to quiz
        self.quiz = QuizModel.objects.create(
            document_name=self.valid_document_name,
            start_page=0,
            end_page=1,
            user=self.user,
        )

        # Create questions for the quiz
        self.question1 = QuestionAnswerModel.objects.create(
            quiz=self.quiz,
            question="What is artificial intelligence?",
            answer="Intelligence exhibited by machines, particularly computer systems.",
        )
        self.question2 = QuestionAnswerModel.objects.create(
            quiz=self.quiz,
            question="What is the field of research in computer science that develops and studies methods and software that enable machines to perceive their environment and use learning and intelligence to take actions that maximize their chances of achieving defined goals?",
            answer="Artificial intelligence",
        )

        self.amount_of_questions = 2

    def authenticate(self):
        self.client.force_authenticate(user=self.user)

    def test_unauthenticated_request(self):
        response = self.client.post(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_request(self):
        self.authenticate()
        invalid_payload = {}
        response = self.client.post(self.url, invalid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_request(self):
        self.authenticate()
        answers = ["answer" for _ in range(self.amount_of_questions)]
        valid_response = {
            "quiz_id": self.quiz.id,
            "student_answers": answers,
        }
        response = self.client.post(self.url, valid_response, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data)

    def test_all_correct_answers(self):
        self.authenticate()
        answers = [
            self.question1.answer,
            self.question2.answer,
        ]
        valid_response = {
            "quiz_id": self.quiz.id,
            "student_answers": answers,
        }
        response = self.client.post(self.url, valid_response, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(response.data["answers_was_correct"]))

    def test_all_incorrect_answers(self):
        self.authenticate()
        answers = [
            "Incorrect answer",
            "Incorrect answer",
        ]
        valid_response = {
            "quiz_id": self.quiz.id,
            "student_answers": answers,
        }
        response = self.client.post(self.url, valid_response, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ensure all answers in answers_was_correct are False
        self.assertFalse(any(response.data["answers_was_correct"]))
        # Ensure that all wrong answers have feedback
        self.assertTrue(all(response.data["feedback"]))


class QuizCRUDTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        # Create and authenticate a user
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword"
        )
        self.client.force_authenticate(user=self.user)
        # Create another user
        self.other_user = User.objects.create_user(
            username="otheruser", email="other@example.com", password="otherpassword"
        )

    def test_create_quiz(self):
        url = f"{base}quizzes/"
        data = {
            "document_name": "Test Document",
            "start_page": 1,
            "end_page": 5,
            "user": self.user.id,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        quiz = QuizModel.objects.get(id=response.data["id"])
        self.assertEqual(quiz.document_name, data["document_name"])
        self.assertEqual(quiz.start_page, data["start_page"])
        self.assertEqual(quiz.end_page, data["end_page"])
        self.assertEqual(quiz.user, self.user)

    def test_retrieve_quiz(self):
        quiz = QuizModel.objects.create(
            document_name="Test Document",
            start_page=1,
            end_page=5,
            subject="Test Subject",
            user=self.user,
        )
        url = f"{base}quizzes/{quiz.id}/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["document_name"], quiz.document_name)

    def test_update_quiz(self):
        quiz = QuizModel.objects.create(
            document_name="Test Document",
            start_page=1,
            end_page=5,
            subject="Test Subject",
            user=self.user,
        )
        data = {
            "document_name": "Updated Document",
            "start_page": 2,
            "end_page": 6,
            "user": self.user.id,
        }
        url = f"{base}quizzes/{quiz.id}/"
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        quiz.refresh_from_db()
        self.assertEqual(quiz.document_name, data["document_name"])
        self.assertEqual(quiz.start_page, data["start_page"])
        self.assertEqual(quiz.end_page, data["end_page"])

    def test_partial_update_quiz(self):
        quiz = QuizModel.objects.create(
            document_name="Test Document",
            start_page=1,
            end_page=5,
            subject="Test Subject",
            user=self.user,
        )
        url = f"{base}quizzes/{quiz.id}/"
        data = {"document_name": "Partially Updated Document"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        quiz.refresh_from_db()
        self.assertEqual(quiz.document_name, data["document_name"])
        self.assertEqual(quiz.start_page, 1)  # Unchanged
        self.assertEqual(quiz.end_page, 5)  # Unchanged

    def test_delete_quiz(self):
        quiz = QuizModel.objects.create(
            document_name="Test Document",
            start_page=1,
            end_page=5,
            subject="Test Subject",
            user=self.user,
        )
        url = f"{base}quizzes/{quiz.id}/"
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(QuizModel.objects.filter(id=quiz.id).exists())

    def test_list_quizzes(self):
        QuizModel.objects.create(
            document_name="Quiz 1",
            start_page=1,
            end_page=3,
            subject="Subject 1",
            user=self.user,
        )
        QuizModel.objects.create(
            document_name="Quiz 2",
            start_page=2,
            end_page=5,
            subject="Subject 2",
            user=self.user,
        )
        QuizModel.objects.create(
            document_name="Other User Quiz",
            start_page=1,
            end_page=4,
            subject="Other Subject",
            user=self.other_user,
        )
        url = f"{base}quizzes/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_quizzes_by_course_id(self):
        # Create some courses
        course1 = Course.objects.create(name="Course 1", user=self.user)
        course2 = Course.objects.create(name="Course 2", user=self.user)

        # Create quizzes associated with different courses
        quiz1 = QuizModel.objects.create(
            document_name="Quiz for Course 1",
            start_page=1,
            end_page=3,
            subject="Subject 1",
            user=self.user,
            course=course1,
        )
        quiz2 = QuizModel.objects.create(
            document_name="Quiz for Course 2",
            start_page=2,
            end_page=4,
            subject="Subject 2",
            user=self.user,
            course=course2,
        )

        # Create a quiz without a course to ensure it is filtered out
        quiz3 = QuizModel.objects.create(
            document_name="Quiz without Course",
            start_page=1,
            end_page=5,
            subject="Subject 3",
            user=self.user,
        )

        # Send a GET request to list quizzes by course_id
        url = f"/api/quizzes/?course_id={course1.id}"
        response = self.client.get(url, format="json")

        # Assert the response status is 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert that only the quizzes belonging to the provided course are returned
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["document_name"], quiz1.document_name)

        # Verify that quiz2 and quiz3 are not in the response
        returned_quiz_ids = [quiz["id"] for quiz in response.data]
        self.assertNotIn(quiz2.id, returned_quiz_ids)
        self.assertNotIn(quiz3.id, returned_quiz_ids)

    def test_cannot_access_other_users_quiz(self):
        quiz = QuizModel.objects.create(
            document_name="Other User Quiz",
            start_page=1,
            end_page=4,
            subject="Other Subject",
            user=self.other_user,  # Specify the user here
        )
        url = f"/api/quizzes/{quiz.id}/"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.patch(url, {"document_name": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_quiz_deletes_question_answers(self):
        quiz = QuizModel.objects.create(
            document_name="Test Document",
            start_page=1,
            end_page=5,
            subject="Test Subject",
            user=self.user,
        )
        QuestionAnswerModel.objects.create(
            question="Question 1", answer="Answer 1", quiz=quiz
        )
        QuestionAnswerModel.objects.create(
            question="Question 2", answer="Answer 2", quiz=quiz
        )
        self.assertEqual(QuestionAnswerModel.objects.filter(quiz=quiz).count(), 2)
        url = f"{base}quizzes/{quiz.id}/"
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(QuestionAnswerModel.objects.filter(quiz=quiz).exists())

    def test_delete_quiz_deletes_multiple_choice_questions(self):
        quiz = QuizModel.objects.create(
            document_name="Test Document",
            start_page=1,
            end_page=5,
            subject="Test Subject",
            user=self.user,
        )
        MultipleChoiceQuestionModel.objects.create(
            question="MCQ 1",
            options=["Option 1", "Option 2"],
            answer="Option 1",
            quiz=quiz,
        )
        MultipleChoiceQuestionModel.objects.create(
            question="MCQ 2",
            options=["Option 1", "Option 2"],
            answer="Option 2",
            quiz=quiz,
        )
        self.assertEqual(
            MultipleChoiceQuestionModel.objects.filter(quiz=quiz).count(), 2
        )
        url = f"/api/quizzes/{quiz.id}/"
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MultipleChoiceQuestionModel.objects.filter(quiz=quiz).exists())


class CompendiumAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = f"{base}compendium/create/"
        self.valid_document = "test.pdf"
        self.start_page = 1
        self.end_page = 10
        self.valid_document_id = str(uuid4())

        for i in range(self.start_page, self.end_page + 1):
            post_context("Some context", i, self.valid_document, self.valid_document_id)

    def test_valid_request(self):
        """Test the create_compendium endpoint with a valid request."""
        valid_payload = {
            "id": self.valid_document_id,
            "start_page": self.start_page,
            "end_page": self.end_page,
            "subject": "Some subject",
        }
        response = self.client.post(
            self.url, data=valid_payload, content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Ensuring the response is JSON
        self.assertIsInstance(response.json(), dict)

    def test_invalid_page_range(self):
        """Test the create_compendium endpoint with an invalid page range (start > end)."""
        invalid_payload = {
            "id": self.valid_document_id,
            "start_page": 10,
            "end_page": 1,
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
                "id": self.valid_document_id,
                "start_page": self.start_page,
            },  # missing 'end'
            {
                "id": self.valid_document_id,
                "end_page": self.end_page,
            },  # missing 'start'
            {
                "start_page": self.start_page,
                "end_page": self.end_page,
            },  # missing 'document'
        ]
        for payload in invalid_payloads:
            response = self.client.post(
                self.url, data=payload, content_type="application/json"
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ChatAPITest(APITestCase):
    def setUp(self):
        # Create two users
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="password123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="password123"
        )

        # Create a course for user1
        self.course1 = Course.objects.create(name="Course 1", user=self.user1)

        # Create chats for user1
        self.chat1 = Chat.objects.create(
            user=self.user1,
            course=self.course1,
            messages=[{"role": "user", "content": "Hello"}],
        )
        self.chat2 = Chat.objects.create(
            user=self.user1, messages=[{"role": "user", "content": "Hi again"}]
        )

        # Create a chat for user2
        self.chat3 = Chat.objects.create(
            user=self.user2, messages=[{"role": "user", "content": "User2's chat"}]
        )

        # URLs
        self.chat_list_url = reverse("chat-history-list")
        self.chat_detail_url = lambda chat_id: reverse(
            "chat-history", kwargs={"chatId": chat_id}
        )
        self.chat_response_url = reverse("chat-response")

        # Authenticate user1
        refresh = RefreshToken.for_user(self.user1)
        self.refresh_token = str(refresh)
        self.access_token = str(refresh.access_token)

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.access_token)

    def create_user_file(self, user, course=None):
        """Helper method to create user files"""
        user_file = UserFile.objects.create(
            name="Test File",
            blob_name="test_blob",
            file_url="http://example.com/file.pdf",
            num_pages=10,
            content_type="application/pdf",
            user=user,
        )
        if course:
            user_file.courses.add(course)
        return user_file

    def test_chat_list_authenticated(self):
        """Test retrieving chat history for authenticated user."""
        self.authenticate()
        response = self.client.get(self.chat_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # Ensure chats are ordered by updated_at descending
        self.assertGreater(
            response.data[0]["updated_at"], response.data[1]["updated_at"]
        )

    def test_chat_list_filtered_by_course(self):
        """Test retrieving chat history filtered by courseId."""
        self.authenticate()
        response = self.client.get(
            self.chat_list_url, {"courseId": str(self.course1.id)}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], str(self.chat1.id))

    def test_chat_list_no_authentication(self):
        """Test that unauthenticated users cannot access chat history."""
        response = self.client.get(self.chat_list_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_chat_detail_authenticated(self):
        """Test retrieving a specific chat for authenticated user."""
        self.authenticate()
        response = self.client.get(self.chat_detail_url(self.chat1.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], str(self.chat1.id))
        self.assertEqual(response.data["messages"][0]["content"], "Hello")

    def test_chat_detail_nonexistent_chat(self):
        """Test retrieving a chat that does not exist."""
        self.authenticate()
        non_existent_id = uuid.uuid4()
        response = self.client.get(self.chat_detail_url(non_existent_id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Chat not found.")

    def test_chat_detail_other_user_chat(self):
        """Test that a user cannot access another user's chat."""
        self.authenticate()
        response = self.client.get(self.chat_detail_url(self.chat3.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data["error"], "Chat not found.")

    def test_chat_detail_no_authentication(self):
        """Test that unauthenticated users cannot access a specific chat."""
        response = self.client.get(self.chat_detail_url(self.chat1.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("learning_materials.views.process_answer")
    def test_chat_response_create_new_chat(self, mock_process_answer):
        """Test creating a new chat and receiving a response."""
        self.authenticate()

        # Mock the LLM response
        mock_process_answer.return_value.content = "Assistant's reply"
        mock_process_answer.return_value.citations = []

        payload = {"message": "Hello, assistant!", "courseId": str(self.course1.id)}

        response = self.client.post(self.chat_response_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("chatId", response.data)
        self.assertIn("title", response.data)

        self.assertEqual(response.data["content"], "Assistant's reply")
        self.assertEqual(response.data["role"], "assistant")

        # Verify that the chat was created
        chat_id = response.data["chatId"]
        chat = Chat.objects.get(id=chat_id)
        self.assertEqual(chat.user, self.user1)
        self.assertEqual(chat.course, self.course1)
        self.assertEqual(len(chat.messages), 2)
        self.assertEqual(chat.messages[0]["content"], "Hello, assistant!")
        self.assertEqual(chat.messages[1]["content"], "Assistant's reply")

    @patch("learning_materials.views.process_answer")
    def test_chat_response_add_message_to_existing_chat(self, mock_process_answer):
        """Test adding a message to an existing chat."""
        self.authenticate()

        # Mock the LLM response
        mock_process_answer.return_value.content = "Assistant's follow-up"
        mock_process_answer.return_value.citations = []

        payload = {"chatId": str(self.chat1.id), "message": "Can you elaborate?"}

        response = self.client.post(self.chat_response_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["chatId"], str(self.chat1.id))
        self.assertEqual(response.data["content"], "Assistant's follow-up")
        self.assertEqual(response.data["role"], "assistant")

        # Verify that the chat was updated and our message was added and the assistant's response
        self.chat1.refresh_from_db()
        self.assertEqual(len(self.chat1.messages), 3)
        self.assertEqual(self.chat1.messages[-2]["content"], "Can you elaborate?")
        self.assertEqual(self.chat1.messages[-1]["content"], "Assistant's follow-up")

    def test_chat_response_invalid_course_id(self):
        """Test creating a chat with an invalid courseId."""
        self.authenticate()
        invalid_course_id = uuid.uuid4()
        payload = {"message": "Hello!", "courseId": str(invalid_course_id)}

        response = self.client.post(self.chat_response_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_chat_response_no_authentication(self):
        """Test that unauthenticated users cannot post chat responses."""
        payload = {"message": "Hello!"}
        response = self.client.post(self.chat_response_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_chat_response_invalid_data(self):
        """Test posting chat response with invalid data."""
        self.authenticate()
        payload = {
            # Missing 'message' field
            "chatId": str(self.chat1.id)
        }
        response = self.client.post(self.chat_response_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("message", response.data)

    @patch("learning_materials.views.process_answer")
    def test_chat_response_processing_error_choose_another_model(
        self, mock_process_answer
    ):
        """Test handling errors during message processing."""
        # TODO CHECK THAT THE MODEL IS SWITCHED WHEN THE FIRST MODEL FAILS
        pass

    def test_chat_response_without_course_and_chat_id(self):
        """Test creating a chat without courseId and chatId."""
        self.authenticate()

        # Mock the LLM response
        with patch("learning_materials.views.process_answer") as mock_process_answer:
            mock_process_answer.return_value.content = "Assistant's generic reply"
            mock_process_answer.return_value.citations = []

            payload = {"message": "General inquiry."}

            response = self.client.post(self.chat_response_url, payload, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn("chatId", response.data)
            self.assertEqual(response.data["content"], "Assistant's generic reply")
            self.assertEqual(response.data["role"], "assistant")

            # Verify that a new chat was created without a course
            chat_id = response.data["chatId"]
            chat = Chat.objects.get(id=chat_id)
            self.assertEqual(chat.user, self.user1)
            self.assertIsNone(chat.course)
            self.assertEqual(len(chat.messages), 2)
            self.assertEqual(chat.messages[0]["content"], "General inquiry.")
            self.assertEqual(chat.messages[1]["content"], "Assistant's generic reply")

    def test_chat_list_ordering(self):
        """Test that the chat list is ordered by updated_at descending."""
        self.authenticate()

        # Update chat2 to have a more recent updated_at
        self.chat2.messages.append({"role": "user", "content": "Latest message"})
        self.chat2.save()

        response = self.client.get(self.chat_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        # chat2 should now be first
        self.assertEqual(response.data[0]["id"], str(self.chat2.id))
        self.assertEqual(response.data[1]["id"], str(self.chat1.id))

    @patch("learning_materials.views.process_answer")
    def test_last_used_at_updates(self, mock_process_answer):
        """Test that last_used_at is updated when a new message is posted in the same chat."""
        self.authenticate()

        # Mock the LLM response
        mock_process_answer.return_value.content = "Assistant's reply"
        mock_process_answer.return_value.citations = []

        # Start a new chat
        payload = {"courseId": str(self.course1.id), "message": "Hello, assistant!"}
        response = self.client.post(self.chat_response_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        chat_id = response.data["chatId"]

        # Retrieve the chat history
        chat_history = Chat.objects.get(id=chat_id)
        first_timestamp = chat_history.updated_at

        # Wait for a moment before sending another message to ensure the timestamp changes
        time.sleep(1)

        # Send another message in the same chat
        payload = {
            "chatId": chat_id,
            "message": "Another question?",
        }
        response = self.client.post(self.chat_response_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refresh the chat instance from the database
        chat_history.refresh_from_db()
        second_timestamp = chat_history.updated_at

        # Check that 'updated_at' has been updated
        self.assertGreater(second_timestamp, first_timestamp)
