import datetime

from django import forms
from django.core import mail
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from rejs.models import Rejs, Wachta, Zgloszenie
from rejs.serwisy.wachty import SerwisWacht


# Helper to get future dates for tests
def future_date(days_from_now: int) -> datetime.date:
	"""Return a date N days from today."""
	return datetime.date.today() + datetime.timedelta(days=days_from_now)


class SerwisWachtTest(TestCase):
	"""Testy SerwisWacht."""

	def setUp(self):
		self.serwis = SerwisWacht()
		self.rejs = Rejs.objects.create(
			nazwa="Rejs testowy",
			od=future_date(30),
			do=future_date(44),
			start="Gdynia",
			koniec="Sztokholm",
		)
		self.wachta = Wachta.objects.create(rejs=self.rejs, nazwa="Alfa")
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

	def test_przypisz_czlonka(self):
		"""Test przypisywania członka do wachty."""
		self.serwis.przypisz_czlonka(self.wachta, self.zgloszenie)

		self.zgloszenie.refresh_from_db()
		self.assertEqual(self.zgloszenie.wachta, self.wachta)

	def test_przypisz_czlonka_inny_rejs_blad(self):
		"""Test błędu przy przypisywaniu członka z innego rejsu."""
		inny_rejs = Rejs.objects.create(
			nazwa="Inny rejs",
			od=future_date(60),
			do=future_date(74),
			start="Gdańsk",
			koniec="Helsinki",
		)
		zgloszenie_inny = Zgloszenie.objects.create(
			imie="Anna",
			nazwisko="Nowak",
			email="anna@example.com",
			telefon="987654321",
			data_urodzenia=datetime.date(1991, 2, 2),
			rejs=inny_rejs,
			rodo=True,
			obecnosc="tak",
		)

		with self.assertRaises(forms.ValidationError):
			self.serwis.przypisz_czlonka(self.wachta, zgloszenie_inny)

	def test_usun_czlonka(self):
		"""Test usuwania członka z wachty."""
		self.zgloszenie.wachta = self.wachta
		self.zgloszenie.save()

		self.serwis.usun_czlonka(self.zgloszenie)

		self.zgloszenie.refresh_from_db()
		self.assertIsNone(self.zgloszenie.wachta)

	def test_pobierz_dostepnych_czlonkow(self):
		"""Test pobierania dostępnych członków."""
		# Jeden bez wachty, jeden z wachtą
		zgloszenie2 = Zgloszenie.objects.create(
			imie="Anna",
			nazwisko="Nowak",
			email="anna@example.com",
			telefon="987654321",
			data_urodzenia=datetime.date(1991, 2, 2),
			rejs=self.rejs,
			rodo=True,
			obecnosc="tak",
			wachta=self.wachta,
		)

		dostepni = self.serwis.pobierz_dostepnych_czlonkow(self.rejs)

		self.assertEqual(dostepni.count(), 1)
		self.assertIn(self.zgloszenie, dostepni)
		self.assertNotIn(zgloszenie2, dostepni)

	def test_aktualizuj_czlonkow_wachty_dodaj(self):
		"""Test aktualizacji - dodanie nowych członków."""
		self.serwis.aktualizuj_czlonkow_wachty(self.wachta, [self.zgloszenie])

		self.zgloszenie.refresh_from_db()
		self.assertEqual(self.zgloszenie.wachta, self.wachta)

	def test_aktualizuj_czlonkow_wachty_usun(self):
		"""Test aktualizacji - usunięcie członków."""
		self.zgloszenie.wachta = self.wachta
		self.zgloszenie.save()

		self.serwis.aktualizuj_czlonkow_wachty(self.wachta, [])

		self.zgloszenie.refresh_from_db()
		self.assertIsNone(self.zgloszenie.wachta)

	def test_aktualizuj_czlonkow_wachty_zamiana(self):
		"""Test aktualizacji - zamiana członków."""
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

		# Najpierw przypisz pierwszego
		self.zgloszenie.wachta = self.wachta
		self.zgloszenie.save()

		# Zamień na drugiego
		self.serwis.aktualizuj_czlonkow_wachty(self.wachta, [zgloszenie2])

		self.zgloszenie.refresh_from_db()
		zgloszenie2.refresh_from_db()

		self.assertIsNone(self.zgloszenie.wachta)
		self.assertEqual(zgloszenie2.wachta, self.wachta)

	def _create_zgloszenie(self, name_suffix):
		"""Helper do tworzenia zgłoszeń testowych."""
		return Zgloszenie.objects.create(
			imie=f"Test{name_suffix}",
			nazwisko=f"User{name_suffix}",
			email=f"test{name_suffix}@example.com",
			telefon=f"12345678{name_suffix}",
			data_urodzenia=datetime.date(1990, 1, 1),
			rejs=self.rejs,
			rodo=True,
			obecnosc="tak",
		)

	def test_aktualizuj_czlonkow_wachty_query_count(self):
		"""Test że aktualizuj_czlonkow_wachty używa stałej liczby zapytań (bulk_update)."""
		# Wyczyść outbox przed testem (setUp tworzy zgloszenie które wysyła email)
		mail.outbox.clear()

		# Utwórz 5 członków
		members = [self._create_zgloszenie(str(i)) for i in range(5)]
		mail.outbox.clear()  # Wyczyść emaile z tworzenia zgłoszeń

		with CaptureQueriesContext(connection) as context:
			self.serwis.aktualizuj_czlonkow_wachty(self.wachta, members)

		# Max ~4 zapytania: fetch current + bulk add (+ ewentualnie savepoint)
		# Z N+1 bugiem byłoby 1 + 5 = 6+ zapytań
		self.assertLess(len(context), 6, f"Za dużo zapytań: {len(context)}")

	def test_aktualizuj_czlonkow_wachty_no_emails_sent(self):
		"""Test że bulk update nie wysyła indywidualnych emaili (omija sygnały)."""
		# Wyczyść outbox
		mail.outbox.clear()

		# Utwórz członków (to wysyła emaile o utworzeniu)
		members = [self._create_zgloszenie(str(i)) for i in range(3)]
		mail.outbox.clear()  # Wyczyść emaile z tworzenia

		# Bulk update nie powinien wysyłać emaili o przypisaniu do wachty
		self.serwis.aktualizuj_czlonkow_wachty(self.wachta, members)

		# Brak emaili - bulk_update omija sygnały
		self.assertEqual(len(mail.outbox), 0)
