from django.utils import timezone
from django.db import transaction
from django.http import HttpResponse
from .models import Employee, Attendance, Shift
import pandas as pd
from io import BytesIO


class PunchService:
    @staticmethod
    def punch_by_code(code: str, action: str) -> str:
        emp = Employee.objects.filter(code=code, is_active=True).first()
        if not emp:
            raise ValueError("従業員コードが見つかりません。")
        return PunchService.punch(emp, action)

    @staticmethod
    @transaction.atomic
    def punch(employee: Employee, action: str) -> str:
        today = timezone.localdate()
        now = timezone.now()
        att, _ = Attendance.objects.get_or_create(employee=employee, work_date=today)
        if action == "in":
            if att.clock_in:
                raise ValueError("本日はすでに出勤済みです。")
            att.clock_in = now
            att.save(update_fields=["clock_in"])
            return f"{employee.name} さん、出勤を記録しました。"
        if action == "out":
            if not att.clock_in:
                raise ValueError("本日は出勤が未記録です。")
            if att.clock_out:
                raise ValueError("本日はすでに退勤済みです。")
            att.clock_out = now
            att.save(update_fields=["clock_out"])
            return f"{employee.name} さん、退勤を記録しました。"
        raise ValueError("不正な操作です。")


class EmployeeExcelImporter:
    REQUIRED_COLS = ["code", "name"]

    def __init__(self, file):
        self.file = file

    def run(self):
        df = pd.read_excel(self.file)
        miss = [c for c in self.REQUIRED_COLS if c not in df.columns]
        if miss:
            raise ValueError(f"従業員Excelに必要な列がありません: {miss}")

        # 「時給」 or 「hourly_rate」どちらでも受け付ける
        hourly_col = None
        for cand in ("時給", "hourly_rate", "wage"):
            if cand in df.columns:
                hourly_col = cand
                break

        created = updated = 0
        for _, r in df.iterrows():
            code = str(r["code"]).strip()
            name = str(r["name"]).strip()
            hourly = None
            if hourly_col is not None:
                val = r.get(hourly_col)
                if pd.notna(val):
                    try:
                        hourly = int(float(val))  # "1200", 1200.0 などを整数化
                    except Exception:
                        raise ValueError(f"時給の値が不正です: {val}")

            obj, is_created = Employee.objects.update_or_create(
                code=code,
                defaults={"name": name, "hourly_rate": hourly}
            )
            created += int(is_created)
            updated += int(not is_created)
        return {"created": created, "updated": updated}


class ShiftExcelImporter:
    REQUIRED_COLS = ["date", "employee_code", "start", "end"]

    def __init__(self, file):
        self.file = file

    def run(self):
        df = pd.read_excel(self.file)
        miss = [c for c in self.REQUIRED_COLS if c not in df.columns]
        if miss:
            raise ValueError(f"シフトExcelに必要な列がありません: {miss}")

        created = 0
        for _, r in df.iterrows():
            emp = Employee.objects.filter(code=str(r["employee_code"]).strip()).first()
            if not emp:
                raise ValueError(f"従業員コードが存在しません: {r['employee_code']}")
            start = pd.to_datetime(r["start"]).time()
            end = pd.to_datetime(r["end"]).time()
            date = pd.to_datetime(r["date"]).date()
            break_minutes = int(r.get("break_minutes", 0) or 0)
            Shift.objects.update_or_create(
                employee=emp, date=date, start=start,
                defaults={"end": end, "break_minutes": break_minutes}
            )
            created += 1
        return {"created": created}


class ExcelExporter:
    @staticmethod
    def employee_template_df():
        return pd.DataFrame([
            {"code": "E001", "name": "山田太郎", "時給": 1200},
            {"code": "E002", "name": "佐藤花子", "時給": 1300},
        ])

    @staticmethod
    def shift_template_df():
        return pd.DataFrame([
            {"date": "2025-08-13", "employee_code": "E001", "start": "09:00", "end": "18:00", "break_minutes": 60},
        ])

    @staticmethod
    def employees_df():# Excelはtz付きdatetimeが苦手なのでJST文字列にして安全に出力
        rows = []
        for e in Employee.objects.order_by("code"):
            rows.append({
                "code": e.code,
                "name": e.name,
                "時給": e.hourly_rate,  # 日本語列名
                "is_active": e.is_active,
                "created_at": timezone.localtime(e.created_at).strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": timezone.localtime(e.updated_at).strftime("%Y-%m-%d %H:%M:%S"),
            })
        return pd.DataFrame(rows)

    @staticmethod
    def shifts_df(date=None):
        qs = Shift.objects.select_related("employee").order_by("date", "start")
        if date:
            qs = qs.filter(date=date)
        rows = []
        for s in qs:
            rows.append({
                "employee_code": s.employee.code,
                "employee_name": s.employee.name,
                "date": s.date,
                "start": s.start.strftime("%H:%M"),
                "end": s.end.strftime("%H:%M"),
                "break_minutes": s.break_minutes,
                "note": s.note,
            })
        return pd.DataFrame(rows)

    @staticmethod
    def df_to_xlsx_response(df, filename: str) -> HttpResponse:
        try:
            for col in df.select_dtypes(include=["datetimetz"]).columns:   # 念のため tz-aware が紛れても外す保険
                df[col] = df[col].dt.tz_localize(None)
        except Exception:
            pass

        bio = BytesIO()
        with pd.ExcelWriter(bio, engine="openpyxl") as w:
            df.to_excel(w, index=False)
        bio.seek(0)
        resp = HttpResponse(
            bio.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        return resp
