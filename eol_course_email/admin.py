# -*- coding: utf-8 -*-


from django.contrib import admin

from .models import EolCourseEmail, FilesCourseEmail

class EolCourseEmailSetupAdmin(admin.ModelAdmin):
    raw_id_fields = ('sender_user', 'receiver_users')
    list_display = ('created_at', 'course_id', 'sender_user', 'subject')

class FilesCourseEmailSetupAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'file_path')


admin.site.register(EolCourseEmail, EolCourseEmailSetupAdmin)
admin.site.register(FilesCourseEmail, FilesCourseEmailSetupAdmin)