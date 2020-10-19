

from django.conf.urls import url
from django.conf import settings

from .views import EolCourseEmailFragmentView, get_received_emails, get_sended_emails, get_all_users_enrolled
from django.contrib.auth.decorators import login_required


urlpatterns = (
    url(
        r'courses/{}/course_emails$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        login_required(EolCourseEmailFragmentView.as_view()),
        name='course_email_view',
    ),
    url(
        r'courses/{}/course_emails/received'.format(
            settings.COURSE_ID_PATTERN,
        ),
        login_required(get_received_emails),
        name='course_email_received_emails',
    ),
    url(
        r'courses/{}/course_emails/sended'.format(
            settings.COURSE_ID_PATTERN,
        ),
        login_required(get_sended_emails),
        name='course_email_sended_emails',
    ),
    url(
        r'courses/{}/course_emails/users'.format(
            settings.COURSE_ID_PATTERN,
        ),
        login_required(get_all_users_enrolled),
        name='course_email_users',
    ),
)
