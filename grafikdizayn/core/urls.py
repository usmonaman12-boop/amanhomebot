from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("admin-panel/", views.admin_panel, name="admin_panel"),
    path("admin-panel/teacher/<int:user_id>/delete/", views.admin_delete_teacher, name="admin_delete_teacher"),
    path("admin-panel/recalculate/", views.admin_recalculate_all, name="admin_recalculate_all"),

    path("teacher/", views.teacher_panel, name="teacher_panel"),
    path("teacher/group/<int:group_id>/", views.group_detail, name="group_detail"),
    path("teacher/group/<int:group_id>/recalc/", views.group_recalculate, name="group_recalculate"),
    path("teacher/group/<int:group_id>/student/<int:student_id>/delete/", views.group_delete_student, name="group_delete_student"),
    path("teacher/group/<int:group_id>/link/", views.group_link_info, name="group_link_info"),
    path("teacher/group/<int:group_id>/day/", views.daily_session, name="daily_session"),

    path("student/", views.student_panel, name="student_panel"),

    path("telegram/webhook/<str:secret>/", views.telegram_webhook, name="telegram_webhook"),
]
