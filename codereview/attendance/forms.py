"""
forms.py
- PunchForm: 打刻（在籍者のみ）
- EmployeeForm: 従業員登録
- EmployeeDeleteForm: 従業員の論理削除（code+name+hourly_rate が一致した在籍者のみ）
- ShiftForm: シフト登録
- EmployeeImportForm / ShiftImportForm: Excel取込
"""
from django import forms
from .models import Employee, Shift


class PunchForm(forms.Form):
    employee = forms.ModelChoiceField(
        label='従業員・ employee',
        queryset=Employee.objects.filter(is_active=True).order_by('code'),
        help_text=''
    )


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['code', 'name', 'hourly_rate']
        labels = {'code': '社員番号', 'name': '氏名', 'hourly_rate': '時給'}
        help_texts = {k: '' for k in fields}

    def clean_hourly_rate(self):
        rate = self.cleaned_data.get('hourly_rate')
        if rate is None:
            return rate
        if rate < 0:
            raise forms.ValidationError('時給は0以上を入力してください。')
        if rate > 100000:
            raise forms.ValidationError('時給が高すぎます。確認してください。')
        return rate


class EmployeeDeleteForm(forms.Form):
    """
    社員番号・氏名・時給 がすべて一致する在籍者のみ削除可能（在籍OFF）。
    """
    code = forms.CharField(
        label='',
        max_length=20,
        widget=forms.TextInput(attrs={'placeholder': '社員番号'})
    )
    name = forms.CharField(
        label='',
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': '氏名'})
    )
    hourly_rate = forms.DecimalField(
        label='',
        max_digits=8, decimal_places=2,
        widget=forms.TextInput(attrs={'placeholder': '時給'})
    )

    def clean(self):
        cleaned = super().clean()
        code = (cleaned.get('code') or '').strip()
        name = (cleaned.get('name') or '').strip()
        rate = cleaned.get('hourly_rate')

        if not code or not name or rate is None:
            raise forms.ValidationError('社員番号・氏名・時給をすべて入力してください。')

        try:
            emp = Employee.objects.get(code=code, name=name, hourly_rate=rate, is_active=True)
        except Employee.DoesNotExist:
            raise forms.ValidationError('一致する在籍中の従業員が見つかりません。')

        cleaned['employee'] = emp
        return cleaned


class ShiftForm(forms.ModelForm):
    class Meta:
        model = Shift
        fields = ['employee', 'date', 'start_time', 'end_time', 'note']
        labels = {'employee': '従業員', 'date': '日付', 'start_time': '開始', 'end_time': '終了', 'note': '備考'}
        help_texts = {k: '' for k in fields}

    def clean(self):
        cleaned = super().clean()
        st = cleaned.get('start_time')
        ed = cleaned.get('end_time')
        if (st and not ed) or (ed and not st):
            raise forms.ValidationError('開始と終了は両方入力してください。')
        return cleaned


class EmployeeImportForm(forms.Form):
    file = forms.FileField(label='Excel ファイル (.xlsx)', help_text='')


class ShiftImportForm(forms.Form):
    file = forms.FileField(label='Excel ファイル (.xlsx)', help_text='')
