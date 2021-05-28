import os
import six
import hashlib
from functools import partial
from django.conf import settings
from django.core.files.storage import get_storage_class
from django.core.files import File
from .models import FilesCourseEmail

import logging
logger = logging.getLogger(__name__)

FILEUPLOAD_MAX_SIZE = 10 * 1000 * 1000  # 10 MB
BLOCK_SIZE = 2**10 * 8  # 8kb

def upload_file(course_id, file):
    """
        Upload files to storage and create model.
        Return error flag and files uploaded.
    """
    if not file:
        return {
            'error'   : False,
            'file'    : None
        }
    sha1 = get_sha1(file)
    if file_size_over_limit(file):
        logger.warning("File over upload limit")
        return {
            'error'   : True,
            'file'   : None
        }
    path = get_file_storage_path(course_id, sha1, file.name)
    storage = get_storage()
    storage.save(path, File(file))
    file_upload = FilesCourseEmail(
        file_name=file.name,
        file_path=path,
        content_type=file.content_type
    )
    file_upload.save()
    return {
        'error'   : False,
        'file'    : file_upload
    }

def get_sha1(file_descriptor):
    """
    Get file hex digest (fingerprint).
    """
    sha1 = hashlib.sha1()
    for block in iter(partial(file_descriptor.read, BLOCK_SIZE), b''):
        sha1.update(block)
    file_descriptor.seek(0)
    return sha1.hexdigest()

def upload_max_size():
    """
    returns max file size limit in system
    """
    return getattr(
        settings,
        "COURSE_EMAIL_FILEUPLOAD_MAX_SIZE",
        FILEUPLOAD_MAX_SIZE
    )

def file_size_over_limit(file_obj):
    """
    checks if file size is under limit.
    """
    file_obj.seek(0, os.SEEK_END)
    return file_obj.tell() > upload_max_size()

def get_file_storage_path(course_id, file_hash, original_filename):
    """
    Returns the file path for an uploaded PDF file
    """
    return (
        six.u(
            '{course_id}/{file_hash}{ext}'
        ).format(
            course_id=course_id,
            file_hash=file_hash,
            ext=os.path.splitext(original_filename)[1]
        )
    )

def get_storage():
    """
    Get the default storage
    """
    return get_storage_class(settings.COURSE_EMAIL_STORAGE_CLASS['class'])(**settings.COURSE_EMAIL_STORAGE_CLASS['options'])