# -*- coding: utf-8 -*-

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from django.conf import settings
from lms.djangoapps.courseware.courses import get_course_by_id
from django.utils.html import strip_tags
from django.urls import reverse

from django.template.loader import render_to_string
from web_fragments.fragment import Fragment
from courseware.courses import get_course_with_access
from openedx.core.djangoapps.plugin_api.views import EdxFragmentView
from opaque_keys.edx.keys import CourseKey
from django.contrib.auth.models import User
from django.http import Http404, HttpResponse
from bson import json_util
import json
from .models import EolCourseEmail
from .email_tasks import send_email
from student.models import CourseAccessRole

import logging
logger = logging.getLogger(__name__)

class EolCourseEmailFragmentView(EdxFragmentView):
    def render_to_fragment(self, request, course_id, **kwargs):
        if(not self.has_page_access(request.user, course_id)):
            raise Http404()

        course_key = CourseKey.from_string(course_id)
        course = get_course_with_access(request.user, "load", course_key)
        context = {
            "course": course
        }
        html = render_to_string('eol_course_email/eol_course_email_fragment.html', context)
        fragment = Fragment(html)
        return fragment
            

    def has_page_access(self, user, course_id):
        course_key = CourseKey.from_string(course_id)
        return User.objects.filter(
            courseenrollment__course_id=course_key,
            courseenrollment__is_active=1,
            pk = user.id
        ).exists()

def get_received_emails(request, course_id):
    """
        Get all received emails
    """
    logger.warning("Received emails")
    user = request.user
    logger.warning(user)
    emails = EolCourseEmail.objects.filter(
        course_id=course_id,
        receiver_users__in=[user],
        deleted_at__isnull=True
    ).values(
        'subject',
        'message',
        'sender_user__profile__name',
        'created_at'
    ).order_by('-created_at')
    logger.warning(emails)
    data = json.dumps(list(emails), default=json_util.default)
    return HttpResponse(data)

def get_sended_emails(request, course_id):
    """
        Get all sended emails
    """
    user = request.user
    emails = EolCourseEmail.objects.filter(
        course_id=course_id,
        sender_user=user,
        deleted_at__isnull=True
    ).order_by('-created_at')
    sended_emails = [
        {
            'receiver_users_list' : e.receiver_users_list,
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
    user = request.user
    roles = get_access_roles(course_id)
    users = User.objects.filter(
        courseenrollment__course_id=course_id,
        courseenrollment__is_active=1
    ).values(
        'username',
        'profile__name',
        'email'
    )
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

def send_new_email(request, course_id):
    """
        POST
        Store data and send email
    """
    # check method and params
    if request.method != "POST":
        return HttpResponse(status=400)
    data = json.loads(request.body.decode())
    if 'subjectInput' not in data or 'messageInput' not in data or 'studentsInput' not in data or 'staffInput' not in data:
        return HttpResponse(status=400)
    user = request.user
    subject = data['subjectInput']
    message = data['messageInput']
    receiver_usernames = data['studentsInput'] + data['staffInput']

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

    # Generate and send email
    redirect_url = reverse(
        'course_email_view',
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
        "sender_name": email.sender_user.profile.name
    }
    from_email = configuration_helpers.get_value(
        'email_from_address',
        settings.BULK_EMAIL_DEFAULT_FROM_EMAIL
    )
    html_message = render_to_string(
        'eol_course_email/email.txt', context)
    plain_message = strip_tags(html_message)
    for u in email.receiver_users.all():
        logger.warning("Sending email to {}".format(u.email))
        send_email.delay(from_email, email.sender_user.email, u.email, email.subject, html_message, plain_message)
