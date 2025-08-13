from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from django.db import models
from django.utils import timezone


# =========================================
# 従業員
# =========================================
class Employee(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    hourly_rate = models.PositiveIntegerField("時給(円)", null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} {self.name}"

    @property
    def label(self) -> str:
        """プルダウン等で使いやすい表示"""
        return f"{self.code} - {self.name}"


# =========================================
# 出退勤（打刻）
#   - 1日1回
# =========================================
class Attendance(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.PROTECT, related_name="attendances"
    )
    work_date = models.DateField()
    clock_in = models.DateTimeField(null=True, blank=True)
    clock_out = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "work_date"], name="uniq_employee_date"
            )
        ]
        indexes = [models.Index(fields=["work_date"])]
        ordering = ["-work_date", "employee__code"]

    def __str__(self) -> str:
        return f"{self.work_date} {self.employee}"

    @property
    def is_open(self) -> bool:
        return bool(self.clock_in and not self.clock_out)

    def duration_minutes(self) -> Optional[int]:#未打刻があればnone
        if not (self.clock_in and self.clock_out):
            return None
        try:
            mins = int((self.clock_out - self.clock_in).total_seconds() // 60)
            return max(mins, 0)
        except Exception:
            return None

    def duration_hhmm(self) -> str:
        m = self.duration_minutes()
        if m is None:
            return "-"
        h, mm = divmod(m, 60)
        return f"{h}:{mm:02d}"


# =========================================
# シフト
#   - date + start/end（Time）/ break_minutes（分）
#   - 跨日勤務に対応（end <= start の場合は翌日扱い）
# =========================================
class Shift(models.Model):
    employee = models.ForeignKey(
        Employee, on_delete=models.PROTECT, related_name="shifts"
    )
    date = models.DateField()
    start = models.TimeField()
    end = models.TimeField()
    break_minutes = models.PositiveSmallIntegerField(default=0)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        indexes = [models.Index(fields=["date"])]
        ordering = ["date", "start"]

    def __str__(self) -> str:
        return f"{self.date} {self.employee} {self.start}-{self.end}"

    # ---------- 内部ユーティリティ ----------
    def _start_dt(self) -> datetime:
        return datetime.combine(self.date, self.start)

    def _end_dt(self) -> datetime:
        end_dt = datetime.combine(self.date, self.end)
        # 跨日（終業が開始時刻以前）を翌日にシフト
        if end_dt <= self._start_dt():
            end_dt += timedelta(days=1)
        return end_dt

    # ---------- 公開API ----------
    def total_work_minutes(self) -> int:
        start_dt = self._start_dt()
        end_dt = self._end_dt()
        gross = int((end_dt - start_dt).total_seconds() // 60)  # 総分
        brk = int(self.break_minutes or 0)
        return max(gross - brk, 0)

    @property
    def total_work_hhmm(self) -> str:
        m = self.total_work_minutes()
        h, mm = divmod(m, 60)
        return f"{h}:{mm:02d}"

    @property
    def estimated_pay(self) -> Optional[int]:
        rate = self.employee.hourly_rate
        if rate is None:
            return None
        per_min = rate / 60.0
        return int(round(per_min * self.total_work_minutes()))
