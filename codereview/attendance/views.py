import io
from datetime import datetime
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import Attendance, Employee, Shift
from .forms import (
    PunchForm,
    EmployeeImportForm,
    ShiftImportForm,
    ShiftForm,
    EmployeeForm,
    EmployeeDeleteForm,
)
from .services import (
    PunchService,
    EmployeeExcelImporter,
    ShiftExcelImporter,
    ExcelExporter,
)

# =========================
# 2-1) 打刻（トップページ）
# 対応テンプレ: templates/attendance/punch.html
# =========================
def punch(request):
    form = PunchForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        emp = form.cleaned_data["employee"]
        action = request.POST.get("action")
        note = ""  # 備考を使わないUIなら空でOK
        svc = PunchService(employee=emp, note=note)
        try:
            if action == "in":
                svc.punch_in()
                messages.success(request, f"{emp.name} さんの出勤を記録しました。")
            elif action == "out":
                svc.punch_out()
                messages.success(request, f"{emp.name} さんの退勤を記録しました。")
            else:
                messages.error(request, "不正な操作です。")
        except ValueError as e:
            messages.error(request, str(e))
        return redirect("punch_page")  # 打刻ページに戻る
    return render(request, "attendance/punch.html", {"form": form})


# =========================
# 勤怠一覧 / 検索
# 対応テンプレ: templates/attendance/attendance_list.html
#                 templates/attendance/attendance_search_results.html
# =========================
def attendance_list(request):
    qs = Attendance.objects.select_related("employee").order_by("work_date", "employee__code")
    return render(request, "attendance/attendance_list.html", {"attendances": qs})


def attendance_search(request):
    qs = Attendance.objects.select_related("employee")
    query = request.GET.get("q", "").strip()
    if query:
        qs = qs.filter(
            Q(employee__code__icontains=query)
            | Q(employee__name__icontains=query)
            | Q(note__icontains=query)
        )
    return render(
        request,
        "attendance/attendance_search_results.html",
        {"attendances": qs, "query": query},
    )


# =========================
# シフト一覧 / 登録
# 対応テンプレ: templates/attendance/shift_list.html
#                 templates/attendance/shift_form.html
# =========================
def shift_list(request):
    month = request.GET.get("month", "")
    emp_query = request.GET.get("emp", "").strip()

    if month:
        try:
            dt = datetime.strptime(month, "%Y-%m")
            year, mon = dt.year, dt.month
        except ValueError:
            today = timezone.localdate()
            year, mon = today.year, today.month
    else:
        today = timezone.localdate()
        year, mon = today.year, today.month

    qs = Shift.objects.select_related("employee").filter(date__year=year, date__month=mon)
    if emp_query:
        qs = qs.filter(
            Q(employee__code__icontains=emp_query) | Q(employee__name__icontains=emp_query)
        )
    qs = qs.order_by("date", "employee__code")

    return render(
        request,
        "attendance/shift_list.html",
        {
            "shifts": qs,
            "year": year,
            "month": mon,
            "ym": f"{year}-{mon:02d}",
            "month_value": f"{year}-{mon:02d}",
            "emp_query": emp_query,
        },
    )


def shift_create(request):
    form = ShiftForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            form.save()
            messages.success(request, "シフトを登録しました。")
            return redirect("shift_list")
        except Exception as e:
            messages.error(request, f"登録に失敗しました: {e}")
    return render(request, "attendance/shift_form.html", {"form": form})


# =========================
# 従業員登録 / 削除
# 対応テンプレ: templates/attendance/employee_register.html
#                 templates/attendance/employee_delete.html
# =========================
def employee_register(request):
    form = EmployeeForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "従業員を登録しました。")
        return redirect("employee_register")
    return render(request, "attendance/employee_register.html", {"form": form})


def employee_delete(request):
    """
    社員番号・名前・時給の3点一致で削除
    """
    form = EmployeeDeleteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        emp = form.cleaned_data["employee"]  # フォーム側で社員特定済み前提
        emp.is_active = False
        emp.save(update_fields=["is_active"])
        messages.success(request, f"{emp.code}（{emp.name}）を在籍OFFにしました。")
        return redirect("employee_delete")
    return render(request, "attendance/employee_delete.html", {"form": form})


# =========================
# インポート ハブ / ダウンロード ハブ
# 対応テンプレ: templates/attendance/import_hub.html
#                 templates/attendance/download_hub.html
# =========================
def import_hub(request):
    return render(
        request,
        "attendance/import_hub.html",
        {"emp_form": EmployeeImportForm(), "shift_form": ShiftImportForm()},
    )


def download_hub(request):
    return render(request, "attendance/download_hub.html")


# =========================
# 従業員インポート
# 対応テンプレ: templates/attendance/employee_import.html
# =========================
@transaction.atomic
def employee_import(request):
    form = EmployeeImportForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        importer = EmployeeExcelImporter(file_obj=form.cleaned_data["file"])
        result = importer.run()  # 想定: result.created / result.updated / result.errors
        if getattr(result, "errors", None):
            for e in result.errors:
                messages.error(request, e)
        messages.success(request, f"従業員: 追加 {result.created} 件 / 更新 {result.updated} 件")
        return redirect("import_hub")
    return render(request, "attendance/employee_import.html", {"form": form})


# =========================
# シフトインポート
# 対応テンプレ: templates/attendance/shift_import.html
# =========================
@transaction.atomic
def shift_import(request):
    form = ShiftImportForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        importer = ShiftExcelImporter(file_obj=form.cleaned_data["file"])
        result = importer.run()  # 想定: result.created / result.updated / result.errors
        if getattr(result, "errors", None):
            for e in result.errors:
                messages.error(request, e)
        messages.success(request, f"シフト: 追加 {result.created} 件 / 更新 {result.updated} 件")
        return redirect("import_hub")
    return render(request, "attendance/shift_import.html", {"form": form})


# =========================
# 2-4) Excelダウンロード（勤怠 / 従業員 / シフト）
# 対応テンプレ: templates/attendance/download_hub.html 
# =========================
def download_attendance(request):
    filename, data = ExcelExporter.attendance()
    resp = HttpResponse(
        data,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


def download_employees(request):
    filename, data = ExcelExporter.employees()
    resp = HttpResponse(
        data,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


def download_shifts(request):
    filename, data = ExcelExporter.shifts()
    resp = HttpResponse(
        data,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp
