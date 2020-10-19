# -*- coding: utf-8 -*-


from django.contrib import admin

from .models import EolCourseEmail, EolCourseEmailUserConfiguration

class EolCourseEmailSetupAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'course_id', 'sender_user', 'subject')


class EolCourseEmailUserConfigurationSetupAdmin(admin.ModelAdmin):
    list_display = ('course_id', 'user')


admin.site.register(EolCourseEmail, EolCourseEmailSetupAdmin)
admin.site.register(EolCourseEmailUserConfiguration, EolCourseEmailUserConfigurationSetupAdmin)