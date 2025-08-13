# services.py
from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Tuple

from django.utils import timezone
from openpyxl import load_workbook

from .models import Employee, Attendance, Shift


# ── 打刻ユースケース ─────────────────────────
@dataclass
class PunchService:
    employee: Employee

    def today(self) -> Attendance:
        d = timezone.localdate()
        att, _ = Attendance.objects.get_or_create(employee=self.employee, work_date=d)
        return att

    def clock_in(self, now: time) -> None:
        self.today().clock_in(now)

    def clock_out(self, now: time) -> None:
        self.today().clock_out(now)


# ── Excel 読み込みの小ヘルパ ───────────────
def _to_date(v) -> date | None:
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, str):
        for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(v.strip(), fmt).date()
            except ValueError:
                continue
    return None

def _to_time(v) -> time | None:
    if isinstance(v, time):
        return v
    if isinstance(v, datetime):
        return v.time()
    if isinstance(v, str):
        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(v.strip(), fmt).time()
            except ValueError:
                continue
    return None


# ── 従業員インポート ───────────────────────
class EmployeeImporter:
    REQUIRED = {'code', 'hourly_rate'}

    def run(self, file) -> Tuple[int, int, int]:
        wb = load_workbook(filename=file, data_only=True)
        ws = wb.active
        header = {str(c.value).strip(): i for i, c in enumerate(ws[1], 1) if c.value is not None}
        names = {k.lower(): i for k, i in header.items()}
        if not self.REQUIRED.issubset(names.keys()):
            raise ValueError('必須列 code / hourly_rate がありません。')

        created = updated = skipped = 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            raw_code = row[names['code'] - 1] if names.get('code') else None
            code = (str(raw_code).strip() if raw_code is not None else '')
            if not code:
                skipped += 1
                continue

            name = row[names['name'] - 1] if names.get('name') else ''
            hourly = row[names['hourly_rate'] - 1]
            try:
                hourly_val = float(hourly)
            except (TypeError, ValueError):
                skipped += 1
                continue

            emp, is_new = Employee.objects.get_or_create(code=code)
            if name:
                emp.name = str(name)
            emp.hourly_rate = hourly_val
            emp.is_active = True  # 取込時は在籍ONに戻す運用
            emp.save()
            created += int(is_new)
            updated += int(not is_new)

        return created, updated, skipped


# ── シフトインポート ───────────────────────
class ShiftImporter:
    REQUIRED = {'code', 'date', 'start', 'end'}

    def run(self, file) -> Tuple[int, int, int]:
        wb = load_workbook(filename=file, data_only=True)
        ws = wb.active
        header = {str(c.value).strip(): i for i, c in enumerate(ws[1], 1) if c.value is not None}
        names = {k.lower(): i for k, i in header.items()}
        if not self.REQUIRED.issubset(names.keys()):
            raise ValueError('必須列 code / date / start / end が見つかりません。')

        c_code = names['code']; c_date = names['date']; c_start = names['start']; c_end = names['end']
        c_note = names.get('note')

        created = updated = skipped = 0
        for row in ws.iter_rows(min_row=2, values_only=True):
            raw_code = row[c_code - 1]
            code = (str(raw_code).strip() if raw_code is not None else '')
            if not code:
                skipped += 1
                continue
            try:
                emp = Employee.objects.get(code=code)
            except Employee.DoesNotExist:
                skipped += 1
                continue

            d = _to_date(row[c_date - 1])
            st = _to_time(row[c_start - 1])
            ed = _to_time(row[c_end - 1])
            note = row[c_note - 1] if c_note else ''
            if not (d and st and ed):
                skipped += 1
                continue

            obj, is_new = Shift.objects.get_or_create(employee=emp, date=d)
            obj.start_time = st
            obj.end_time = ed
            obj.note = str(note or '')
            obj.save()
            created += int(is_new)
            updated += int(not is_new)

        return created, updated, skipped
