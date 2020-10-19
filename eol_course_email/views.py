# -*- coding: utf-8 -*-


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
    user = request.user
    emails = EolCourseEmail.objects.filter(
        course_id=course_id,
        receiver_users__in=[user],
        deleted_at__isnull=True
    ).values(
        'subject',
        'message',
        'sender_user__profile__name',
        'created_at'
    ).order_by('created_at')
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
    ).order_by('created_at')
    sended_emails = [
        {
            'receiver_users_list' : e.receiver_users_list,
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
        Get all users enrolled in the course (except user logged)
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
    ).exclude(id=user.id)
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