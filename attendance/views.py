import io
from datetime import datetime
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View
from openpyxl import Workbook

from .models import Attendance, Employee, Shift
from .forms import (
    EmployeeForm, EmployeeDeleteForm,
    EmployeeImportForm, PunchForm, ShiftForm, ShiftImportForm,
)
from .services import PunchService, EmployeeImporter, ShiftImporter


class PunchView(View):
    template_name = 'attendance/punch.html'
    def get(self, request):
        return render(request, self.template_name, {'form': PunchForm()})
    @transaction.atomic
    def post(self, request):
        form = PunchForm(request.POST)
        if not form.is_valid():
            messages.error(request, '入力に誤りがあります。')
            return render(request, self.template_name, {'form': form})
        employee = form.cleaned_data['employee']
        action = request.POST.get('action')
        now_time = timezone.localtime().time()
        svc = PunchService(employee)
        try:
            if action == 'in':
                svc.clock_in(now_time)
                messages.success(request, f'{employee.name} を出勤打刻しました。（{now_time}）')
            elif action == 'out':
                svc.clock_out(now_time)
                messages.success(request, f'{employee.name} を退勤打刻しました。（{now_time}）')
            else:
                messages.error(request, '不明な操作です。')
        except ValueError as e:
            messages.warning(request, str(e))
        return redirect('punch_page')


def attendance_list(request):
    qs = Attendance.objects.select_related('employee').order_by('work_date', 'employee__code')
    return render(request, 'attendance/attendance_list.html', {'attendances': qs})


def attendance_search(request):
    qs = Attendance.objects.select_related('employee')
    query = request.GET.get('q', '').strip()
    if query:
        qs = qs.filter(
            Q(employee__code__icontains=query) |
            Q(employee__name__icontains=query) |
            Q(note__icontains=query)
        )
    return render(request, 'attendance/attendance_search_results.html',
                  {'attendances': qs, 'query': query})


def employee_register(request):
    """
    従業員の「登録」と「削除」を1画面で提供。
    - 登録: EmployeeForm（ボタン name='add-submit'）
    - 削除: EmployeeDeleteForm（ボタン name='del-submit'）
    削除は code+name+hourly_rate が一致する在籍者だけ在籍OFFにする（論理削除）。
    """
    form_add = EmployeeForm(request.POST or None, prefix='add')
    form_del = EmployeeDeleteForm(request.POST or None, prefix='del')

    if request.method == 'POST':
        # 追加
        if 'add-submit' in request.POST and form_add.is_valid():
            form_add.save()
            messages.success(request, '従業員を登録しました。')
            return redirect('employee_register')

        # 削除
        if 'del-submit' in request.POST and form_del.is_valid():
            emp = form_del.cleaned_data['employee']  # forms.clean() で解決済み
            emp.is_active = False
            emp.save(update_fields=['is_active'])
            messages.success(request, f'{emp.code}（{emp.name}）を在籍OFFにしました。')
            return redirect('employee_register')

    return render(request, 'attendance/employee_register.html', {
        'form': form_add,
        'delete_form': form_del,
    })

def employee_delete(request):
    form = EmployeeDeleteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        emp = form.cleaned_data['employee']  # forms.clean() で解決済み
        emp.is_active = False
        emp.save(update_fields=['is_active'])
        messages.success(request, f'{emp.code}（{emp.name}）を在籍OFFにしました。')
        return redirect('employee_delete')

    return render(request, 'attendance/employee_delete.html', {'form': form})


def shift_list(request):
    month = request.GET.get('month', '')
    emp_query = request.GET.get('emp', '').strip()
    if month:
        try:
            dt = datetime.strptime(month, "%Y-%m")
            year, mon = dt.year, dt.month
        except ValueError:
            today = timezone.localdate(); year, mon = today.year, today.month
    else:
        today = timezone.localdate(); year, mon = today.year, today.month
    qs = Shift.objects.select_related('employee').filter(date__year=year, date__month=mon)
    if emp_query:
        qs = qs.filter(Q(employee__code__icontains=emp_query) | Q(employee__name__icontains=emp_query))
    qs = qs.order_by('date', 'employee__code')
    return render(request, 'attendance/shift_list.html', {
        'shifts': qs, 'year': year, 'month': mon,
        'ym': f"{year}-{mon:02d}", 'month_value': f"{year}-{mon:02d}",
        'emp_query': emp_query,
    })


