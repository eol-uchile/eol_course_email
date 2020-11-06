# -*- coding: utf-8 -*-


from mock import patch, Mock
import json

from django.test import TestCase, Client
from django.urls import reverse

from util.testing import UrlResetMixin
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory, CourseEnrollmentFactory

from six.moves import range

from . import views
from .models import EolCourseEmail

USER_COUNT = 11

DEFAULT_TEST_DATA_LENGTH = 5
def generate_default_test_data(course_id, sender_user, receiver_user_list):
    for i in range(DEFAULT_TEST_DATA_LENGTH):
        email = EolCourseEmail(
            course_id=course_id,
            sender_user=sender_user,
            subject="Subject {}".format(i),
            message="Message {}".format(i)
        )
        email.save()
        email.receiver_users.add(*receiver_user_list)

class TestEolCourseEmailView(UrlResetMixin, ModuleStoreTestCase):
    def setUp(self):
        super(TestEolCourseEmailView, self).setUp()
        # create a course
        self.course = CourseFactory.create(org='mss', course='999',
                                           display_name='eol course email')

        # Create users, enroll 
        self.users = [UserFactory.create() for _ in range(USER_COUNT)]
        for user in self.users:
            CourseEnrollmentFactory.create(user=user, course_id=self.course.id)

        # Patch the comment client user save method so it does not try
        # to create a new cc user when creating a django user
        with patch('student.models.cc.User.save'):
            # Create the student
            self.student = UserFactory(username='student', password='test', email='student@edx.org')
            # Enroll the student in the course
            CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

            # Create and Enroll staff user
            self.staff_user = UserFactory(username='staff_user', password='test', email='staff@edx.org', is_staff=True)
            CourseEnrollmentFactory(user=self.staff_user, course_id=self.course.id)

            # Log the student in
            self.client = Client()
            self.assertTrue(self.client.login(username='student', password='test'))

            # Log the user staff in
            self.staff_client = Client()
            self.assertTrue(self.staff_client.login(username='staff_user', password='test'))

    def test_render_page(self):
        """
            Test correct render page with an IFrame
        """
        url = reverse('course_email_view',
                      kwargs={'course_id': self.course.id})
        self.response = self.client.get(url)
        self.assertEqual(self.response.status_code, 200)
        self.assertIn( 'id="reactIframe"', self.response.content.decode("utf-8"))

    def test_get_received_emails(self):
        """
            Test get user received emails
        """
        # Empty list
        response = self.client.get(
            reverse(
                'course_email_received_emails',
                    kwargs={'course_id': self.course.id}
            )
        )
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(content, [])

        # Generate data + get email list
        generate_default_test_data(self.course.id, self.staff_user, [self.student, self.staff_user])
        response = self.client.get(
            reverse(
                'course_email_received_emails',
                    kwargs={'course_id': self.course.id}
            )
        )
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(content), DEFAULT_TEST_DATA_LENGTH)

    def test_get_sended_emails(self):
        """
            Test get user sended emails
        """
        # Empty list
        response = self.client.get(
            reverse(
                'course_email_sended_emails',
                    kwargs={'course_id': self.course.id}
            )
        )
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(content, [])

        # Generate data + get email list
        generate_default_test_data(self.course.id, self.student, [self.staff_user])
        response = self.client.get(
            reverse(
                'course_email_sended_emails',
                    kwargs={'course_id': self.course.id}
            )
        )
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(content), DEFAULT_TEST_DATA_LENGTH)
