import datetime
from decimal import Decimal

from django.core import mail
from django.test import TestCase

from rejs.models import Ogloszenie, Rejs, Wachta, Wplata, Zgloszenie


# Helper to get future dates for tests
def future_date(days_from_now: int) -> str:
	"""Return a date string N days from today."""
	return (datetime.date.today() + datetime.timedelta(days=days_from_now)).isoformat()


class SignalsTest(TestCase):
	"""Testy sygnałów wysyłających emaile."""

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

	def test_email_sent_on_zgloszenie_create(self):
		"""Test wysyłania emaila przy tworzeniu zgłoszenia."""
		Zgloszenie.objects.create(
			imie="Jan",
			nazwisko="Kowalski",
			email="jan@example.com",
			telefon="123456789",
			data_urodzenia=datetime.date(1990, 1, 1),
			rejs=self.rejs,
			rodo=True,
			obecnosc="tak",
		)
		self.assertEqual(len(mail.outbox), 1)
		self.assertIn("Potwierdzenie zgłoszenia", mail.outbox[0].subject)
		self.assertEqual(mail.outbox[0].to, ["jan@example.com"])

	def test_email_sent_on_status_change_qualified(self):
		"""Test wysyłania emaila przy zmianie statusu na zakwalifikowany."""
		zgloszenie = Zgloszenie.objects.create(
			imie="Jan",
			nazwisko="Kowalski",
			email="jan@example.com",
			telefon="123456789",
			data_urodzenia=datetime.date(1990, 1, 1),
			rejs=self.rejs,
			status=Zgloszenie.STATUS_NIEZAKWALIFIKOWANY,
			rodo=True,
			obecnosc="tak",
		)
		mail.outbox.clear()

		zgloszenie.status = Zgloszenie.STATUS_ZAKWALIFIKOWANY
		zgloszenie.save()

		self.assertEqual(len(mail.outbox), 1)
		self.assertIn("zakwalifikowanie", mail.outbox[0].subject)

	def test_email_sent_on_status_change_odrzucone(self):
		"""Test wysyłania emaila przy zmianie statusu na odrzucone."""
		zgloszenie = Zgloszenie.objects.create(
			imie="Jan",
			nazwisko="Kowalski",
			email="jan@example.com",
			telefon="123456789",
			data_urodzenia=datetime.date(1990, 1, 1),
			rejs=self.rejs,
			status=Zgloszenie.STATUS_NIEZAKWALIFIKOWANY,
			rodo=True,
			obecnosc="tak",
		)
		mail.outbox.clear()

		zgloszenie.status = Zgloszenie.STATUS_ODRZUCONE
		zgloszenie.save()

		self.assertEqual(len(mail.outbox), 1)
		self.assertIn("Odrzucone", mail.outbox[0].subject)

	def test_no_email_on_same_status(self):
		"""Test braku emaila gdy status się nie zmienia."""
		zgloszenie = Zgloszenie.objects.create(
			imie="Jan",
			nazwisko="Kowalski",
			email="jan@example.com",
			telefon="123456789",
			data_urodzenia=datetime.date(1990, 1, 1),
			rejs=self.rejs,
			status=Zgloszenie.STATUS_NIEZAKWALIFIKOWANY,
			rodo=True,
			obecnosc="tak",
		)
		mail.outbox.clear()

		zgloszenie.imie = "Janusz"
		zgloszenie.save()

		self.assertEqual(len(mail.outbox), 0)

	def test_email_sent_on_wachta_assignment(self):
		"""Test wysyłania emaila przy przypisaniu do wachty."""
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
		wachta = Wachta.objects.create(rejs=self.rejs, nazwa="Alfa")
		mail.outbox.clear()

		zgloszenie.wachta = wachta
		zgloszenie.save()

		self.assertEqual(len(mail.outbox), 1)
		self.assertIn("wachty", mail.outbox[0].subject)

	def test_email_sent_on_wplata_create(self):
		"""Test wysyłania emaila przy tworzeniu wpłaty."""
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
		mail.outbox.clear()

		Wplata.objects.create(zgloszenie=zgloszenie, kwota=Decimal("500.00"), rodzaj="wplata")

		self.assertEqual(len(mail.outbox), 1)
		self.assertIn("wpłatę", mail.outbox[0].subject)

	def test_email_sent_on_zwrot_create(self):
		"""Test wysyłania emaila przy tworzeniu zwrotu."""
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
		mail.outbox.clear()

		Wplata.objects.create(zgloszenie=zgloszenie, kwota=Decimal("100.00"), rodzaj="zwrot")

		self.assertEqual(len(mail.outbox), 1)
		self.assertIn("Zwrot", mail.outbox[0].subject)

	def test_email_sent_on_ogloszenie_create(self):
		"""Test wysyłania emaila przy tworzeniu ogłoszenia."""
		zgloszenie1 = Zgloszenie.objects.create(
			imie="Jan",
			nazwisko="Kowalski",
			email="jan@example.com",
			telefon="123456789",
			data_urodzenia=datetime.date(1990, 1, 1),
			rejs=self.rejs,
			rodo=True,
			obecnosc="tak",
		)
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
		mail.outbox.clear()

		Ogloszenie.objects.create(rejs=self.rejs, tytul="Ważne ogłoszenie", text="Treść ogłoszenia")

		self.assertEqual(len(mail.outbox), 2)
		recipients = [m.to[0] for m in mail.outbox]
		self.assertIn("jan@example.com", recipients)
		self.assertIn("anna@example.com", recipients)

	def test_powiadom_o_ogloszeniu_uses_batch_sending(self):
		"""Test że ogłoszenie używa batch sending (wszystkie emaile wysłane)."""
		# Utwórz 3 uczestników
		for i in range(3):
			Zgloszenie.objects.create(
				imie=f"User{i}",
				nazwisko=f"Test{i}",
				email=f"user{i}@example.com",
				telefon=f"12345678{i}",
				data_urodzenia=datetime.date(1990, 1, 1),
				rejs=self.rejs,
				rodo=True,
				obecnosc="tak",
			)
		mail.outbox.clear()

		# Utwórz ogłoszenie - wywołuje sygnał
		Ogloszenie.objects.create(rejs=self.rejs, tytul="Test batch", text="Treść")

		# Wszystkie 3 emaile powinny być wysłane
		self.assertEqual(len(mail.outbox), 3)

	def test_powiadom_o_ogloszeniu_no_error_when_empty(self):
		"""Test że ogłoszenie nie powoduje błędu gdy brak uczestników."""
		# Brak uczestników na tym rejsie
		mail.outbox.clear()

		# Nie powinno rzucić wyjątku
		Ogloszenie.objects.create(rejs=self.rejs, tytul="Test empty", text="Treść")

		# Brak emaili
		self.assertEqual(len(mail.outbox), 0)
