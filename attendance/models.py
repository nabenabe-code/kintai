from django.db import models

class Employee(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    hourly_rate = models.PositiveIntegerField("時給(円)", null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return f"{self.code} {self.name}"

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="attendances")
    work_date = models.DateField()
    clock_in = models.DateTimeField(null=True, blank=True)
    clock_out = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["employee", "work_date"], name="uniq_employee_date")
        ]
        indexes = [models.Index(fields=["work_date"])]

    @property
    def is_open(self):
        return bool(self.clock_in and not self.clock_out)

class Shift(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="shifts")
    date = models.DateField()
    start = models.TimeField()
    end = models.TimeField()
    break_minutes = models.PositiveSmallIntegerField(default=0)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        indexes = [models.Index(fields=["date"])]
        ordering = ["date", "start"]

    def __str__(self):
        return f"{self.date} {self.employee} {self.start}-{self.end}"
    
    def total_work_minutes(self) -> int:
        start_dt = datetime.combine(self.date, self.start)
        end_dt = datetime.combine(self.date, self.end)
        if end_dt < start_dt:
            end_dt += timedelta(days=1)  # 日跨ぎ対応
        mins = int((end_dt - start_dt).total_seconds() // 60) - int(self.break_minutes or 0)
        return max(mins, 0)

    @property
    def total_work_hhmm(self) -> str:
        m = self.total_work_minutes()
        h, mm = divmod(m, 60)
        return f"{h}:{mm:02d}"
