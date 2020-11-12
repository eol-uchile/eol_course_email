from django.conf import settings
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from django.utils.translation import ugettext_noop

from courseware.tabs import EnrolledTab
from xmodule.tabs import TabFragmentViewMixin

from django.contrib.auth.models import User


class EolCourseEmailTab(TabFragmentViewMixin, EnrolledTab):
    type = 'eol_course_email'
    title = ugettext_noop('Contacto')
    priority = None
    view_name = 'course_email_view'
    fragment_view_name = 'eol_course_email.views.EolCourseEmailFragmentView'
    is_hideable = True
    is_default = False
    body_class = 'eol_course_email'
    online_help_token = 'eol_course_email'

    @classmethod
    def is_enabled(cls, course, user=None):
        """
            Check if user is enrolled on course
        """
        if not super(EolCourseEmailTab, cls).is_enabled(course, user):
            return False
        return configuration_helpers.get_value('EOL_COURSE_EMAIL_TAB_ENABLED', False)
