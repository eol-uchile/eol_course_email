from django.conf import settings
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from django.utils.translation import ugettext_noop

from lms.djangoapps.courseware.tabs import EnrolledTab
from xmodule.tabs import TabFragmentViewMixin

from django.contrib.auth.models import User


class EolCourseEmailTab(TabFragmentViewMixin, EnrolledTab):
    type = 'eol_course_email'
    title = ugettext_noop('Contacto')
    priority = None
    view_name = 'eol/course_email:course_email_view'
    fragment_view_name = 'eol_course_email.views.EolCourseEmailFragmentView'
    is_hideable = True
    is_default = True
    is_hidden = True
    body_class = 'eol_course_email'
    online_help_token = 'eol_course_email'

    
    def __init__(self, tab_dict):
        super(EolCourseEmailTab, self).__init__(tab_dict)
        self.is_hidden = tab_dict.get('eol_visible', True)

    def to_json(self):
        """ Return a dictionary representation of this tab. """
        to_json_val = super(EolCourseEmailTab, self).to_json()
        to_json_val.update({'eol_visible': self.is_hidden})
        return to_json_val

    @classmethod
    def is_enabled(cls, course, user=None):
        """
            Check if user is enrolled on course
        """
        if not super(EolCourseEmailTab, cls).is_enabled(course, user):
            return False
        return configuration_helpers.get_value('EOL_COURSE_EMAIL_TAB_ENABLED', False)
