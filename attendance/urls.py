from django.urls import path
from . import views

urlpatterns = [
    # トップ
    path("", views.punch, name="punch_page"),
    path("health/", views.healthcheck, name="healthcheck"),

    # base.html が参照するURL名（全部そろえる）
    path("attendance/list/", views.attendance_list, name="attendance_list"),
    path("attendance/search/", views.attendance_search, name="attendance_search"),

    path("shift/", views.shift_list, name="shift_list"),
    path("shift/new/", views.shift_create, name="shift_create"),

    path("employee/new/", views.employee_register, name="employee_register"),
    path("employee/delete/", views.employee_delete, name="employee_delete"),

    path("import/", views.import_hub, name="import_hub"),
    path("import/employee/", views.employee_import, name="employee_import"),
    path("import/shift/", views.shift_import, name="shift_import"),

    path("download/", views.download_hub, name="download_hub"),
    path("download/employees.xlsx", views.download_employees, name="employee_export"),
    path("download/shifts.xlsx", views.download_shifts, name="shift_export"),
    path("download/attendance.xlsx", views.download_attendance, name="attendance_export"),
]
