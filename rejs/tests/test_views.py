import datetime
import uuid

from django.test import Client, TestCase
from django.urls import reverse

from rejs.forms import ZgloszenieForm
from rejs.models import Rejs, Zgloszenie


# Helper to get future dates for tests
def future_date(days_from_now: int) -> str:
	"""Return a date string N days from today."""
	return (datetime.date.today() + datetime.timedelta(days=days_from_now)).isoformat()


class IndexViewTest(TestCase):
	"""Testy widoku listy rejsów."""

	def setUp(self):
		self.client = Client()

	def test_index_returns_200(self):
		"""Test czy strona główna zwraca status 200."""
		response = self.client.get(reverse("index"))
		self.assertEqual(response.status_code, 200)

	def test_index_uses_correct_template(self):
		"""Test czy używany jest prawidłowy szablon."""
		response = self.client.get(reverse("index"))
		self.assertTemplateUsed(response, "rejs/index.html")

	def test_index_displays_rejsy(self):
		"""Test czy rejsy są wyświetlane (tylko aktywne, przyszłe)."""
		Rejs.objects.create(
			nazwa="Rejs wakacyjny",
			od=future_date(30),
			do=future_date(44),
			start="Gdynia",
			koniec="Sztokholm",
			aktywna_rekrutacja=True,
		)
		response = self.client.get(reverse("index"))
		self.assertContains(response, "Rejs wakacyjny")

	def test_index_empty_rejsy(self):
		"""Test strony gdy brak rejsów."""
		response = self.client.get(reverse("index"))
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.context["rejsy"]), 0)

	def test_index_rejsy_ordered_by_date(self):
		"""Test czy rejsy są posortowane po dacie."""
		rejs2 = Rejs.objects.create(
			nazwa="Rejs późniejszy",
			od=future_date(60),
			do=future_date(74),
			start="Gdańsk",
			koniec="Helsinki",
			aktywna_rekrutacja=True,
		)
		rejs1 = Rejs.objects.create(
			nazwa="Rejs wcześniejszy",
			od=future_date(30),
			do=future_date(44),
			start="Gdynia",
			koniec="Sztokholm",
			aktywna_rekrutacja=True,
		)
		response = self.client.get(reverse("index"))
		rejsy = list(response.context["rejsy"])
		self.assertEqual(rejsy[0], rejs1)
		self.assertEqual(rejsy[1], rejs2)

	def test_index_hides_inactive_rekrutacja(self):
		"""Test czy rejsy z nieaktywną rekrutacją są ukryte."""
		Rejs.objects.create(
			nazwa="Rejs nieaktywny",
			od=future_date(30),
			do=future_date(44),
			start="Gdynia",
			koniec="Sztokholm",
			aktywna_rekrutacja=False,
		)
		response = self.client.get(reverse("index"))
		self.assertEqual(len(response.context["rejsy"]), 0)

	def test_index_hides_past_rejsy(self):
		"""Test czy przeszłe rejsy są ukryte."""
		Rejs.objects.create(
			nazwa="Rejs przeszły",
			od="2020-07-01",
			do="2020-07-14",
			start="Gdynia",
			koniec="Sztokholm",
			aktywna_rekrutacja=True,
		)
		response = self.client.get(reverse("index"))
		self.assertEqual(len(response.context["rejsy"]), 0)


