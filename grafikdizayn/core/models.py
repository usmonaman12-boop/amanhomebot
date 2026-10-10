import secrets

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_ADMIN = "admin"
    ROLE_TEACHER = "teacher"
    ROLE_STUDENT = "student"
    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_TEACHER, "O'qituvchi"),
        (ROLE_STUDENT, "O'quvchi"),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    phone = models.CharField(max_length=20, blank=True)

    def is_admin_role(self):
        return self.role == self.ROLE_ADMIN

    def is_teacher_role(self):
        return self.role == self.ROLE_TEACHER

    def is_student_role(self):
        return self.role == self.ROLE_STUDENT

    def __str__(self):
        return self.get_full_name() or self.username


def generate_link_code():
    return secrets.token_hex(4).upper()


class Group(models.Model):
    name = models.CharField(max_length=150)
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="taught_groups",
        limit_choices_to={"role": User.ROLE_TEACHER},
    )
    telegram_chat_id = models.CharField(max_length=64, blank=True, null=True)
    telegram_link_code = models.CharField(
        max_length=16, unique=True, default=generate_link_code
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def student_count(self):
        return self.students.count()


class StudentProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="student_profile",
        limit_choices_to={"role": User.ROLE_STUDENT},
    )
    group = models.ForeignKey(
        Group, on_delete=models.SET_NULL, null=True, blank=True, related_name="students"
    )
    total_score = models.IntegerField(default=0)
    missed_homework_count = models.IntegerField(default=0)
    father_phone = models.CharField(max_length=20, blank=True)
    mother_phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return str(self.user)


class DailyRecord(models.Model):
    ATTEND_BOR = "bor"
    ATTEND_YUQ = "yuq"
    ATTEND_CHOICES = [(ATTEND_BOR, "Bor"), (ATTEND_YUQ, "Yo'q")]

    HW_BOR = "bor"
    HW_YUQ = "yuq"
    HW_CHALA = "chala"
    HW_CHOICES = [
        (HW_BOR, "Bor (bajargan)"),
        (HW_YUQ, "Yo'q (bajarmagan)"),
        (HW_CHALA, "Chala"),
    ]

    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="daily_records",
        limit_choices_to={"role": User.ROLE_STUDENT},
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="daily_records")
    teacher = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="given_records"
    )
    date = models.DateField()

    attendance_status = models.CharField(max_length=5, choices=ATTEND_CHOICES, blank=True)
    attendance_points = models.IntegerField(default=0)

    homework_status = models.CharField(max_length=6, choices=HW_CHOICES, blank=True)
    homework_points = models.IntegerField(default=0)
    # "Chala" bo'lganda o'qituvchi kiritgan foiz (100% = 8 ball). Eski yozuvlarda bo'sh.
    homework_percent = models.PositiveSmallIntegerField(null=True, blank=True)

    extra_points = models.IntegerField(default=0)
    note = models.CharField(max_length=255, blank=True)

    finalized = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("student", "date")
        ordering = ["-date"]

    @property
    def day_total(self):
        return self.attendance_points + self.homework_points + self.extra_points

    def __str__(self):
        return f"{self.student} - {self.date}"
