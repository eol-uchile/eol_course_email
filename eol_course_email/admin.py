# -*- coding: utf-8 -*-


from django.contrib import admin

from .models import EolCourseEmail

class EolCourseEmailSetupAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'course_id', 'sender_user', 'subject')




admin.site.register(EolCourseEmail, EolCourseEmailSetupAdmin)