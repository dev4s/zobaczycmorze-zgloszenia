import datetime

from django.test import TestCase

from rejs.forms import ZgloszenieForm
from rejs.models import Rejs


# Helper to get future dates for tests
def future_date(days_from_now: int) -> str:
	"""Return a date string N days from today."""
	return (datetime.date.today() + datetime.timedelta(days=days_from_now)).isoformat()


class ZgloszenieFormTest(TestCase):
	"""Testy formularza zgłoszenia."""

	def setUp(self):
		self.rejs = Rejs.objects.create(
			nazwa="Rejs testowy",
			od=future_date(30),
			do=future_date(44),
			start="Gdynia",
			koniec="Sztokholm",
		)

	def get_valid_form_data(self, **overrides):
		"""Zwraca słownik z poprawnymi danymi formularza."""
		data = {
			"imie": "Jan",
			"nazwisko": "Kowalski",
			"email": "jan@example.com",
			"telefon": "123456789",
			"data_urodzenia": "1990-01-01",
			"adres": "ul. Testowa 1",
			"kod_pocztowy": "00-001",
			"miejscowosc": "Warszawa",
			"wzrok": "NIEWIDOMY",
			"obecnosc": "tak",
			"rodo": True,
		}
		data.update(overrides)
		return data

	def test_valid_form(self):
		"""Test poprawnego formularza."""
		form = ZgloszenieForm(data=self.get_valid_form_data(), initial={"rejs": self.rejs})
		self.assertTrue(form.is_valid())

	def test_telefon_validation_9_digits(self):
		"""Test walidacji telefonu - 9 cyfr."""
		form = ZgloszenieForm(data=self.get_valid_form_data(telefon="123456789"), initial={"rejs": self.rejs})
		self.assertTrue(form.is_valid())

	def test_telefon_validation_with_plus(self):
		"""Test walidacji telefonu z +."""
		form = ZgloszenieForm(data=self.get_valid_form_data(telefon="+48123456789"), initial={"rejs": self.rejs})
		self.assertTrue(form.is_valid())

	def test_telefon_validation_15_digits(self):
		"""Test walidacji telefonu - 15 cyfr."""
		form = ZgloszenieForm(data=self.get_valid_form_data(telefon="123456789012345"), initial={"rejs": self.rejs})
		self.assertTrue(form.is_valid())

	def test_telefon_validation_invalid_letters(self):
		"""Test walidacji telefonu - litery."""
		form = ZgloszenieForm(data=self.get_valid_form_data(telefon="abc123def"), initial={"rejs": self.rejs})
		self.assertFalse(form.is_valid())
		self.assertIn("telefon", form.errors)

	def test_telefon_validation_too_short(self):
		"""Test walidacji telefonu - za krótki."""
		form = ZgloszenieForm(data=self.get_valid_form_data(telefon="12345678"), initial={"rejs": self.rejs})
		self.assertFalse(form.is_valid())

	def test_telefon_cleans_spaces_and_dashes(self):
		"""Test czy telefon jest czyszczony ze spacji i myślników."""
		form = ZgloszenieForm(data=self.get_valid_form_data(telefon="123-456-789"), initial={"rejs": self.rejs})
		self.assertTrue(form.is_valid())
		self.assertEqual(form.cleaned_data["telefon"], "123456789")

	def test_required_fields(self):
		"""Test wymaganych pól."""
		form = ZgloszenieForm(data={}, initial={"rejs": self.rejs})
		self.assertFalse(form.is_valid())
		self.assertIn("imie", form.errors)
		self.assertIn("nazwisko", form.errors)
		self.assertIn("email", form.errors)
		self.assertIn("telefon", form.errors)

	def test_invalid_email(self):
		"""Test nieprawidłowego emaila."""
		form = ZgloszenieForm(data=self.get_valid_form_data(email="nieprawidlowy-email"), initial={"rejs": self.rejs})
		self.assertFalse(form.is_valid())
		self.assertIn("email", form.errors)
