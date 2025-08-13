from __future__ import annotations

from datetime import datetime, date, time, timedelta
from decimal import Decimal
from django.db import models


class Employee(models.Model):
    code = models.CharField("社員番号", max_length=20, unique=True)
    name = models.CharField("氏名", max_length=100)
    hourly_rate = models.DecimalField("時給", max_digits=7, decimal_places=2, default=0)
    is_active = models.BooleanField("在籍", default=True)
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} {self.name}"


class Shift(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="shifts", verbose_name="従業員")
    date = models.DateField("日付")
    start_time = models.TimeField("開始", null=True, blank=True)
    end_time = models.TimeField("終了", null=True, blank=True)
    note = models.CharField("備考", max_length=200, blank=True, default="")

    class Meta:
        ordering = ["date", "employee__code", "start_time"]

    def __str__(self) -> str:
        st = self.start_time.strftime("%H:%M") if self.start_time else "--:--"
        et = self.end_time.strftime("%H:%M") if self.end_time else "--:--"
        return f"{self.date} {self.employee} {st}-{et}"


class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendances", verbose_name="従業員")
    work_date = models.DateField("勤務日", db_index=True)
    time_in = models.TimeField("出勤", null=True, blank=True)
    time_out = models.TimeField("退勤", null=True, blank=True)
    note = models.CharField("備考", max_length=200, blank=True, default="")
    created_at = models.DateTimeField("作成日時", auto_now_add=True)
    updated_at = models.DateTimeField("更新日時", auto_now=True)

    class Meta:
        ordering = ["work_date", "employee__code"]
        indexes = [models.Index(fields=["work_date", "employee"])]

    def __str__(self) -> str:
        return f"{self.work_date} {self.employee}"

    @property
    def work_hours(self) -> float:
        """出退勤が両方ある場合の実働時間[時間]（小数）"""
        if self.time_in and self.time_out:
            d = datetime.combine(self.work_date, self.time_out) - datetime.combine(self.work_date, self.time_in)
            return round(d.total_seconds() / 3600, 2)
        return 0.0

    @property
    def wage_amount(self) -> Decimal:
        """概算支給額（実働×時給）"""
        try:
            return (Decimal(str(self.work_hours)) * (self.employee.hourly_rate or Decimal("0"))).quantize(Decimal("0.01"))
        except Exception:
            return Decimal("0.00")
