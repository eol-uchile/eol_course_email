# -*- coding: utf-8 -*-
import urllib.parse

from django.db import models

from django.contrib.auth.models import User
from opaque_keys.edx.django.models import CourseKeyField
from django.urls import reverse

class FilesCourseEmail(models.Model):
    """
        File Uploads
    """
    file_name = models.CharField(max_length=100)
    file_path = models.TextField()
    content_type = models.CharField(max_length=100)

class EolCourseEmail(models.Model):
    """
        Emails
    """
    course_id = CourseKeyField(max_length=255)
    sender_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sender_user")
    receiver_users = models.ManyToManyField(User)
    subject = models.CharField(max_length=50)
    message = models.TextField()
    files = models.ManyToManyField(FilesCourseEmail)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    @property
    def receiver_users_list(self):
        """
            Return list of users profile names
        """
        return [u.profile.name for u in self.receiver_users.all()]

    
    @property
    def files_list(self):
        """
            Return list of files
        """
        return [
            {
                'name': f.file_name,
                'url': reverse(
                    'eol/course_email:get_file_url', 
                    kwargs={
                        'content_type': urllib.parse.quote(f.content_type.encode('utf-8'), safe=''),
                        'course_id': f.file_path.split("/")[0], 
                        'file': f.file_path.split("/")[1]
                    }
                )
            }
            for f in self.files.all()
        ]
