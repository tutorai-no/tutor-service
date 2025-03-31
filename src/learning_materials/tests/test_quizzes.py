from django.test import TestCase
from unittest.mock import patch
from learning_materials.learning_resources import (
    GradedQuiz,
    Quiz,
    QuestionAnswer,
    MultipleChoiceQuestion,
    Citation,
)
from learning_materials.quizzes.quiz_service import generate_quiz, grade_quiz


class QuizGenerationTests(TestCase):

    @patch("learning_materials.quizzes.quiz_service.get_page_range")
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

        self.assertIn(
            "The start index of the document cannot be after the end index!",
            str(context.exception),
        )

    @patch("learning_materials.quizzes.quiz_service.get_page_range")
    def test_generate_quiz(self, mock_get_page_range):
        document_name = "test_document.pdf"

        start = 1
        end = 2
        subject = "Artificial Intelligence"

        pages = [
            Citation(
                text="""Artiﬁcial Intelligence (AI) is the branch of computer science,
                which makesthe computers to mimic the human behavior to assist humans for better performance in the field of science and technology.""",
                page_num=start,
                document_name=document_name,
            ),
            Citation(
                text="""Replicating human intelligence, solving knowledge-intensive tasks, building machines, which can perform tasks, that requirehuman intelligence,
                creating some system which can learn by itself are the few speciﬁc goals of AI.
                Machine learning and deep learning are two subsets of AI which are used to solve problems using high performance algorithms and multilayer neural networks, respectively.
                With the help of machine learning process, structured datalike genetic data, electrophysical data,
                and imaging data are properly investigatedin medical diagnosis.
                AI provides advanced devices, advanced drug designing tech-niques, tele-treatment,
                physician patient communication using Chatbots and intelligent machines used for analyzing
                the cause and the chances of occurrence of anydisease in the field of health care.""",
                page_num=end,
                document_name=document_name,
            ),
        ]
        mock_get_page_range.return_value = pages

        quiz = generate_quiz(document_name, start, end, subject)

        # Check the quiz object
        self.assertIsInstance(quiz, Quiz)
        self.assertEqual(quiz.document_name, document_name)
        self.assertEqual(quiz.start_page, start)
        self.assertEqual(quiz.end_page, end)

        self.assertGreaterEqual(len(quiz.questions), 2)

        # Check that there are QuestionAnswer or MultipleChoiceQuestion objects
        for question in quiz.questions:
            self.assertTrue(
                isinstance(question, QuestionAnswer)
                or isinstance(question, MultipleChoiceQuestion)
            )


