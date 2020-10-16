

from django.conf.urls import url
from django.conf import settings

from .views import EolCourseEmailFragmentView
from django.contrib.auth.decorators import login_required


urlpatterns = (
    url(
        r'courses/{}/course_emails$'.format(
            settings.COURSE_ID_PATTERN,
        ),
        login_required(EolCourseEmailFragmentView.as_view()),
        name='course_email_view',
    ),
)
