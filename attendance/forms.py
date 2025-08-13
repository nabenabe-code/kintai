from __future__ import annotations

from datetime import datetime
from django import forms
from django.core.exceptions import ValidationError

from .models import Employee, Shift

class PunchForm(forms.Form):
    employee = forms.ModelChoiceField(
        label="従業員",
        queryset=Employee.objects.filter(is_active=True).order_by("code"),
        empty_label=None,
    )

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ["code", "name", "hourly_rate", "is_active"]
        labels = {
            "code": "社員番号",
            "name": "氏名",
            "hourly_rate": "時給",
            "is_active": "在籍",
        }


class EmployeeDeleteForm(forms.Form):
    employee = forms.ModelChoiceField(
        label="在籍中の従業員",
        queryset=Employee.objects.filter(is_active=True).order_by("code"),
        empty_label=None,
    )

    def clean_employee(self):
        emp = self.cleaned_data["employee"]
        if not emp.is_active:
            raise ValidationError("すでに在籍OFFです。")
        return emp


class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ["employee", "date", "start_time", "end_time", "note"]
        labels = {
            "employee": "従業員",
            "date": "日付",
            "start_time": "開始",
            "end_time": "終了",
            "note": "備考",
        }
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def clean(self):
        cleaned = super().clean()
        st = cleaned.get("start_time")
        et = cleaned.get("end_time")
        if st and et and et <= st:
            raise ValidationError("終了は開始より後にしてください。")
        return cleaned


class EmployeeImportForm(forms.Form):
    file = forms.FileField(label="従業員Excelファイル（.xlsx）")


class ShiftImportForm(forms.Form):
    file = forms.FileField(label="シフトExcelファイル（.xlsx）")
