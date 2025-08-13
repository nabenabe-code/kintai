from django.urls import path
from .views import (
    PunchView,
    attendance_list, attendance_search, employee_register,
    shift_list, shift_create, shift_import,
    import_hub, employee_import,
    download_hub, employee_export_excel, shift_export_excel,
    attendance_export_excel,
)

urlpatterns = [
     # ルート：打刻画面（従業員選択 → 出勤/退勤ボタン）
    # View: PunchView（CBV）
    # Template: attendance/punch.html
    path('', PunchView.as_view(), name='punch_page'),

    # 勤怠一覧ページ
    # View: attendance_list
    # Template: attendance/attendance_list.html
    path('list/', attendance_list, name='attendance_list'),

    # 勤怠検索結果（?q= でコード/氏名/備考を部分一致検索）
    # View: attendance_search
    # Template: attendance/attendance_search_results.html
    path('search/', attendance_search, name='attendance_search'),

    # 従業員 登録／削除 ページ（1画面で登録と削除に対応）
    # View: employee_register
    # Template: attendance/employee_register.html
    path('employee/register/', employee_register, name='employee_register'),

    # シフト一覧（?month=YYYY-MM, ?emp= で絞り込み）
    # View: shift_list
    # Template: attendance/shift_list.html
    path('shift/', shift_list, name='shift_list'),

    # シフト単票登録
    # View: shift_create
    # Template: attendance/shift_form.html
    path('shift/new/', shift_create, name='shift_create'),

    # シフトExcel取込（個別URL）
    # View: shift_import
    # Template: attendance/shift_import.html
    path('shift/import/', shift_import, name='shift_import'),

    # インポート統合（従業員・シフトのアップロード入口）
    # View: import_hub
    # Template: attendance/import_hub.html
    path('import/', import_hub, name='import_hub'),

    # 従業員Excel取込（個別URL）
    # View: employee_import
    # Template: attendance/employee_import.html
    path('employee/import/', employee_import, name='employee_import'),

    # ダウンロード入口（従業員/シフト それぞれのDLリンクあり）
    # View: download_hub
    # Template: attendance/download_hub.html
    path('download/', download_hub, name='download_hub'),

    # 従業員一覧Excelダウンロード（テンプレートは使わず xlsx を返す）
    # View: employee_export_excel
    # Response: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    path('download/employees/', employee_export_excel, name='employee_export'),

    # シフト一覧Excelダウンロード（テンプレートは使わず xlsx を返す）
    # View: shift_export_excel
    # Response: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    path('download/shifts/', shift_export_excel, name='shift_export'),

    # 勤怠一覧Excelダウンロード（テンプレートは使わず xlsx を返す）
    # View: attendance_export_excel
    # Response: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    path('export/', attendance_export_excel, name='attendance_export'),
]
