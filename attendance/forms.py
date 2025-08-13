from django import forms
from .models import Employee, Shift

class PunchForm(forms.Form): #出勤と退勤の画面
    employee_code = forms.CharField(
        label="従業員コード",
        max_length=20,
        widget=forms.TextInput(attrs={"class": "input"})
    )

class EmployeeForm(forms.ModelForm):#従業員登録画面
    class Meta:
        model = Employee
        fields = ["code", "name", "hourly_rate",]  
        labels = {"hourly_rate": "時給（円）"}
        widgets = {
            "code": forms.TextInput(attrs={"class": "input"}),
            "name": forms.TextInput(attrs={"class": "input"}),
            "hourly_rate": forms.NumberInput(attrs={"class": "input", "min": 0, "step": 1}),
        }


class ShiftForm(forms.ModelForm): #シフト登録画面
    class Meta:
        model = Shift
        fields = ["employee", "date", "start", "end", "break_minutes", "note"]
        widgets = {
            "date":  forms.DateInput(attrs={"type": "date", "class": "input"}),
            "start": forms.TimeInput(attrs={"type": "time", "class": "input", "step": 300}),
            "end":   forms.TimeInput(attrs={"type": "time", "class": "input", "step": 300}),
            "break_minutes": forms.NumberInput(attrs={"class": "input", "min": 0, "step": 1}),
            "note":  forms.TextInput(attrs={"class": "input"}),
        }

class BulkExcelUploadForm(forms.Form): #Excel一括登録画面
    employees_file = forms.FileField(label="従業員Excel (.xlsx)", required=False)   
    shifts_file = forms.FileField(label="シフトExcel (.xlsx)", required=False)

class ShiftSearchForm(forms.Form):
    date = forms.DateField(label="日付", widget=forms.DateInput(attrs={"type": "date", "class": "input"}))
