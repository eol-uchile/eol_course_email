# -*- coding: utf-8 -*-


from mock import patch, Mock
import json

from django.test import TestCase, Client
from django.urls import reverse
from django.test import override_settings

from common.djangoapps.util.testing import UrlResetMixin
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from xmodule.modulestore.tests.factories import CourseFactory
from common.djangoapps.student.tests.factories import UserFactory, CourseEnrollmentFactory
from common.djangoapps.student.roles import CourseStaffRole

from six.moves import range

from . import views, email_tasks, upload
from .models import EolCourseEmail, FilesCourseEmail


USER_COUNT = 11

DEFAULT_TEST_DATA_LENGTH = 5
def generate_default_test_data(course_id, sender_user, receiver_user_list):
    for i in range(DEFAULT_TEST_DATA_LENGTH):
        file = FilesCourseEmail(
            file_name='name',
            file_path='course-v1:eol+mss-01+2021/path',
            content_type='content_type'
        )
        file.save()
        email = EolCourseEmail(
            course_id=course_id,
            sender_user=sender_user,
            subject="Subject {}".format(i),
            message="Message {}".format(i)
        )
        email.save()
        email.files.add(file)
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
        with patch('common.djangoapps.student.models.cc.User.save'):
            # Create the student
            self.student = UserFactory(username='student', password='test', email='student@edx.org')
            # Enroll the student in the course
            CourseEnrollmentFactory(user=self.student, course_id=self.course.id)

            # Create and Enroll staff user
            self.staff_user = UserFactory(username='staff_user', password='test', email='staff@edx.org', is_staff=True)
            CourseEnrollmentFactory(user=self.staff_user, course_id=self.course.id)
            CourseStaffRole(self.course.id).add_users(self.staff_user)

            # Log the student in
            self.client = Client()
            self.assertTrue(self.client.login(username='student', password='test'))

            # Log the user staff in
            self.staff_client = Client()
            self.assertTrue(self.staff_client.login(username='staff_user', password='test'))

    @patch("eol_course_email.views._has_page_access")
    def test_render_page(self, has_page_access):
        """
            Test correct render page with an IFrame
        """
        has_page_access.side_effect = [True]
        url = reverse('eol/course_email:course_email_view',
                      kwargs={'course_id': self.course.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn( 'id="reactIframe"', response.content.decode("utf-8"))

    @patch("eol_course_email.views._has_page_access")
    def test_get_user_email(self, has_page_access):
        """
            Test get user email
        """
        has_page_access.side_effect = [True]
        # Empty list
        response = self.client.get(
            reverse(
                'eol/course_email:course_email_user_email',
                    kwargs={'course_id': self.course.id}
            )
        )
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(content, self.student.email)
    
    @patch("eol_course_email.views._has_page_access")
    def test_get_received_emails(self, has_page_access):
        """
            Test get user received emails
        """
        has_page_access.side_effect = [True, True]
        # Empty list
        response = self.client.get(
            reverse(
                'eol/course_email:course_email_received_emails',
                    kwargs={'course_id': self.course.id}
            )
        )
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(content, [])

        # Generate data + get email list
        generate_default_test_data(self.course.id, self.staff_user, [self.student, self.staff_user])
        response = self.client.get(
            reverse(
                'eol/course_email:course_email_received_emails',
                    kwargs={'course_id': self.course.id}
            )
        )
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(content), DEFAULT_TEST_DATA_LENGTH)

    @patch("eol_course_email.views._has_page_access")
    def test_get_sended_emails(self, has_page_access):
        """
            Test get user sended emails
        """
        has_page_access.side_effect = [True, True]
        # Empty list
        response = self.client.get(
            reverse(
                'eol/course_email:course_email_sended_emails',
                    kwargs={'course_id': self.course.id}
            )
        )
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(content, [])

        # Generate data + get email list
        generate_default_test_data(self.course.id, self.student, [self.staff_user])
        response = self.client.get(
            reverse(
                'eol/course_email:course_email_sended_emails',
                    kwargs={'course_id': self.course.id}
            )
        )
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(content), DEFAULT_TEST_DATA_LENGTH)

    @patch("eol_course_email.views._has_page_access")
    def test_get_users_enrolled(self, has_page_access):
        """
            Test get all users enrolled
        """
        has_page_access.side_effect = [True]
        response = self.client.get(
            reverse(
                'eol/course_email:course_email_users',
                    kwargs={'course_id': self.course.id}
            )
        )
        content = json.loads(response.content.decode("utf-8"))
        self.assertEqual(len(content), USER_COUNT + 2) # Test users + student + staff_user

    def test_get_access_roles(self):
        """
            Test get users with access roles
        """
        access_roles = views.get_access_roles(self.course.id)
        self.assertEqual(access_roles, ['staff_user'])

    @patch("eol_course_email.views._has_page_access")
    def test_send_new_email(self, has_page_access):
        """
            Test post new email
        """
        has_page_access.side_effect = [True, True, True, True]
        response = self.client.get(
            reverse(
                'eol/course_email:course_email_send_new_email',
                    kwargs={'course_id': self.course.id}
            )
        )
        self.assertEqual(response.status_code, 400) # not a GET request
        response = self.client.post(
            reverse(
                'eol/course_email:course_email_send_new_email',
                    kwargs={'course_id': self.course.id}
            )
        )
        self.assertEqual(response.status_code, 400) # POST request without data required
        post_data = {
            'messageInput' : "messageInput",
            'studentsInput' : ["student"],
            'staffInput': ["staff_user"]
        }
        response = self.client.post(
            reverse(
                'eol/course_email:course_email_send_new_email',
                    kwargs={'course_id': self.course.id}
            ), post_data
        )
        self.assertEqual(response.status_code, 400) # POST request without subject required

        post_data = {
            'subjectInput' : "subjectInput",
            'messageInput' : "messageInput",
            'studentsInput' : ["student"],
            'staffInput': ["staff_user"]
        }

        with override_settings(RATELIMIT_ENABLE=False):
            response = self.client.post(
                reverse(
                    'eol/course_email:course_email_send_new_email',
                        kwargs={'course_id': self.course.id}
                ), post_data
            )
            self.assertEqual(response.status_code, 201) # POST request with all data


            exists = EolCourseEmail.objects.filter(
                course_id=self.course.id,
                subject="subjectInput"
            ).exists()
            self.assertEqual(exists, True) # Check if email has been created

    def test_send_email_task(self):
        """"
            Test send email task
        """
        email = email_tasks.send_email(
            "from_email@email.com", 
            "reply_to@email.com", 
            "to_email@email.com", 
            "subject", 
            "html_message", 
            "plain_message",
            '{}'
        )
        self.assertEqual(email, 1) # success

    def test_build_file_storage_path(self):
        """
            Test building the file storage path. Uses course_id, sha1, and original filename extension
        """
        path = upload.get_file_storage_path('course_id', "sha1", "test.pdf")
        self.assertEqual(path, "course_id/sha1.pdf")

    @patch("eol_course_email.upload.os")
    @patch("eol_course_email.upload.File", return_value="call_file")
    @patch("eol_course_email.upload.get_storage")
    @patch(
        "eol_course_email.upload.get_file_storage_path", return_value="file_path"
    )
    @patch("eol_course_email.upload.get_sha1", return_value="sha1")
    @patch("eol_course_email.upload.file_size_over_limit", return_value=False)
    def test_upload_file(
        self,
        file_size_over_limit,
        get_sha1,
        get_file_storage_path,
        get_storage,
        mock_file,
        mock_os,
    ):
        """
            Test save file with display name and file
        """
        mock_file_object = Mock()
        mock_file_object.configure_mock(name="file_name", content_type="content_type")
        get_storage.configure_mock(size=Mock(return_value="1234"))
        mock_os.configure_mock(path=Mock(join=Mock(return_value="path_join")))

        course_id = 'course_id'
        result = upload.upload_file(course_id, mock_file_object)

        file_size_over_limit.assert_called_once_with(mock_file_object)
        get_sha1.assert_called_once_with(mock_file_object)
        get_storage().save.assert_called_once_with('file_path', "call_file")
        mock_file.assert_called_once_with(mock_file_object)

        self.assertEqual(result['error'], False)
        self.assertEqual(result['file'].file_name, "file_name")
        self.assertEqual(result['file'].file_path, "file_path")
        self.assertEqual(result['file'].content_type, "content_type")