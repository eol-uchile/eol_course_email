# -*- coding: utf-8 -*-
import urllib.parse
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from django.conf import settings
from lms.djangoapps.courseware.courses import get_course_by_id
from lms.djangoapps.courseware.tabs import get_course_tab_list
from django.utils.html import strip_tags
from django.urls import reverse
from ratelimit.decorators import ratelimit

from django.template.loader import render_to_string
from web_fragments.fragment import Fragment
from courseware.courses import get_course_with_access
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from opaque_keys.edx.keys import CourseKey
from django.contrib.auth.models import User
from django.http import Http404, HttpResponse
from bson import json_util
import json
from django.db.models.functions import Lower
from .models import EolCourseEmail
from .email_tasks import send_email
from .upload import upload_file, get_storage
from student.models import CourseAccessRole
from django.core.serializers import serialize

import logging
logger = logging.getLogger(__name__)


class EolCourseEmailFragmentView(EdxFragmentView):
    def render_to_fragment(self, request, course_id, **kwargs):
        if(not _has_page_access(request, course_id)):
            raise Http404()

        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, "load", course_key)
        context = {
            "course": course,
            "DEV_URL": configuration_helpers.get_value('EOL_COURSE_EMAIL_DEV_URL', settings.EOL_COURSE_EMAIL_DEV_URL)
        }
        html = render_to_string('eol_course_email/eol_course_email_fragment.html', context)
        fragment = Fragment(html)
        return fragment
            

def _has_page_access(request, course_id):
    """
        Check if tab is enabled and user is enrolled
    """ 
    course_key = CourseKey.from_string(course_id)
    course = get_course_with_access(request.user, "load", course_key)
    tabs = get_course_tab_list(request.user, course)
    tabs_list = [tab.tab_id for tab in tabs]
    if 'eol_course_email' not in tabs_list:
        return False
    return User.objects.filter(
        courseenrollment__course_id=course_key,
        courseenrollment__is_active=1,
        pk = request.user.id
    ).exists()

def get_user_email(request, course_id):
    """
        Get user email
    """
    if(not _has_page_access(request, course_id)):
        raise Http404()
    user = request.user
    data = json.dumps(request.user.email, default=json_util.default)
    return HttpResponse(data)

def get_received_emails(request, course_id):
    """
        Get all received emails
    """
    if(not _has_page_access(request, course_id)):
        raise Http404()
    user = request.user
    emails = EolCourseEmail.objects.filter(
        course_id=course_id,
        receiver_users__in=[user],
        deleted_at__isnull=True
    ).order_by('-created_at')
    received_emails = [
        {
            'subject' : e.subject,
            'message' : e.message,
            'files_list' : e.files_list,
            'sender_user' : e.sender_user.profile.name,
            'created_at' : e.created_at,
        }
        for e in emails
    ]
    data = json.dumps(list(received_emails), default=json_util.default)
    return HttpResponse(data)

def get_sended_emails(request, course_id):
    """
        Get all sended emails
    """
    if(not _has_page_access(request, course_id)):
        raise Http404()
    user = request.user
    emails = EolCourseEmail.objects.filter(
        course_id=course_id,
        sender_user=user,
        deleted_at__isnull=True
    ).order_by('-created_at')
    sended_emails = [
        {
            'receiver_users_list' : e.receiver_users_list,
            'files_list' : e.files_list,
            'sender_user' : e.sender_user.profile.name,
            'subject' : e.subject,
            'message' : e.message,
            'created_at' : e.created_at
        } 
        for e in emails
    ]
    data = json.dumps(sended_emails, default=json_util.default)
    return HttpResponse(data)

def get_all_users_enrolled(request, course_id):
    """
        Get all users enrolled in the course
    """
    if(not _has_page_access(request, course_id)):
        raise Http404()
    user = request.user
    roles = get_access_roles(course_id)
    users = User.objects.filter(
        courseenrollment__course_id=course_id,
        courseenrollment__is_active=1
    ).values(
        'username',
        'profile__name'
    ).order_by(Lower('profile__name'))
    for u in users:
        u['has_role'] = u['username'] in roles
    data = json.dumps(list(users), default=json_util.default)
    return HttpResponse(data)

