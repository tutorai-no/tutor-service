from django.test import TestCase
from unittest.mock import patch
from learning_materials.learning_resources import GradedQuiz, Quiz, QuestionAnswer, MultipleChoiceQuestion, Page
from learning_materials.quizzes.quiz_service import generate_quiz, grade_quiz


class QuizGenerationTests(TestCase):


   @patch('learning_materials.quizzes.quiz_service.get_page_range')
   def test_generate_quiz_invalid_page_range(self, mock_get_page_range):
      """
      Test generate_quiz with an invalid page range (start > end) to ensure it raises ValueError.
      """
      # Arrange: Set up the mock for get_page_range (though it won't be used)
      mock_get_page_range.return_value = []

      # Act & Assert: Call generate_quiz with start > end and expect ValueError
      document = "test_document.pdf"
      start = 5
      end = 3
      learning_goals = ["Invalid page range test"]

      with self.assertRaises(ValueError) as context:
            generate_quiz(document, start, end, learning_goals)
      
      self.assertIn("The start index of the document cannot be after the end index!", str(context.exception))


   @patch('learning_materials.quizzes.quiz_service.get_page_range')
   def test_generate_quiz(self, mock_get_page_range):
      pdf_name = "test_document.pdf"
      
      start = 1
      end = 2

      pages = [
            Page(text="""Artiﬁcial Intelligence (AI) is the branch of computer science, which makesthe computers to mimic the human behavior to assist humans for better performance in the field of science and technology.""", 
                 page_num=start, pdf_name=pdf_name),
            Page(text="""Replicating human intelligence, solving knowledge-intensive tasks, building machines, which can perform tasks, that requirehuman intelligence, creating some system which can learn by itself are the few speciﬁc goals of AI. 
               Machine learning and deep learning are two subsets of AI which are used to solve problems using high performance algorithms and multilayer neural networks, respectively. 
               With the help of machine learning process, structured datalike genetic data, electrophysical data, and imaging data are properly investigatedin medical diagnosis. 
               AI provides advanced devices, advanced drug designing tech-niques,
               tele-treatment, physician patient communication using Chatbots and intelligent machines used for analyzing the cause and the chances of occurrence of anydisease in the field of health care.""", 
                page_num=end, pdf_name=pdf_name),
      ]
      mock_get_page_range.return_value = pages

      quiz = generate_quiz(pdf_name, start, end)

      # Check the quiz object
      self.assertIsInstance(quiz, Quiz)
      self.assertEqual(quiz.document, pdf_name)
      self.assertEqual(quiz.start, start)
      self.assertEqual(quiz.end, end)

      self.assertGreaterEqual(len(quiz.questions), 2)
      
      # Check that there are QuestionAnswer or MultipleChoiceQuestion objects
      for question in quiz.questions:
         self.assertTrue(isinstance(question, QuestionAnswer) or isinstance(question, MultipleChoiceQuestion))

     
class QuizGradingTests(TestCase):

   def setUp(self):
      self.options = ["Paris", "London", "New York", "Tokyo"]
      self.all_correct_answers = ["Paris", "4", "Jupiter", "100°C"]
      self.all_incorrect_answers = ["London", "5", "Mars", "50°C"]
      self.incomplete_answers = ["Paris", "4", "Jupiter"]
      self.quiz = Quiz(document="test_document.pdf", start=1, end=2, questions=[MultipleChoiceQuestion(question="What is the capital of France?", options=self.options, answer="Paris"), QuestionAnswer(question="What is 2 + 2?", answer="4"), QuestionAnswer(question="What is the largest planet?", answer="Jupiter"), QuestionAnswer(question="What is the boiling point of water?", answer="100°C")])
    
   def test_grade_quiz_mismatched_lengths(self):
      """
      Test grade_quiz with mismatched list lengths to ensure it raises ValueError.
      """
      # Arrange: Define test data with mismatched lengths
      questions = ["Question 1", "Question 2"]
      correct_answers = ["Answer 1"]  # Missing one answer
      student_answers = ["Student Answer 1", "Student Answer 2"]

      # Act & Assert: Call grade_quiz with mismatched lists and expect ValueError
      with self.assertRaises(ValueError) as context:
         grade_quiz(questions, correct_answers, student_answers)
      
      self.assertIn("All input lists must have the same length.", str(context.exception))

   def test_grade_quiz(self):
      
      graded_quiz = grade_quiz(self.quiz, self.all_correct_answers)

      self.assertIsInstance(graded_quiz, GradedQuiz)
      self.assertEqual(len(graded_quiz.answers_was_correct), 4)
      self.assertEqual(len(graded_quiz.feedback), 2)

      self.assertTrue(graded_quiz.answers_was_correct[0])
      self.assertFalse(graded_quiz.answers_was_correct[1])

      self.assertEqual(graded_quiz.feedback[0], "Correct! Paris is the capital of France.")
      self.assertEqual(graded_quiz.feedback[1], "Incorrect. 2 + 2 equals 4.")