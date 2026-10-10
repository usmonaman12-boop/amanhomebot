from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import DailyRecord, Group, StudentProfile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Qo'shimcha", {"fields": ("role", "phone")}),
    )
    list_display = ("username", "first_name", "last_name", "role", "is_staff")
    list_filter = ("role",)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "teacher", "student_count", "telegram_chat_id", "telegram_link_code")


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "group", "total_score", "missed_homework_count")
    list_filter = ("group",)


@admin.register(DailyRecord)
class DailyRecordAdmin(admin.ModelAdmin):
    list_display = ("student", "group", "date", "attendance_status", "homework_status", "day_total", "finalized")
    list_filter = ("group", "date", "attendance_status", "homework_status")