class ZgloszenieCreateViewTest(TestCase):
	"""Testy widoku tworzenia zgłoszenia."""

	def setUp(self):
		self.client = Client()
		self.rejs = Rejs.objects.create(
			nazwa="Rejs testowy",
			od=future_date(30),
			do=future_date(44),
			start="Gdynia",
			koniec="Sztokholm",
			aktywna_rekrutacja=True,
		)

	def test_get_form(self):
		"""Test wyświetlania formularza."""
		response = self.client.get(reverse("zgloszenie_utworz", kwargs={"rejs_id": self.rejs.id}))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, "rejs/zgloszenie_form.html")
		self.assertIsInstance(response.context["form"], ZgloszenieForm)

	def test_get_form_nonexistent_rejs(self):
		"""Test formularza dla nieistniejącego rejsu."""
		response = self.client.get(reverse("zgloszenie_utworz", kwargs={"rejs_id": 99999}))
		self.assertEqual(response.status_code, 404)

	def test_get_form_inactive_rejs_redirects(self):
		"""Test że formularz dla rejsu z nieaktywną rekrutacją przekierowuje na index."""
		self.rejs.aktywna_rekrutacja = False
		self.rejs.save()
		response = self.client.get(reverse("zgloszenie_utworz", kwargs={"rejs_id": self.rejs.id}))
		self.assertRedirects(response, reverse("index"))

	def test_get_form_past_rejs_redirects(self):
		"""Test że formularz dla przeszłego rejsu przekierowuje na index."""
		self.rejs.od = "2020-07-01"
		self.rejs.do = "2020-07-14"
		self.rejs.save()
		response = self.client.get(reverse("zgloszenie_utworz", kwargs={"rejs_id": self.rejs.id}))
		self.assertRedirects(response, reverse("index"))

	def test_post_valid_form(self):
		"""Test wysłania poprawnego formularza."""
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
		response = self.client.post(reverse("zgloszenie_utworz", kwargs={"rejs_id": self.rejs.id}), data)
		self.assertEqual(Zgloszenie.objects.count(), 1)
		zgloszenie = Zgloszenie.objects.first()
		self.assertRedirects(
			response,
			reverse("zgloszenie_details", kwargs={"token": zgloszenie.token}),
		)

	def test_post_invalid_form_missing_fields(self):
		"""Test wysłania formularza z brakującymi polami."""
		data = {
			"imie": "Jan",
		}
		response = self.client.post(reverse("zgloszenie_utworz", kwargs={"rejs_id": self.rejs.id}), data)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(Zgloszenie.objects.count(), 0)
		self.assertFormError(response.context["form"], "nazwisko", "To pole jest wymagane.")

	def test_post_invalid_telefon(self):
		"""Test wysłania formularza z nieprawidłowym telefonem."""
		data = {
			"imie": "Jan",
			"nazwisko": "Kowalski",
			"email": "jan@example.com",
			"telefon": "abc",
			"data_urodzenia": "1990-01-01",
			"adres": "ul. Testowa 1",
			"kod_pocztowy": "00-001",
			"miejscowosc": "Warszawa",
			"wzrok": "NIEWIDOMY",
			"obecnosc": "tak",
			"rodo": True,
		}
		response = self.client.post(reverse("zgloszenie_utworz", kwargs={"rejs_id": self.rejs.id}), data)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(Zgloszenie.objects.count(), 0)


class ZgloszenieDetailsViewTest(TestCase):
	"""Testy widoku szczegółów zgłoszenia."""

	def setUp(self):
		self.client = Client()
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

	def test_get_details_by_token(self):
		"""Test wyświetlania szczegółów po tokenie."""
		response = self.client.get(reverse("zgloszenie_details", kwargs={"token": self.zgloszenie.token}))
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, "rejs/zgloszenie_details.html")
		self.assertEqual(response.context["zgloszenie"], self.zgloszenie)

	def test_invalid_token_returns_404(self):
		"""Test 404 dla nieprawidłowego tokena."""
		fake_token = uuid.uuid4()
		response = self.client.get(reverse("zgloszenie_details", kwargs={"token": fake_token}))
		self.assertEqual(response.status_code, 404)

	def test_details_contains_personal_data(self):
		"""Test czy szczegóły zawierają dane osobowe."""
		response = self.client.get(reverse("zgloszenie_details", kwargs={"token": self.zgloszenie.token}))
		self.assertContains(response, "Jan")
		self.assertContains(response, "Kowalski")
