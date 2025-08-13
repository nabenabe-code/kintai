from django.contrib import admin
from .models import Attendance, Shift  

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    @admin.display(description="出勤")
    def clock_in(self, obj):
        for name in ("clock_in", "start", "start_time", "in_time", "time_in"):
            v = getattr(obj, name, None)
            if v:
                return v
        return "-"

    @admin.display(description="退勤")
    def clock_out(self, obj):
        for name in ("clock_out", "end", "end_time", "out_time", "time_out"):
            v = getattr(obj, name, None)
            if v:
                return v
        return "-"

    @admin.display(description="実働(分)")
    def worked_minutes(self, obj):
        cin = None
        cout = None
        for name in ("clock_in", "start", "start_time", "in_time", "time_in"):
            cin = cin or getattr(obj, name, None)
        for name in ("clock_out", "end", "end_time", "out_time", "time_out"):
            cout = cout or getattr(obj, name, None)
        if cin and cout:
            try:
                return int((cout - cin).total_seconds() // 60)
            except Exception:
                pass
        return None

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    @admin.display(description="開始")
    def start(self, obj):
        for name in ("start", "start_time", "begin"):
            v = getattr(obj, name, None)
            if v:
                return v
        return "-"

    @admin.display(description="終了")
    def end(self, obj):
        for name in ("end", "end_time", "finish"):
            v = getattr(obj, name, None)
            if v:
                return v
        return "-"

    @admin.display(description="休憩(分)")
    def break_minutes(self, obj):
        # 明示フィールドがあればそれを使う
        for name in ("break_minutes", "break_min", "break_duration_min"):
            if hasattr(obj, name):
                return getattr(obj, name)
        # 休憩の開始/終了から計算
        bstart = getattr(obj, "break_start", None) or getattr(obj, "break_from", None)
        bend   = getattr(obj, "break_end", None)   or getattr(obj, "break_to", None)
        if bstart and bend:
            try:
                return int((bend - bstart).total_seconds() // 60)
            except Exception:
                pass
        return 0
