from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db import models
from django.utils import timezone


class Employee(models.Model):
    code = models.CharField('社員番号', max_length=20, unique=True)
    name = models.CharField('氏名', max_length=100, blank=True, default='')
    hourly_rate = models.DecimalField('時給', max_digits=8, decimal_places=2, default=0)
    is_active = models.BooleanField(
        '在籍', default=True,
        help_text='退職や一時停止時にOFF（論理削除）。'
    )

    class Meta:
        ordering = ['code']

    def __str__(self) -> str:
        return f'{self.code} {self.name}'.strip()


class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    work_date = models.DateField('勤務日', default=timezone.localdate)
    time_in = models.TimeField('出勤', null=True, blank=True)
    time_out = models.TimeField('退勤', null=True, blank=True)
    note = models.CharField('備考', max_length=200, blank=True, default='')

    class Meta:
        unique_together = [('employee', 'work_date')]
        ordering = ['-work_date', 'employee__code']

    def __str__(self) -> str:
        return f'{self.work_date} {self.employee}'

    # ── ドメインロジック ──────────────────────────────
    def clock_in(self, t: time) -> None:
        if self.time_in:
            raise ValueError('既に出勤打刻済みです。')
        self.time_in = t
        self.save(update_fields=['time_in'])

    def clock_out(self, t: time) -> None:
        if not self.time_in:
            raise ValueError('出勤打刻がありません。')
        if self.time_out:
            raise ValueError('既に退勤打刻済みです。')
        self.time_out = t
        self.save(update_fields=['time_out'])

    @property
    def work_seconds(self) -> int:
        if not (self.time_in and self.time_out):
            return 0
        dt_in = datetime.combine(self.work_date, self.time_in)
        dt_out = datetime.combine(self.work_date, self.time_out)
        if dt_out < dt_in:
            dt_out += timedelta(days=1)
        return int((dt_out - dt_in).total_seconds())

    @property
    def work_hours(self) -> float:
        """勤務時間（h, 小数）。表示・Excel用。"""
        return round(self.work_seconds / 3600.0, 2)

    @property
    def wage_amount(self) -> int:
        rate = Decimal(self.employee.hourly_rate or 0)
        return int(rate * Decimal(self.work_hours))


class Shift(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField('日付')
    start_time = models.TimeField('開始', null=True, blank=True)
    end_time = models.TimeField('終了', null=True, blank=True)
    note = models.CharField('備考', max_length=200, blank=True, default='')

    class Meta:
        unique_together = [('employee', 'date')]
        ordering = ['-date', 'employee__code']

    def __str__(self) -> str:
        return f'{self.date} {self.employee}'