def shift_create(request):
    form = ShiftForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            form.save(); messages.success(request, 'シフトを登録しました。')
            return redirect('shift_list')
        except Exception as e:
            messages.error(request, f'登録に失敗しました: {e}')
    return render(request, 'attendance/shift_form.html', {'form': form})


@transaction.atomic
def shift_import(request):
    if request.method == 'POST':
        form = ShiftImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                c,u,s = ShiftImporter().run(form.cleaned_data['file'])
                messages.success(request, f'シフト 追加 {c} / 更新 {u} / スキップ {s}')
            except Exception as e:
                messages.error(request, f'取込に失敗しました: {e}')
        return redirect('import_hub')
    return render(request, 'attendance/shift_import.html', {'form': ShiftImportForm()})


def import_hub(request):
    return render(request, 'attendance/import_hub.html', {
        'emp_form': EmployeeImportForm(), 'shift_form': ShiftImportForm(),
    })


@transaction.atomic
def employee_import(request):
    if request.method == 'POST':
        form = EmployeeImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                c,u,s = EmployeeImporter().run(form.cleaned_data['file'])
                messages.success(request, f'従業員 追加 {c} / 更新 {u} / スキップ {s}')
            except Exception as e:
                messages.error(request, f'取込に失敗しました: {e}')
        return redirect('import_hub')
    return render(request, 'attendance/employee_import.html', {'form': EmployeeImportForm()})


def download_hub(request):
    return render(request, 'attendance/download_hub.html')


def _autosize(ws):
    for col_cells in ws.columns:
        max_len = 0
        for c in col_cells:
            v = c.value; l = len(str(v)) if v is not None else 0
            if l > max_len: max_len = l
        ws.column_dimensions[col_cells[0].column_letter].width = max(12, max_len + 2)


def attendance_export_excel(request):
    qs = Attendance.objects.select_related('employee').order_by('work_date', 'employee__code')
    wb = Workbook(); ws = wb.active; ws.title = '勤怠一覧'
    ws.append(['勤務日','社員番号','氏名','出勤','退勤','勤務時間[h]','時給','支給額','備考'])
    for a in qs:
        ws.append([
            a.work_date.strftime('%Y/%m/%d'),
            a.employee.code, a.employee.name,
            a.time_in.strftime('%H:%M') if a.time_in else '',
            a.time_out.strftime('%H:%M') if a.time_out else '',
            a.work_hours, float(a.employee.hourly_rate), a.wage_amount, a.note,
        ])
    _autosize(ws)
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    resp = HttpResponse(buf.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = f'attachment; filename="attendance_{datetime.now():%Y%m%d_%H%M%S}.xlsx"'
    return resp


def employee_export_excel(request):
    qs = Employee.objects.filter(is_active=True).order_by('code')
    wb = Workbook(); ws = wb.active; ws.title = '従業員'
    ws.append(['社員番号','氏名','時給'])
    for e in qs:
        ws.append([e.code, e.name, float(e.hourly_rate)])
    _autosize(ws)
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    resp = HttpResponse(buf.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = f'attachment; filename="employees_{datetime.now():%Y%m%d_%H%M%S}.xlsx"'
    return resp


def shift_export_excel(request):
    qs = Shift.objects.select_related('employee').order_by('date', 'employee__code')
    wb = Workbook(); ws = wb.active; ws.title = 'シフト'
    ws.append(['日付','社員番号','氏名','開始','終了','備考'])
    for s in qs:
        ws.append([
            s.date.strftime('%Y/%m/%d'),
            s.employee.code, s.employee.name,
            s.start_time.strftime('%H:%M') if s.start_time else '',
            s.end_time.strftime('%H:%M') if s.end_time else '',
            s.note,
        ])
    _autosize(ws)
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    resp = HttpResponse(buf.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = f'attachment; filename="shifts_{datetime.now():%Y%m%d_%H%M%S}.xlsx"'
    return resp
