import datetime

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import Client, TestCase

from rejs.admin import RejsyAdmin, ZgloszenieAdmin
from rejs.models import Rejs, Zgloszenie


# Helper to get future dates for tests
def future_date(days_from_now: int) -> str:
	"""Return a date string N days from today."""
	return (datetime.date.today() + datetime.timedelta(days=days_from_now)).isoformat()


class AdminTest(TestCase):
	"""Testy panelu administracyjnego."""

	def setUp(self):
		self.client = Client()
		self.admin_user = User.objects.create_superuser(
			username="admin", email="admin@example.com", password="adminpass123"
		)
		self.client.login(username="admin", password="adminpass123")
		self.rejs = Rejs.objects.create(
			nazwa="Rejs testowy",
			od=future_date(30),
			do=future_date(44),
			start="Gdynia",
			koniec="Sztokholm",
		)

	def test_rejs_admin_accessible(self):
		"""Test dostępności admina rejsów."""
		response = self.client.get("/admin/rejs/rejs/")
		self.assertEqual(response.status_code, 200)

	def test_rejs_admin_add(self):
		"""Test dodawania rejsu przez admin."""
		response = self.client.get("/admin/rejs/rejs/add/")
		self.assertEqual(response.status_code, 200)

	def test_zgloszenie_admin_accessible(self):
		"""Test dostępności admina zgłoszeń."""
		response = self.client.get("/admin/rejs/zgloszenie/")
		self.assertEqual(response.status_code, 200)

	def test_zgloszenie_admin_change(self):
		"""Test edycji zgłoszenia przez admin."""
		zgloszenie = Zgloszenie.objects.create(
			imie="Jan",
			nazwisko="Kowalski",
			email="jan@example.com",
			telefon="123456789",
			data_urodzenia=datetime.date(1990, 1, 1),
			rejs=self.rejs,
			rodo=True,
			obecnosc="tak",
		)
		response = self.client.get(f"/admin/rejs/zgloszenie/{zgloszenie.id}/change/")
		self.assertEqual(response.status_code, 200)

	def test_rejs_admin_has_inlines(self):
		"""Test czy admin rejsu ma inline'y."""
		site = AdminSite()
		admin = RejsyAdmin(Rejs, site)
		self.assertEqual(len(admin.inlines), 3)

	def test_zgloszenie_admin_has_readonly_fields(self):
		"""Test czy admin zgłoszenia ma pola tylko do odczytu."""
		site = AdminSite()
		admin = ZgloszenieAdmin(Zgloszenie, site)
		self.assertIn("rejs_cena", admin.readonly_fields)
		self.assertIn("do_zaplaty", admin.readonly_fields)
		self.assertIn("suma_wplat", admin.readonly_fields)