class QuizGradingTests(TestCase):

    def setUp(self):
        # Set up sample data for the test cases
        self.options = ["Paris", "London", "New York", "Tokyo"]
        self.all_correct_answers = ["Paris", "4", "Jupiter", "100°C"]
        self.all_incorrect_answers = ["London", "5", "Mars", "50°C"]
        self.partial_correct_answers = ["Paris", "5", "Jupiter", "100°C"]
        self.incomplete_answers = ["Paris", "4", "Jupiter"]

        # A diverse quiz with mixed types of questions
        self.diverse_quiz = Quiz(
            document_name="test_document.pdf",
            start_page=1,
            end_page=2,
            questions=[
                MultipleChoiceQuestion(
                    question="What is the capital of France?",
                    options=self.options,
                    answer="Paris",
                ),
                QuestionAnswer(question="What is 2 + 2?", answer="4"),
                QuestionAnswer(
                    question="What is the largest planet?", answer="Jupiter"
                ),
                QuestionAnswer(
                    question="What is the boiling point of water?", answer="100°C"
                ),
            ],
        )

        # A quiz with only multiple-choice questions
        self.only_multiple_choice_quiz = Quiz(
            document_name="test_document.pdf",
            start_page=1,
            end_page=2,
            questions=[
                MultipleChoiceQuestion(
                    question="What is the capital of France?",
                    options=self.options,
                    answer="Paris",
                ),
                MultipleChoiceQuestion(
                    question="What is the capital of Japan?",
                    options=self.options,
                    answer="Tokyo",
                ),
            ],
        )

        # A quiz with only question-answer type questions
        self.only_question_answer_quiz = Quiz(
            document_name="test_document.pdf",
            start_page=1,
            end_page=2,
            questions=[
                QuestionAnswer(question="What is 2 + 2?", answer="4"),
                QuestionAnswer(
                    question="What is the boiling point of water?", answer="100°C"
                ),
            ],
        )

    def test_grade_quiz_mismatched_lengths(self):
        """
        Test grade_quiz with mismatched list lengths to ensure it raises ValueError.
        """
        # Act & Assert: Call grade_quiz with mismatched lists and expect ValueError
        with self.assertRaises(ValueError) as context:
            grade_quiz(self.diverse_quiz, self.incomplete_answers)

        self.assertIn(
            "All input lists must have the same length.", str(context.exception)
        )

    def test_grade_diverse_quiz_all_correct(self):
        """
        Test grading a diverse quiz with a all correct answers
        """
        # Grade the quiz with all correct answers
        all_correct_graded_quiz = grade_quiz(
            self.diverse_quiz, self.all_correct_answers
        )

        # Assert the GradedQuiz type and the feedback length
        self.assertIsInstance(all_correct_graded_quiz, GradedQuiz)
        amount_of_correct_answers = all_correct_graded_quiz.answers_was_correct.count(
            True
        )
        self.assertEqual(amount_of_correct_answers, len(self.all_correct_answers))
        self.assertEqual(
            len(all_correct_graded_quiz.feedback), len(self.all_correct_answers)
        )

    def test_grade_diverse_quiz_all_incorrect(self):
        """
        Test grading a diverse quiz with all incorrect answers.
        """
        # Grade the quiz with all incorrect answers
        all_incorrect_graded_quiz = grade_quiz(
            self.diverse_quiz, self.all_incorrect_answers
        )

        # Assert that no answers were correct and feedback length matches input
        self.assertIsInstance(all_incorrect_graded_quiz, GradedQuiz)
        amount_of_correct_answers = all_incorrect_graded_quiz.answers_was_correct.count(
            True
        )
        self.assertEqual(amount_of_correct_answers, 0)
        self.assertEqual(
            len(all_incorrect_graded_quiz.feedback), len(self.all_incorrect_answers)
        )

    def test_grade_diverse_quiz_mix_correct_incorrect(self):
        """
        Test grading a diverse quiz with all incorrect answers.
        """
        # Grade the quiz with all incorrect answers
        all_incorrect_graded_quiz = grade_quiz(
            self.diverse_quiz, self.partial_correct_answers
        )

        # Assert that no answers were correct and feedback length matches input
        self.assertIsInstance(all_incorrect_graded_quiz, GradedQuiz)
        amount_of_correct_answers = all_incorrect_graded_quiz.answers_was_correct.count(
            True
        )
        self.assertEqual(amount_of_correct_answers, 3)

    def test_grade_quiz_with_only_multiple_choice(self):
        """
        Test grade_quiz with only multiple-choice questions.
        """
        # Assume the correct answers are partially correct
        partial_multiple_choice_answers = [
            "Paris",
            "London",
        ]  # Only the first answer is correct

        # Grade the multiple-choice quiz
        graded_quiz = grade_quiz(
            self.only_multiple_choice_quiz, partial_multiple_choice_answers
        )

        # Assert that the grading results match the expected output
        self.assertIsInstance(graded_quiz, GradedQuiz)
        self.assertEqual(
            len(graded_quiz.answers_was_correct), len(partial_multiple_choice_answers)
        )
        self.assertEqual(
            graded_quiz.answers_was_correct.count(True), 1
        )  # Only one correct
        self.assertEqual(
            len(graded_quiz.feedback), len(partial_multiple_choice_answers)
        )

    def test_grade_quiz_with_only_question_answer(self):
        """
        Test grade_quiz with only question-answer type questions.
        """
        # Assume both answers are correct
        qa_answers = ["4", "100°C"]

        # Grade the question-answer quiz
        graded_quiz = grade_quiz(self.only_question_answer_quiz, qa_answers)

        # Assert that all answers were correct
        self.assertIsInstance(graded_quiz, GradedQuiz)
        amount_of_correct_answers = graded_quiz.answers_was_correct.count(True)
        self.assertEqual(amount_of_correct_answers, len(qa_answers))
        self.assertTrue(all(graded_quiz.answers_was_correct))  # All correct
        self.assertEqual(len(graded_quiz.feedback), len(qa_answers))
