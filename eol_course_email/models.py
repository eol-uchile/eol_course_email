# -*- coding: utf-8 -*-


from django.db import models

from django.contrib.auth.models import User
from opaque_keys.edx.django.models import CourseKeyField


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
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    @property
    def receiver_users_list(self):
        """
            Return list of users profile names
        """
        return [u.profile.name for u in self.receiver_users.all()]
