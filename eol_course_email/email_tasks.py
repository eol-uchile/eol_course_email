# -*- coding: utf-8 -*-

from celery import task
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from .upload import get_storage
import json

import logging
logger = logging.getLogger(__name__)

EMAIL_DEFAULT_RETRY_DELAY = 30
EMAIL_MAX_RETRIES = 5

@task(
    queue='edx.lms.core.low',
    default_retry_delay=EMAIL_DEFAULT_RETRY_DELAY,
    max_retries=EMAIL_MAX_RETRIES)
def send_email(from_email, reply_to, to_email, subject, html_message, plain_message, files):
    """
        Send mail to specific user
            from_email: default noreply@mail
            reply_to: sender user
            to_email: receiver user
    """
    email = EmailMultiAlternatives(
        subject,
        plain_message,
        from_email,
        [to_email],
        reply_to=[reply_to])
    email.attach_alternative(html_message, "text/html")
    for f in json.loads(files):
        file = get_storage().open(f['file_path'])
        email.attach(f['file_name'], file.read(), f['content_type'])
    return email.send(fail_silently=False)