from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import datetime
from django.db import transaction
from django.db.models.deletion import ProtectedError

from .forms import (
    PunchForm, EmployeeForm, ShiftForm,
    BulkExcelUploadForm, ShiftSearchForm
)
from .models import Employee, Attendance, Shift
from .services import (
    PunchService, EmployeeExcelImporter, ShiftExcelImporter, ExcelExporter
)

# トップ画面: 打刻
def punch_view(request):
    if request.method == "POST":
        f = PunchForm(request.POST)
        if f.is_valid():
            action = "in" if "in" in request.POST else "out"
            try:
                messages.success(request, PunchService.punch_by_code(f.cleaned_data["employee_code"], action))
            except ValueError as e:
                messages.error(request, str(e))
            return redirect("attendance:punch")
    else:
        f = PunchForm()

    recent = Attendance.objects.select_related("employee").order_by("-work_date", "-clock_in")[:10]
    return render(request, "attendance/punch.html", {"form": f, "recent": recent, "today": timezone.localdate()})

# 従業員: 追加・一覧・削除
def employee_list_create_view(request):
    if request.method == "POST":
        f = EmployeeForm(request.POST)
        if f.is_valid():
            f.save()
            messages.success(request, "従業員を登録しました。")
            return redirect("attendance:employees")
    else:
        f = EmployeeForm()
    employees = Employee.objects.order_by("code")
    return render(request, "attendance/employees.html", {"form": f, "employees": employees})

@require_POST
def employee_delete_view(request, pk):
    emp = get_object_or_404(Employee, pk=pk)
    try:
        with transaction.atomic():
            Shift.objects.filter(employee=emp).delete()
            Attendance.objects.filter(employee=emp).delete()
            emp.delete()
        messages.success(request, "従業員と関連するシフト/打刻を削除しました。")
    except ProtectedError:
        messages.error(request, "関連データの保護により削除できませんでした。")
    except Exception as e:
        messages.error(request, f"削除できません: {e}")
    return redirect("attendance:employees")

# シフト: 追加・一覧・削除
def shifts_manage_view(request):
    if request.method == "POST":
        f = ShiftForm(request.POST)
        if f.is_valid():
            f.save()
            messages.success(request, "シフトを登録しました。")
            return redirect("attendance:shifts_manage")
    else:
        f = ShiftForm()
    shifts = Shift.objects.select_related("employee").order_by("-date", "start")[:200]
    return render(request, "attendance/shifts_manage.html", {"form": f, "shifts": shifts})

@require_POST
def shift_delete_view(request, pk):
    get_object_or_404(Shift, pk=pk).delete()
    messages.success(request, "シフトを削除しました。")
    return redirect("attendance:shifts_manage")

# Excel一括登録（従業員 & シフト）
def import_bulk_view(request):
    if request.method == "POST":
        f = BulkExcelUploadForm(request.POST, request.FILES)
        if f.is_valid():
            did_any = False
            if f.cleaned_data.get("employees_file"):
                try:
                    r = EmployeeExcelImporter(f.cleaned_data["employees_file"]).run()
                    messages.success(request, f"従業員: 追加 {r['created']} / 更新 {r['updated']}")
                except ValueError as e:
                    messages.error(request, f"従業員Excel: {e}")
                did_any = True
            if f.cleaned_data.get("shifts_file"):
                try:
                    r = ShiftExcelImporter(f.cleaned_data["shifts_file"]).run()
                    messages.success(request, f"シフト: 登録 {r['created']}")
                except ValueError as e:
                    messages.error(request, f"シフトExcel: {e}")
                did_any = True
            if not did_any:
                messages.warning(request, "ファイルが選択されていません。")
            return redirect("attendance:import_bulk")
    else:
        f = BulkExcelUploadForm()
    return render(request, "attendance/import_bulk.html", {"form": f})

# Excelエクスポート
def export_employees_view(request):
    df = ExcelExporter.employees_df()
    if df.empty:
        df = ExcelExporter.template_employees()
    return ExcelExporter.df_to_xlsx_response(df, "employees.xlsx")

def export_shifts_view(request):
    date = None
    if request.GET.get("date"):
        try:
            date = datetime.strptime(request.GET["date"], "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "日付の形式が不正です (YYYY-MM-DD)。")
    df = ExcelExporter.shifts_df(date=date)
    if df.empty:
        df = ExcelExporter.template_shifts()
    return ExcelExporter.df_to_xlsx_response(df, "shifts.xlsx")

# シフト検索
def shift_search_view(request):
    f = ShiftSearchForm(request.GET or None)
    qs = []
    if f.is_valid():
        qs = Shift.objects.select_related("employee").filter(date=f.cleaned_data["date"]).order_by("start")
    return render(request, "attendance/shifts.html", {"form": f, "shifts": qs})
