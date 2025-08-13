from django.contrib import admin
from .models import Employee, Attendance, Shift

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_active", "hourly_rate")
    search_fields = ("code", "name")

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "work_date", "clock_in", "clock_out")
    list_filter = ("work_date",)

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ("employee", "date", "start", "end", "break_minutes")
    list_filter = ("date",)
