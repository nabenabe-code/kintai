from django.urls import path
from . import views

urlpatterns = [
    # トップ（打刻）
    path("", views.punch, name="punch_page"),

    # 勤怠
    path("attendance/", views.attendance_list, name="attendance_list"),
    path("attendance/search/", views.attendance_search, name="attendance_search"),

    # シフト
    path("shifts/", views.shift_list, name="shift_list"),
    path("shifts/new/", views.shift_create, name="shift_create"),

    # 従業員（登録 / 削除）
    path("employees/register/", views.employee_register, name="employee_register"),
    path("employees/delete/", views.employee_delete, name="employee_delete"),

    # インポート（ハブ + 実処理）
    path("import/", views.import_hub, name="import_hub"),
    path("import/employees/", views.employee_import, name="employee_import"),
    path("import/shifts/", views.shift_import, name="shift_import"),

    # ダウンロード（ハブ + Excel出力）
    path("download/", views.download_hub, name="download_hub"),
    path("export/employees/", views.download_employees, name="employee_export"),
    path("export/shifts/", views.download_shifts, name="shift_export"),
    path("export/attendance/", views.download_attendance, name="attendance_export"),
]
