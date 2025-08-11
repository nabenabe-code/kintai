# ==============================================================
# 目的：
#  - モデルの振る舞い（clock_in/out、時間計算）が壊れていないか
#  - サービス層（PunchService、各 Importer）が正しく動くか
#  - 主要なビュー（打刻画面、一覧、Excelダウンロード）が落ちないか
#
# 実行方法：
#   python manage.py test attendance
# ==============================================================

from datetime import time, datetime
from io import BytesIO

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from openpyxl import Workbook

from .models import Employee, Attendance, Shift
from .services import PunchService, EmployeeImporter, ShiftImporter


# ---------------- モデルのテスト ----------------
class ModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.emp = Employee.objects.create(code='E001', name='太郎', hourly_rate=1000)

    def test_attendance_clock_in_out_normal(self):
        """通常の出勤→退勤で、勤務時間と支給額が正しいか。"""
        att = Attendance.objects.create(employee=self.emp, work_date=timezone.localdate())
        att.clock_in(time(9, 0))
        att.clock_out(time(18, 0))
        self.assertEqual(att.work_seconds, 9 * 3600)
        self.assertAlmostEqual(att.work_hours, 9.0)
        self.assertEqual(att.wage_amount, 9000)

    def test_attendance_clock_out_without_in_raises(self):
        """出勤前に退勤するとエラーになる。"""
        att = Attendance.objects.create(employee=self.emp, work_date=timezone.localdate())
        with self.assertRaises(ValueError):
            att.clock_out(time(18, 0))

    def test_attendance_overnight(self):
        """日跨ぎ（22:00→翌6:00）でも正しく時間計算される。"""
        att = Attendance.objects.create(employee=self.emp, work_date=timezone.localdate())
        att.clock_in(time(22, 0))
        att.clock_out(time(6, 0))
        self.assertEqual(att.work_seconds, 8 * 3600)


# ---------------- サービス層のテスト ----------------
class PunchServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.emp = Employee.objects.create(code='E100', name='花子', hourly_rate=1200)

    def test_punch_service_in_out(self):
        """PunchService で出勤→退勤ができる。"""
        svc = PunchService(self.emp)
        today = timezone.localdate()

        svc.clock_in(time(9, 0))
        att = Attendance.objects.get(employee=self.emp, work_date=today)
        self.assertIsNotNone(att.time_in)

        svc.clock_out(time(18, 0))
        att.refresh_from_db()
        self.assertIsNotNone(att.time_out)

    def test_punch_service_double_in_raises(self):
        """二重出勤は models 側のガードで例外になる。"""
        svc = PunchService(self.emp)
        svc.clock_in(time(9, 0))
        with self.assertRaises(ValueError):
            svc.clock_in(time(10, 0))


# ---------------- Importer のテスト ----------------
class ImporterTests(TestCase):
    def _wb_to_bytes(self, wb: Workbook) -> BytesIO:
        """workbook を BytesIO にして先頭へシークしたものを返す。"""
        fp = BytesIO()
        wb.save(fp)
        fp.seek(0)
        return fp

    def test_employee_importer(self):
        """従業員インポートで作成・更新・スキップの件数が返る。"""
        wb = Workbook()
        ws = wb.active
        ws.append(['code', 'name', 'hourly_rate'])
        ws.append(['E001', '太郎', 1000])
        ws.append(['E002', '花子', 1100])
        fp = self._wb_to_bytes(wb)

        created, updated, skipped = EmployeeImporter().run(fp)
        self.assertEqual((created, updated, skipped), (2, 0, 0))
        self.assertEqual(Employee.objects.count(), 2)

        # 同じ内容をもう一度流すと updated に回る
        fp2 = self._wb_to_bytes(wb)
        created2, updated2, skipped2 = EmployeeImporter().run(fp2)
        self.assertEqual((created2, updated2, skipped2), (0, 2, 0))

    def test_shift_importer(self):
        """シフトインポートでシフトが登録される。"""
        emp = Employee.objects.create(code='S001', name='佐藤', hourly_rate=1000)

        wb = Workbook()
        ws = wb.active
        ws.append(['code', 'date', 'start', 'end', 'note'])
        today = timezone.localdate().strftime('%Y-%m-%d')
        ws.append(['S001', today, '09:00', '18:00', '通常'])
        fp = self._wb_to_bytes(wb)

        created, updated, skipped = ShiftImporter().run(fp)
        self.assertEqual((created, updated, skipped), (1, 0, 0))
        self.assertEqual(Shift.objects.count(), 1)


# ---------------- ビューのテスト ----------------
class ViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.emp = Employee.objects.create(code='V001', name='表示用', hourly_rate=1000)

    def setUp(self):
        self.client = Client()

    def test_punch_page_get(self):
        """トップ（打刻）ページが表示できる。"""
        resp = self.client.get(reverse('punch_page'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '従業員')  # ラベルの一部

    def test_punch_page_post_in(self):
        """打刻：出勤ボタンで出勤時刻が入る。"""
        resp = self.client.post(reverse('punch_page'),
                                data={'employee': self.emp.pk, 'action': 'in'})
        # 成功時はリダイレクト
        self.assertEqual(resp.status_code, 302)

        att = Attendance.objects.get(employee=self.emp, work_date=timezone.localdate())
        self.assertIsNotNone(att.time_in)

    def test_attendance_list_view(self):
        """勤怠一覧が 200 を返す。"""
        resp = self.client.get(reverse('attendance_list'))
        self.assertEqual(resp.status_code, 200)

    def test_shift_list_view(self):
        """シフト一覧が 200 を返す（パラメータ無し＝今月）。"""
        resp = self.client.get(reverse('shift_list'))
        self.assertEqual(resp.status_code, 200)

    def test_export_excel_endpoints(self):
        """Excel ダウンロード3種が成功する。"""
        # 勤怠
        r1 = self.client.get(reverse('attendance_export'))
        self.assertEqual(r1.status_code, 200)
        self.assertIn('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                      r1.headers.get('Content-Type', ''))

        # 従業員
        r2 = self.client.get(reverse('employee_export'))
        self.assertEqual(r2.status_code, 200)

        # シフト
        r3 = self.client.get(reverse('shift_export'))
        self.assertEqual(r3.status_code, 200)
from django.test import TestCase

# Create your tests here.
