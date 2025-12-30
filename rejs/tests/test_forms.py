import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase

from rejs.forms import Dane_DodatkoweForm, ZgloszenieForm, validate_pesel
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


class ValidatePeselTest(TestCase):
	"""Testy funkcji walidacji PESEL."""

	def test_valid_pesel(self):
		"""Test poprawnego numeru PESEL."""
		# 90021401384 - poprawny PESEL (suma kontrolna = 0 mod 10)
		result = validate_pesel("90021401384")
		self.assertEqual(result, "90021401384")

	def test_valid_pesel_with_spaces(self):
		"""Test PESEL ze spacjami - powinny być usunięte."""
		result = validate_pesel("900 214 013 84")
		self.assertEqual(result, "90021401384")

	def test_valid_pesel_with_dashes(self):
		"""Test PESEL z myślnikami - powinny być usunięte."""
		result = validate_pesel("900-214-013-84")
		self.assertEqual(result, "90021401384")

	def test_empty_pesel(self):
		"""Test pustego PESEL."""
		with self.assertRaises(ValidationError) as context:
			validate_pesel("")
		self.assertIn("wymagany", str(context.exception))

	def test_pesel_too_short(self):
		"""Test za krótkiego PESEL."""
		with self.assertRaises(ValidationError) as context:
			validate_pesel("1234567890")  # 10 cyfr
		self.assertIn("11 cyfr", str(context.exception))

	def test_pesel_too_long(self):
		"""Test za długiego PESEL."""
		with self.assertRaises(ValidationError) as context:
			validate_pesel("123456789012")  # 12 cyfr
		self.assertIn("11 cyfr", str(context.exception))

	def test_pesel_with_letters(self):
		"""Test PESEL z literami."""
		with self.assertRaises(ValidationError) as context:
			validate_pesel("9002140138A")
		self.assertIn("tylko cyfry", str(context.exception))

	def test_pesel_invalid_checksum(self):
		"""Test PESEL z błędną sumą kontrolną."""
		with self.assertRaises(ValidationError) as context:
			validate_pesel("90021401385")  # ostatnia cyfra zmieniona (4->5)
		self.assertIn("suma kontrolna", str(context.exception))

	def test_pesel_all_zeros(self):
		"""Test PESEL składającego się z samych zer."""
		# 00000000000 ma sumę kontrolną 0, więc jest technicznie poprawny
		result = validate_pesel("00000000000")
		self.assertEqual(result, "00000000000")


class Dane_DodatkoweFormTest(TestCase):
	"""Testy formularza danych dodatkowych."""

	def get_valid_form_data(self, **overrides):
		"""Zwraca słownik z poprawnymi danymi formularza."""
		data = {
			"poz1": "90021401384",  # poprawny PESEL
			"poz2": "paszport",
			"poz3": "ABC123456",
			"zgoda_dane_wrazliwe": True,
		}
		data.update(overrides)
		return data

	def test_valid_form(self):
		"""Test poprawnego formularza."""
		form = Dane_DodatkoweForm(data=self.get_valid_form_data())
		self.assertTrue(form.is_valid(), form.errors)

	def test_valid_form_with_dowod(self):
		"""Test poprawnego formularza z dowodem osobistym."""
		form = Dane_DodatkoweForm(data=self.get_valid_form_data(poz2="dowod-osobisty"))
		self.assertTrue(form.is_valid(), form.errors)

	def test_invalid_pesel_in_form(self):
		"""Test formularza z niepoprawnym PESEL."""
		form = Dane_DodatkoweForm(data=self.get_valid_form_data(poz1="12345678901"))
		self.assertFalse(form.is_valid())
		self.assertIn("poz1", form.errors)

	def test_empty_pesel_in_form(self):
		"""Test formularza z pustym PESEL."""
		form = Dane_DodatkoweForm(data=self.get_valid_form_data(poz1=""))
		self.assertFalse(form.is_valid())
		self.assertIn("poz1", form.errors)

	def test_zgoda_required(self):
		"""Test że zgoda jest wymagana."""
		form = Dane_DodatkoweForm(data=self.get_valid_form_data(zgoda_dane_wrazliwe=False))
		self.assertFalse(form.is_valid())
		self.assertIn("zgoda_dane_wrazliwe", form.errors)

	def test_zgoda_missing(self):
		"""Test formularza bez zgody."""
		data = self.get_valid_form_data()
		del data["zgoda_dane_wrazliwe"]
		form = Dane_DodatkoweForm(data=data)
		self.assertFalse(form.is_valid())

	def test_dokument_required(self):
		"""Test że numer dokumentu jest wymagany."""
		form = Dane_DodatkoweForm(data=self.get_valid_form_data(poz3=""))
		self.assertFalse(form.is_valid())
		self.assertIn("poz3", form.errors)

	def test_pesel_cleaned_in_form(self):
		"""Test że PESEL jest czyszczony w formularzu."""
		form = Dane_DodatkoweForm(data=self.get_valid_form_data(poz1="900 214 01384"))
		self.assertTrue(form.is_valid(), form.errors)
		self.assertEqual(form.cleaned_data["poz1"], "90021401384")