def get_access_roles(course_id):
    """
        Return users lists with access roles (staff and instructor)
    """
    roles = CourseAccessRole.objects.filter(
        role__in=('staff', 'instructor'),
        course_id=course_id
    ).values_list(
        'user__username',
        flat=True,
    )
    return list(roles)

@ratelimit(key=settings.EOL_COURSE_EMAIL_POST_EMAIL_KEY, rate=settings.EOL_COURSE_EMAIL_POST_EMAIL_RATE)
def send_new_email(request, course_id):
    """
        POST
        Store data and send email
    """
    if(not _has_page_access(request, course_id)):
        raise Http404()
    # check method and params
    if request.method != "POST":
        logger.warning("Wrong Method/data")
        return HttpResponse(status=400)
    data = request.POST
    if 'subjectInput' not in data or 'messageInput' not in data or 'studentsInput' not in data or 'staffInput' not in data:
        logger.warning("POST without all data")
        return HttpResponse(status=400)

    # Ratelimit: too many API calls
    if getattr(request, 'limited', False):
        return HttpResponse('ratelimit', status=403)

    if request.FILES:
        upload = upload_file(course_id, request.FILES['fileInput'])
        # File exceded max size
        if upload['error']:
            return HttpResponse('file_size', status=409)
    user = request.user
    subject = data['subjectInput']
    message = data['messageInput']
    receiver_usernames = data['studentsInput'].split(",") + data['staffInput'].split(",")


    # get users
    receiver_users = User.objects.filter(
        courseenrollment__course_id=course_id,
        courseenrollment__is_active=1,
        username__in=receiver_usernames
    )

    # store data
    email = EolCourseEmail(
        course_id=course_id,
        sender_user=user,
        subject=subject.strip(),
        message=message.strip()
    )
    email.save()
    email.receiver_users.add(*receiver_users)

    if request.FILES:
        email.files.add(upload['file'])

    # Generate and send email
    redirect_url = reverse(
        'eol/course_email:course_email_view',
            kwargs={
                'course_id': email.course_id
            }
    )
    generate_email(email, request.build_absolute_uri(redirect_url))

    return HttpResponse(status=201)

def generate_email(email, redirect_url):
    """"
        Generate html/plain message and send email to each user
    """
    platform_name = configuration_helpers.get_value(
            'PLATFORM_NAME', settings.PLATFORM_NAME)
    # course_key = CourseKey.from_string(course_id)
    course = get_course_by_id(email.course_id)
    context = {
        "course_name": course.display_name_with_default,
        "platform_name": platform_name,
        "redirect_url": redirect_url,
        "message": email.message,
        "sender_name": email.sender_user.profile.name.title()
    }
    from_email = configuration_helpers.get_value(
        'email_from_address',
        settings.BULK_EMAIL_DEFAULT_FROM_EMAIL
    )
    html_message = render_to_string(
        'eol_course_email/email.txt', context)
    plain_message = strip_tags(html_message)
    email_subject = "{} - {}".format(email.subject, course.display_name_with_default)
    files = json.dumps(list(email.files.all().values('file_name', 'file_path', 'content_type')), default=json_util.default)
    for u in email.receiver_users.all():
        send_email.delay(
            from_email, 
            email.sender_user.email, 
            u.email, 
            email_subject, 
            html_message, 
            plain_message, 
            files
        )

def get_file_url(request, course_id, file, content_type):
    """
        Get file url: course_id/file_hash.ext
    """
    if(not _has_page_access(request, course_id)):
        raise Http404()
    try:
        file_path = "{}/{}".format(course_id, file)
        return HttpResponse(
        get_storage().open(file_path).read(),
        content_type=urllib.parse.unquote(content_type),
        )
    except Exception: 
        raise Http404()
