import re
import json
from datetime import date

from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from .forms import GroupCreateForm, LoginForm, StudentCreateForm, TeacherCreateForm
from .models import DailyRecord, Group, StudentProfile, User
from .telegram import send_telegram_message


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        auth_login(request, form.get_user())
        return redirect("dashboard")
    return render(request, "core/login.html", {"form": form})


@login_required
def logout_view(request):
    auth_logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    if request.user.is_admin_role():
        return redirect("admin_panel")
    if request.user.is_teacher_role():
        return redirect("teacher_panel")
    return redirect("student_panel")


def is_admin(user):
    return user.is_authenticated and user.is_admin_role()


def is_teacher(user):
    return user.is_authenticated and user.is_teacher_role()


def is_student(user):
    return user.is_authenticated and user.is_student_role()


# ---------------- ADMIN ----------------

@user_passes_test(is_admin, login_url="login")
def admin_panel(request):
    if request.method == "POST":
        form = TeacherCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "O'qituvchi qo'shildi.")
            return redirect("admin_panel")
    else:
        form = TeacherCreateForm()
    teachers = User.objects.filter(role=User.ROLE_TEACHER).order_by("-id")
    return render(request, "core/admin_panel.html", {"form": form, "teachers": teachers})


@user_passes_test(is_admin, login_url="login")
def admin_delete_teacher(request, user_id):
    teacher = get_object_or_404(User, id=user_id, role=User.ROLE_TEACHER)
    teacher.delete()
    messages.success(request, "O'qituvchi o'chirildi.")
    return redirect("admin_panel")


def _recalculate_students(students_qs):
    """Recompute total_score / missed_homework_count for a queryset of
    StudentProfile objects from their finalized DailyRecord history.
    Fixes any drift (e.g. records edited directly via /django-admin/)."""
    count = 0
    for sp in students_qs:
        records = DailyRecord.objects.filter(student=sp.user, finalized=True)
        total = 0
        missed = 0
        for r in records:
            total += r.day_total
            if r.homework_status == DailyRecord.HW_YUQ:
                missed += 1
        sp.total_score = total
        sp.missed_homework_count = missed
        sp.save(update_fields=["total_score", "missed_homework_count"])
        count += 1
    return count


@user_passes_test(is_admin, login_url="login")
def admin_recalculate_all(request):
    if request.method == "POST":
        n = _recalculate_students(StudentProfile.objects.all())
        messages.success(request, f"Barcha o'quvchilar balli yangilandi ({n} ta).")
    return redirect("admin_panel")


# ---------------- TEACHER ----------------

@user_passes_test(is_teacher, login_url="login")
def teacher_panel(request):
    if request.method == "POST" and "save_phone" in request.POST:
        request.user.phone = request.POST.get("phone", "").strip()[:20]
        request.user.save(update_fields=["phone"])
        messages.success(request, "Telefon raqamingiz saqlandi.")
        return redirect("teacher_panel")
    if request.method == "POST":
        form = GroupCreateForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.teacher = request.user
            group.save()
            messages.success(request, "Guruh yaratildi.")
            return redirect("teacher_panel")
    else:
        form = GroupCreateForm()
    groups = Group.objects.filter(teacher=request.user).order_by("-created_at")
    return render(request, "core/teacher_panel.html", {"form": form, "groups": groups})


@user_passes_test(is_teacher, login_url="login")
def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id, teacher=request.user)

    if request.method == "POST":
        form = StudentCreateForm(request.POST)
        if form.is_valid():
            student = form.save()
            StudentProfile.objects.create(
                user=student, group=group,
                father_phone=form.cleaned_data.get("father_phone", "").strip(),
                mother_phone=form.cleaned_data.get("mother_phone", "").strip(),
            )
            messages.success(request, "O'quvchi qo'shildi.")
            return redirect("group_detail", group_id=group.id)
    else:
        form = StudentCreateForm()

    students = StudentProfile.objects.filter(group=group).select_related("user")
    return render(
        request, "core/group_detail.html",
        {"group": group, "students": students, "form": form},
    )


@user_passes_test(is_teacher, login_url="login")
def group_recalculate(request, group_id):
    group = get_object_or_404(Group, id=group_id, teacher=request.user)
    if request.method == "POST":
        n = _recalculate_students(StudentProfile.objects.filter(group=group))
        messages.success(request, f"\"{group.name}\" guruhidagi ballar yangilandi ({n} ta o'quvchi).")
    return redirect("group_detail", group_id=group.id)


@user_passes_test(is_teacher, login_url="login")
def group_delete_student(request, group_id, student_id):
    group = get_object_or_404(Group, id=group_id, teacher=request.user)
    sp = get_object_or_404(StudentProfile, id=student_id, group=group)
    if request.method == "POST":
        name = sp.user.get_full_name() or sp.user.username
        sp.user.delete()  # cascades: StudentProfile + DailyRecord ham o'chadi
        messages.success(request, f"\"{name}\" o'quvchi ro'yxatdan o'chirildi.")
    return redirect("group_detail", group_id=group.id)


@user_passes_test(is_teacher, login_url="login")
def group_link_info(request, group_id):
    group = get_object_or_404(Group, id=group_id, teacher=request.user)
    return render(request, "core/group_link_info.html", {"group": group})


