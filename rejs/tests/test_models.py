import datetime
from decimal import Decimal

from django.forms import ValidationError
from django.test import TestCase
from django.urls import reverse

from rejs.models import Ogloszenie, Rejs, Wachta, Wplata, Zgloszenie


# Helper to get future dates for tests
def future_date(days_from_now: int) -> str:
	"""Return a date string N days from today."""
	return (datetime.date.today() + datetime.timedelta(days=days_from_now)).isoformat()


class RejsModelTest(TestCase):
	"""Testy modelu Rejs."""

	def setUp(self):
		self.rejs = Rejs.objects.create(
			nazwa="Rejs testowy",
			od=future_date(30),
			do=future_date(44),
			start="Gdynia",
			koniec="Sztokholm",
			cena=Decimal("1500.00"),
			zaliczka=Decimal("500.00"),
			opis="Opis testowego rejsu",
		)

	def test_str_representation(self):
		"""Test reprezentacji tekstowej rejsu."""
		self.assertEqual(str(self.rejs), "Rejs testowy")

	def test_reszta_do_zaplaty(self):
		"""Test obliczania reszty do zapłaty."""
		self.assertEqual(self.rejs.reszta_do_zaplaty, Decimal("1000.00"))

	def test_reszta_do_zaplaty_custom_values(self):
		"""Test reszty do zapłaty z niestandardowymi wartościami."""
		rejs = Rejs.objects.create(
			nazwa="Rejs drogi",
			od=future_date(60),
			do=future_date(74),
			start="Gdańsk",
			koniec="Kopenhaga",
			cena=Decimal("2500.00"),
			zaliczka=Decimal("800.00"),
		)
		self.assertEqual(rejs.reszta_do_zaplaty, Decimal("1700.00"))


class WachtaModelTest(TestCase):
	"""Testy modelu Wachta."""

	def setUp(self):
		self.rejs = Rejs.objects.create(
			nazwa="Rejs testowy",
			od=future_date(30),
			do=future_date(44),
			start="Gdynia",
			koniec="Sztokholm",
		)
		self.wachta = Wachta.objects.create(rejs=self.rejs, nazwa="Alfa")

	def test_str_representation(self):
		"""Test reprezentacji tekstowej wachty."""
		self.assertEqual(str(self.wachta), "Wachta Alfa - Rejs testowy")


class ZgloszenieModelTest(TestCase):
	"""Testy modelu Zgloszenie."""

	def setUp(self):
		self.rejs = Rejs.objects.create(
			nazwa="Rejs testowy",
			od=future_date(30),
			do=future_date(44),
			start="Gdynia",
			koniec="Sztokholm",
			cena=Decimal("1500.00"),
			zaliczka=Decimal("500.00"),
		)
		self.zgloszenie = Zgloszenie.objects.create(
			imie="Jan",
			nazwisko="Kowalski",
			email="jan@example.com",
			telefon="123456789",
			data_urodzenia=datetime.date(1990, 1, 1),
			rejs=self.rejs,
			rodo=True,
			obecnosc="tak",
		)

	def test_str_representation(self):
		"""Test reprezentacji tekstowej zgłoszenia."""
		self.assertEqual(str(self.zgloszenie), "Jan Kowalski")

	def test_token_generated_on_create(self):
		"""Test czy token UUID jest generowany przy tworzeniu."""
		self.assertIsNotNone(self.zgloszenie.token)

	def test_token_is_unique(self):
		"""Test unikalności tokena."""
		zgloszenie2 = Zgloszenie.objects.create(
			imie="Anna",
			nazwisko="Nowak",
			email="anna@example.com",
			telefon="987654321",
			data_urodzenia=datetime.date(1991, 2, 2),
			rejs=self.rejs,
			rodo=True,
			obecnosc="tak",
		)
		self.assertNotEqual(self.zgloszenie.token, zgloszenie2.token)

	def test_suma_wplat_empty(self):
		"""Test sumy wpłat gdy brak wpłat."""
		self.assertEqual(self.zgloszenie.suma_wplat, Decimal("0"))

	def test_suma_wplat_with_payments(self):
		"""Test sumy wpłat z wpłatami."""
		Wplata.objects.create(zgloszenie=self.zgloszenie, kwota=Decimal("500.00"), rodzaj="wplata")
		Wplata.objects.create(zgloszenie=self.zgloszenie, kwota=Decimal("300.00"), rodzaj="wplata")
		self.assertEqual(self.zgloszenie.suma_wplat, Decimal("800.00"))

	def test_suma_wplat_with_zwroty(self):
		"""Test sumy wpłat z wpłatami i zwrotami."""
		Wplata.objects.create(zgloszenie=self.zgloszenie, kwota=Decimal("500.00"), rodzaj="wplata")
		Wplata.objects.create(zgloszenie=self.zgloszenie, kwota=Decimal("100.00"), rodzaj="zwrot")
		self.assertEqual(self.zgloszenie.suma_wplat, Decimal("400.00"))

	def test_do_zaplaty_calculation(self):
		"""Test obliczania kwoty do zapłaty."""
		self.assertEqual(self.zgloszenie.do_zaplaty, Decimal("1500.00"))

		Wplata.objects.create(zgloszenie=self.zgloszenie, kwota=Decimal("500.00"), rodzaj="wplata")
		self.assertEqual(self.zgloszenie.do_zaplaty, Decimal("1000.00"))

	def test_rejs_cena(self):
		"""Test właściwości rejs_cena."""
		self.assertEqual(self.zgloszenie.rejs_cena, Decimal("1500.00"))

	def test_clean_wachta_validation_same_rejs(self):
		"""Test walidacji - wachta z tego samego rejsu."""
		wachta = Wachta.objects.create(rejs=self.rejs, nazwa="Alfa")
		self.zgloszenie.wachta = wachta
		self.zgloszenie.clean()

	def test_clean_wachta_validation_different_rejs(self):
		"""Test walidacji - wachta z innego rejsu."""
		inny_rejs = Rejs.objects.create(
			nazwa="Inny rejs",
			od=future_date(60),
			do=future_date(74),
			start="Gdańsk",
			koniec="Helsinki",
		)
		wachta = Wachta.objects.create(rejs=inny_rejs, nazwa="Beta")
		self.zgloszenie.wachta = wachta

		with self.assertRaises(ValidationError):
			self.zgloszenie.clean()

	def test_get_absolute_url(self):
		"""Test generowania URL do szczegółów zgłoszenia."""
		url = self.zgloszenie.get_absolute_url()
		expected = reverse("zgloszenie_details", kwargs={"token": self.zgloszenie.token})
		self.assertEqual(url, expected)


class WplataModelTest(TestCase):
	"""Testy modelu Wplata."""

	def setUp(self):
		self.rejs = Rejs.objects.create(
			nazwa="Rejs testowy",
			od=future_date(30),
			do=future_date(44),
			start="Gdynia",
			koniec="Sztokholm",
		)
		self.zgloszenie = Zgloszenie.objects.create(
			imie="Jan",
			nazwisko="Kowalski",
			email="jan@example.com",
			telefon="123456789",
			data_urodzenia=datetime.date(1990, 1, 1),
			rejs=self.rejs,
			rodo=True,
			obecnosc="tak",
		)

	def test_str_representation(self):
		"""Test reprezentacji tekstowej wpłaty."""
		wplata = Wplata.objects.create(zgloszenie=self.zgloszenie, kwota=Decimal("500.00"), rodzaj="wplata")
		self.assertEqual(str(wplata), "Wpłata: 500.00 zł")
