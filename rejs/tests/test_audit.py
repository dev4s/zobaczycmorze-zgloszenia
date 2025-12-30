from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from rejs.audit import log_audit
from rejs.models import AuditLog


class LogAuditFunctionTest(TestCase):
	"""Testy funkcji log_audit."""

	def setUp(self):
		self.factory = RequestFactory()
		self.user = get_user_model().objects.create_user(
			username="testuser",
			email="test@example.com",
			password="testpass123",
		)

	def test_log_audit_with_request_and_user(self):
		"""Test tworzenia logu z requestem i zalogowanym użytkownikiem."""
		request = self.factory.get("/admin/")
		request.user = self.user
		request.META["REMOTE_ADDR"] = "192.168.1.100"
		request.META["HTTP_USER_AGENT"] = "Mozilla/5.0 Test Browser"

		log = log_audit(
			request=request,
			akcja="odczyt",
			model_name="Dane_Dodatkowe",
			object_id=42,
			object_repr="Jan Kowalski",
			szczegoly="Podgląd danych osobowych",
		)

		self.assertEqual(log.uzytkownik, self.user)
		self.assertEqual(log.akcja, "odczyt")
		self.assertEqual(log.model_name, "Dane_Dodatkowe")
		self.assertEqual(log.object_id, 42)
		self.assertEqual(log.object_repr, "Jan Kowalski")
		self.assertEqual(log.ip_address, "192.168.1.100")
		self.assertEqual(log.user_agent, "Mozilla/5.0 Test Browser")
		self.assertEqual(log.szczegoly, "Podgląd danych osobowych")

	def test_log_audit_without_request(self):
		"""Test tworzenia logu bez requesta (operacja systemowa)."""
		log = log_audit(
			request=None,
			akcja="usuniecie",
			model_name="Dane_Dodatkowe",
			object_id=1,
			szczegoly="Automatyczne usunięcie po 30 dniach",
		)

		self.assertIsNone(log.uzytkownik)
		self.assertIsNone(log.ip_address)
		self.assertEqual(log.user_agent, "")
		self.assertEqual(log.akcja, "usuniecie")
		self.assertEqual(log.szczegoly, "Automatyczne usunięcie po 30 dniach")

	def test_log_audit_with_anonymous_user(self):
		"""Test tworzenia logu z anonimowym użytkownikiem."""
		from django.contrib.auth.models import AnonymousUser

		request = self.factory.get("/")
		request.user = AnonymousUser()
		request.META["REMOTE_ADDR"] = "10.0.0.1"

		log = log_audit(
			request=request,
			akcja="odczyt",
			model_name="Zgloszenie",
		)

		self.assertIsNone(log.uzytkownik)
		self.assertEqual(log.ip_address, "10.0.0.1")

	def test_log_audit_with_x_forwarded_for(self):
		"""Test pobierania IP z nagłówka X-Forwarded-For (proxy)."""
		request = self.factory.get("/")
		request.user = self.user
		request.META["HTTP_X_FORWARDED_FOR"] = "203.0.113.50, 70.41.3.18, 150.172.238.178"
		request.META["REMOTE_ADDR"] = "127.0.0.1"

		log = log_audit(
			request=request,
			akcja="odczyt",
			model_name="Test",
		)

		# Powinien użyć pierwszego IP z X-Forwarded-For
		self.assertEqual(log.ip_address, "203.0.113.50")

	def test_log_audit_truncates_long_user_agent(self):
		"""Test obcinania zbyt długiego User-Agent."""
		request = self.factory.get("/")
		request.user = self.user
		request.META["REMOTE_ADDR"] = "127.0.0.1"
		request.META["HTTP_USER_AGENT"] = "A" * 600

		log = log_audit(
			request=request,
			akcja="odczyt",
			model_name="Test",
		)

		self.assertEqual(len(log.user_agent), 500)

	def test_log_audit_truncates_long_object_repr(self):
		"""Test obcinania zbyt długiej reprezentacji obiektu."""
		log = log_audit(
			request=None,
			akcja="odczyt",
			model_name="Test",
			object_repr="X" * 300,
		)

		self.assertEqual(len(log.object_repr), 200)

	def test_log_audit_returns_audit_log_instance(self):
		"""Test czy funkcja zwraca instancję AuditLog."""
		log = log_audit(
			request=None,
			akcja="utworzenie",
			model_name="Test",
		)

		self.assertIsInstance(log, AuditLog)
		self.assertIsNotNone(log.pk)

	def test_log_audit_all_akcja_types(self):
		"""Test wszystkich typów akcji."""
		akcje = ["odczyt", "utworzenie", "modyfikacja", "usuniecie", "eksport"]

		for akcja in akcje:
			log = log_audit(
				request=None,
				akcja=akcja,
				model_name="Test",
			)
			self.assertEqual(log.akcja, akcja)

	def test_log_audit_empty_object_repr(self):
		"""Test z pustą reprezentacją obiektu."""
		log = log_audit(
			request=None,
			akcja="odczyt",
			model_name="Test",
			object_repr="",
		)

		self.assertEqual(log.object_repr, "")

	def test_log_audit_none_object_repr(self):
		"""Test z None jako reprezentacja obiektu."""
		log = log_audit(
			request=None,
			akcja="odczyt",
			model_name="Test",
			object_repr=None,
		)

		self.assertEqual(log.object_repr, "")

	def test_log_audit_persists_to_database(self):
		"""Test czy log jest zapisywany do bazy danych."""
		initial_count = AuditLog.objects.count()

		log_audit(
			request=None,
			akcja="eksport",
			model_name="Dane_Dodatkowe",
			szczegoly="Eksport do Excel",
		)

		self.assertEqual(AuditLog.objects.count(), initial_count + 1)