@user_passes_test(is_teacher, login_url="login")
def daily_session(request, group_id):
    group = get_object_or_404(Group, id=group_id, teacher=request.user)
    today = date.today()
    students = StudentProfile.objects.filter(group=group).select_related("user")

    records = {}
    for sp in students:
        rec, _ = DailyRecord.objects.get_or_create(
            student=sp.user, date=today,
            defaults={"group": group, "teacher": request.user},
        )
        records[sp.user.id] = rec

    if request.method == "POST":
        summary_lines = []
        for sp in students:
            rec = records[sp.user.id]
            old_total = rec.day_total

            attendance = request.POST.get(f"attendance_{sp.user.id}", "")
            homework = request.POST.get(f"homework_{sp.user.id}", "")
            extra_raw = request.POST.get(f"extra_{sp.user.id}", "0").strip()
            try:
                extra = int(extra_raw) if extra_raw else 0
            except ValueError:
                extra = 0

            was_hw_missing_before = rec.homework_status == DailyRecord.HW_YUQ

            chala_raw = request.POST.get(f"chala_{sp.user.id}", "").strip()
            try:
                chala_points = max(0, int(chala_raw)) if chala_raw else None
            except ValueError:
                chala_points = None

            attendance_points = 3 if attendance == DailyRecord.ATTEND_BOR else 0
            if homework == DailyRecord.HW_BOR:
                homework_points = 5
            elif homework == DailyRecord.HW_CHALA:
                if chala_points is not None:
                    homework_points = chala_points  # domla o'zi kiritgan ball
                else:
                    homework_points = 3  # ball kiritilmasa eski qoida (3 ball)
            elif homework == DailyRecord.HW_YUQ:
                homework_points = 0
            else:
                homework_points = 0

            rec.group = group
            rec.teacher = request.user
            rec.attendance_status = attendance
            rec.attendance_points = attendance_points
            rec.homework_status = homework
            rec.homework_points = homework_points
            rec.homework_percent = None  # endi foiz ishlatilmaydi (eski yozuvlarda saqlanib qoladi)
            rec.extra_points = extra
            rec.finalized = True
            rec.save()

            # Adjust missed-homework counter
            is_hw_missing_now = homework == DailyRecord.HW_YUQ
            if is_hw_missing_now and not was_hw_missing_before:
                sp.missed_homework_count += 1
            elif not is_hw_missing_now and was_hw_missing_before:
                sp.missed_homework_count = max(0, sp.missed_homework_count - 1)

            new_total = rec.day_total
            sp.total_score += (new_total - old_total)
            sp.save()

            summary_lines.append(
                f"{sp.user.get_full_name() or sp.user.username}: bugun +{new_total} ball "
                f"(davomat: {attendance or '-'}, uy vazifasi: {homework or '-'}, qo'shimcha: {extra}) "
                f"| Umumiy: {sp.total_score}"
            )

        if group.telegram_chat_id:
            header = f"\U0001F4CB {group.name} guruhi \u2014 {today.strftime('%d.%m.%Y')} natijalari:\n\n"
            body = "\n".join(summary_lines)
            send_telegram_message(group.telegram_chat_id, header + body)

        messages.success(request, "Kunlik baholar saqlandi va yuborildi.")
        return redirect("daily_session", group_id=group.id)

    rows = [(sp, records[sp.user.id]) for sp in students]
    return render(
        request, "core/daily_session.html",
        {"group": group, "rows": rows, "today": today},
    )


# ---------------- STUDENT ----------------

@user_passes_test(is_student, login_url="login")
def student_panel(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    records = DailyRecord.objects.filter(student=request.user, finalized=True).order_by("-date")[:60]
    teacher = profile.group.teacher if profile.group_id else None
    teacher_phone = (teacher.phone or "").strip() if teacher else ""
    teacher_tel = re.sub(r"[^\d+]", "", teacher_phone)
    return render(
        request, "core/student_panel.html",
        {"profile": profile, "records": records, "teacher": teacher,
         "teacher_phone": teacher_phone, "teacher_tel": teacher_tel},
    )


# ---------------- TELEGRAM WEBHOOK ----------------

@csrf_exempt
def telegram_webhook(request, secret):
    if secret != getattr(settings, "TELEGRAM_WEBHOOK_SECRET", ""):
        return HttpResponse(status=404)
    if request.method != "POST":
        return HttpResponse(status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"ok": False})

    message = data.get("message") or {}
    text = (message.get("text") or "").strip()
    chat = message.get("chat") or {}
    chat_id = chat.get("id")

    if text.startswith("/link") and chat_id:
        parts = text.split()
        if len(parts) == 2:
            code = parts[1].strip().upper()
            try:
                group = Group.objects.get(telegram_link_code=code)
            except Group.DoesNotExist:
                send_telegram_message(chat_id, "Kod topilmadi. Kodni tekshiring.")
                return JsonResponse({"ok": True})
            group.telegram_chat_id = str(chat_id)
            group.save(update_fields=["telegram_chat_id"])
            send_telegram_message(
                chat_id,
                f"\u2705 Bu guruh endi \"{group.name}\" bilan bog'landi. Endi baholar shu yerga yuboriladi.",
            )
        else:
            send_telegram_message(chat_id, "Foydalanish: /link KOD")

    return JsonResponse({"ok": True})
