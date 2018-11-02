import datetime
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .constants import ONE_DAY
from .models import Question


class QuestionModelTests(TestCase):

    def test_that_was_published_recently_with_future_question_returns_false(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is in the future.
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertFalse(future_question.was_published_recently())

    def test_that_was_published_recently_with_old_question_returns_false(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)
        self.assertFalse(old_question.was_published_recently())

    def test_that_was_published_recently_with_one_day_old_question_returns_false(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=ONE_DAY)
        old_question = Question(pub_date=time)
        self.assertFalse(old_question.was_published_recently())

    def test_that_was_published_recently_with_recent_question_returns_true(self):
        """
        was_published_recently() returns True for questions whose pub_date
        is within the last day.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertTrue(recent_question.was_published_recently())


def create_question(question_text, days, should_add_choice=True):
    """
    Create a question with the given `question_text` and published the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    """
    time = timezone.now() + datetime.timedelta(days=days)
    question = Question.objects.create(question_text=question_text, pub_date=time)
    if should_add_choice:
        question.choice_set.create(choice_text="The only answer", votes=0)
    return question


class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_past_question(self):
        """
        Questions with a pub_date in the past are displayed on the
        index page.
        """
        create_question(question_text="Past question.", days=-30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question.>']
        )

    def test_future_question(self):
        """
        Questions with a pub_date in the future aren't displayed on
        the index page.
        """
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_future_question_and_past_question(self):
        """
        Even if both past and future questions exist, only past questions
        are displayed.
        """
        create_question(question_text="Past question.", days=-30)
        create_question(question_text="Future question.", days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question.>']
        )

    def test_two_past_questions(self):
        """
        The questions index page may display multiple questions.
        """
        create_question(question_text="Past question 1.", days=-30)
        create_question(question_text="Past question 2.", days=-5)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Past question 2.>', '<Question: Past question 1.>']
        )

    def test_that_only_questions_with_choices_are_displayed(self):
        create_question(question_text="First added", days=-3)
        create_question(question_text="Second added", days=-2)
        create_question(question_text="No choice", days=-2, should_add_choice=False)
        response =self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            ['<Question: Second added>', '<Question: First added>']
         )


class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        """
        The detail view of a question with a pub_date in the future
        returns a 404 not found.
        """
        future_question = create_question(question_text='Future question.', days=5)
        url = reverse('polls:detail', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
        The detail view of a question with a pub_date in the past
        displays the question's text.
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)

    def test_that_questions_without_choices_are_not_displayed(self):
        question_without_choice = create_question(question_text="No choice", days=-2, should_add_choice=False)
        url = reverse('polls:detail', args=(question_without_choice.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class QuestionResultsViewTests(TestCase):
    def test_future_question(self):
        """
        The detail view of a question with a pub_date in the future
        returns a 404 not found.
        """
        future_question = create_question(question_text='Future question.', days=5)
        url = reverse('polls:results', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
        The detail view of a question with a pub_date in the past
        displays the question's text.
        """
        past_question = create_question(question_text='Past Question.', days=-5)
        url = reverse('polls:results', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)

    def test_that_questions_without_choices_are_not_displayed(self):
        question_without_choice = create_question(question_text="No choice", days=-2, should_add_choice=False)
        url = reverse('polls:results', args=(question_without_choice.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class TestVoting(TestCase):
    def test_that_in_question_doesnt_exist_404_is_returned(self):
        non_existing_question_id = 777
        url = reverse('polls:vote', args=(non_existing_question_id,))
        response = self.client.post(
            url,
        )
        self.assertEqual(response.status_code, 404)

    def test_that_when_no_choice_is_made_vote_returns_to_question_details_view(self):
        question = create_question(question_text='Past Question.', days=-5)
        url = reverse('polls:vote', args=(question.id, ))
        response = self.client.post(
            url,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, question.question_text)

    def test_that_when_choice_is_made_vote_redirects_to_results_view(self):
        question = create_question(question_text='Past Question.', days=-5)
        choice = question.choice_set.create(choice_text="second choice", votes=0)
        url = reverse('polls:vote', args=(question.id, ))
        response = self.client.post(
            url,
            data={'choice': (choice.id)}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('polls:results', args=(question.id,)))
