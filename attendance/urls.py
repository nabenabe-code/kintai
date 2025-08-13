from django.urls import path
from . import views

app_name = "attendance"

urlpatterns = [
    path("", views.punch_view, name="punch"),  
    path("employees/", views.employee_list_create_view, name="employees"),
    path("employees/<int:pk>/delete/", views.employee_delete_view, name="employee_delete"),
    path("shifts/", views.shifts_manage_view, name="shifts_manage"),
    path("shifts/<int:pk>/delete/", views.shift_delete_view, name="shift_delete"),
    path("shifts/search/", views.shift_search_view, name="shift_search"),
    path("import/bulk/", views.import_bulk_view, name="import_bulk"),
    path("export/employees.xlsx", views.export_employees_view, name="export_employees"),
    path("export/shifts.xlsx", views.export_shifts_view, name="export_shifts"),
]
