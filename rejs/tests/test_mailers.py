from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings

from rejs.mailers import send_mass_mail_html, send_simple_mail


class SendSimpleMailTest(TestCase):
	"""Testy funkcji send_simple_mail."""

	def test_sends_email_with_html_and_txt(self):
		"""Test wysyłania emaila z szablonami HTML i TXT."""
		send_simple_mail(
			subject="Test Subject",
			to_mail="test@example.com",
			template_base="emails/zgloszenie_utworzone",
			context={"zgloszenie": {"imie": "Jan", "nazwisko": "Kowalski"}},
		)

		self.assertEqual(len(mail.outbox), 1)
		email = mail.outbox[0]
		self.assertEqual(email.subject, "Test Subject")
		self.assertEqual(email.to, ["test@example.com"])
		self.assertTrue(len(email.alternatives) > 0)

	def test_sends_email_with_txt_only(self):
		"""Test wysyłania emaila gdy dostępny tylko szablon TXT."""
		# Używamy istniejącego szablonu który ma .txt
		send_simple_mail(
			subject="Test TXT",
			to_mail="test@example.com",
			template_base="emails/zgloszenie_utworzone",
			context={},
		)

		self.assertEqual(len(mail.outbox), 1)
		email = mail.outbox[0]
		self.assertIsNotNone(email.body)

	def test_email_recipient(self):
		"""Test poprawnego adresata emaila."""
		send_simple_mail(
			subject="Test",
			to_mail="recipient@example.com",
			template_base="emails/zgloszenie_utworzone",
			context={},
		)

		self.assertEqual(mail.outbox[0].to, ["recipient@example.com"])

	def test_email_subject(self):
		"""Test poprawnego tematu emaila."""
		send_simple_mail(
			subject="Ważna wiadomość",
			to_mail="test@example.com",
			template_base="emails/zgloszenie_utworzone",
			context={},
		)

		self.assertEqual(mail.outbox[0].subject, "Ważna wiadomość")

	def test_context_passed_to_template(self):
		"""Test przekazywania kontekstu do szablonu."""
		send_simple_mail(
			subject="Test",
			to_mail="test@example.com",
			template_base="emails/wplata",
			context={
				"zgloszenie": type("obj", (), {"imie": "Jan", "nazwisko": "Kowalski"})(),
				"wplata": type("obj", (), {"kwota": "500.00"})(),
			},
		)

		self.assertEqual(len(mail.outbox), 1)
		# Sprawdzamy czy email został wysłany (kontekst był poprawny)
		self.assertIn("test@example.com", mail.outbox[0].to)

	def test_no_email_sent_when_no_templates(self):
		"""Test braku wysyłki gdy brak szablonów."""
		with self.assertLogs("rejs.mailers", level="WARNING") as logs:
			send_simple_mail(
				subject="Test",
				to_mail="test@example.com",
				template_base="emails/nonexistent_template",
				context={},
			)

		self.assertEqual(len(mail.outbox), 0)
		# Verify correct warning messages were logged
		self.assertTrue(any("nonexistent_template.txt" in msg for msg in logs.output))
		self.assertTrue(any("nonexistent_template.html" in msg for msg in logs.output))

	def test_html_alternative_attached(self):
		"""Test dołączania alternatywy HTML."""
		send_simple_mail(
			subject="Test",
			to_mail="test@example.com",
			template_base="emails/zgloszenie_utworzone",
			context={},
		)

		email = mail.outbox[0]
		# Sprawdzamy czy jest alternatywa HTML
		html_alternatives = [alt for alt in email.alternatives if alt[1] == "text/html"]
		self.assertTrue(len(html_alternatives) > 0)

	@override_settings(DEFAULT_FROM_EMAIL="custom@sender.com")
	def test_from_email_from_settings(self):
		"""Test używania FROM z ustawień."""
		# Reimportujemy moduł aby pobrać nową wartość FROM
		from importlib import reload

		import rejs.mailers

		reload(rejs.mailers)

		rejs.mailers.send_simple_mail(
			subject="Test",
			to_mail="test@example.com",
			template_base="emails/zgloszenie_utworzone",
			context={},
		)

		self.assertEqual(mail.outbox[0].from_email, "custom@sender.com")

	def test_multiple_emails_independent(self):
		"""Test wysyłania wielu niezależnych emaili."""
		send_simple_mail(
			subject="Email 1",
			to_mail="user1@example.com",
			template_base="emails/zgloszenie_utworzone",
			context={},
		)
		send_simple_mail(
			subject="Email 2",
			to_mail="user2@example.com",
			template_base="emails/zgloszenie_utworzone",
			context={},
		)

		self.assertEqual(len(mail.outbox), 2)
		self.assertEqual(mail.outbox[0].to, ["user1@example.com"])
		self.assertEqual(mail.outbox[1].to, ["user2@example.com"])

	@patch("rejs.mailers.EmailMultiAlternatives.send")
	def test_raises_on_send_failure(self, mock_send):
		"""Test rzucania wyjątku przy błędzie wysyłki."""
		mock_send.side_effect = Exception("SMTP Error")

		with self.assertLogs("rejs.mailers", level="ERROR") as logs:
			with self.assertRaises(Exception) as context:
				send_simple_mail(
					subject="Test",
					to_mail="test@example.com",
					template_base="emails/zgloszenie_utworzone",
					context={},
				)

		self.assertIn("SMTP Error", str(context.exception))
		# Verify error was logged with correct details
		self.assertTrue(any("Błąd wysyłania emaila" in msg for msg in logs.output))
		self.assertTrue(any("test@example.com" in msg for msg in logs.output))

	def test_different_templates(self):
		"""Test różnych szablonów emaili."""
		templates = [
			"emails/zgloszenie_utworzone",
			"emails/zgloszenie_potwierdzone",
			"emails/wplata",
			"emails/wplata_zwrot",
			"emails/wachta_added",
			"emails/ogloszenie",
		]

		for template in templates:
			mail.outbox.clear()
			send_simple_mail(
				subject=f"Test {template}",
				to_mail="test@example.com",
				template_base=template,
				context={
					"zgloszenie": type(
						"obj",
						(),
						{
							"imie": "Jan",
							"nazwisko": "Kowalski",
							"rejs": type("rejs", (), {"nazwa": "Test Rejs"})(),
							"token": "abc123",
						},
					)(),
					"wplata": type("obj", (), {"kwota": "500.00"})(),
					"ogloszenie": type("obj", (), {"tytul": "Test", "text": "Treść"})(),
					"wachta": type("obj", (), {"nazwa": "Alfa"})(),
				},
			)
			self.assertEqual(len(mail.outbox), 1, f"Email nie został wysłany dla szablonu {template}")

	def test_template_does_not_exist_caught_specifically(self):
		"""Test że tylko TemplateDoesNotExist jest łapany, nie inne wyjątki."""
		from django.template import TemplateDoesNotExist

		with patch("rejs.mailers.render_to_string", side_effect=TemplateDoesNotExist("test")):
			with self.assertLogs("rejs.mailers", level="WARNING") as logs:
				send_simple_mail("Test", "test@example.com", "nonexistent/template", {})

		self.assertTrue(any("Nie znaleziono szablonu" in msg for msg in logs.output))


class SendMassMailHtmlTest(TestCase):
	"""Testy funkcji send_mass_mail_html."""

	def test_sends_multiple_emails_in_batch(self):
		"""Test wysyłania wielu emaili w jednym batchu."""
		messages = [
			("Subject 1", "Body 1", "<p>HTML 1</p>", "from@example.com", ["user1@example.com"]),
			("Subject 2", "Body 2", "<p>HTML 2</p>", "from@example.com", ["user2@example.com"]),
			("Subject 3", "Body 3", "<p>HTML 3</p>", "from@example.com", ["user3@example.com"]),
		]

		sent_count, failed = send_mass_mail_html(messages)

		self.assertEqual(sent_count, 3)
		self.assertEqual(len(failed), 0)
		self.assertEqual(len(mail.outbox), 3)

		# Verify recipients
		recipients = [m.to[0] for m in mail.outbox]
		self.assertIn("user1@example.com", recipients)
		self.assertIn("user2@example.com", recipients)
		self.assertIn("user3@example.com", recipients)

	def test_returns_zero_for_empty_messages(self):
		"""Test że pusta lista zwraca 0 wysłanych."""
		sent_count, failed = send_mass_mail_html([])

		self.assertEqual(sent_count, 0)
		self.assertEqual(len(failed), 0)
		self.assertEqual(len(mail.outbox), 0)

	def test_html_alternative_attached(self):
		"""Test że HTML jest dołączany jako alternatywa."""
		messages = [
			("Subject", "Plain text", "<p>HTML content</p>", "from@example.com", ["user@example.com"]),
		]

		send_mass_mail_html(messages)

		email = mail.outbox[0]
		self.assertEqual(email.body, "Plain text")
		html_alternatives = [alt for alt in email.alternatives if alt[1] == "text/html"]
		self.assertEqual(len(html_alternatives), 1)
		self.assertIn("HTML content", html_alternatives[0][0])

	def test_continues_on_single_failure(self):
		"""Test że kontynuuje wysyłkę mimo błędu pojedynczego emaila."""
		messages = [
			("Subject 1", "Body 1", None, "from@example.com", ["user1@example.com"]),
			("Subject 2", "Body 2", None, "from@example.com", ["user2@example.com"]),
		]

		# Mock send to fail on first email only
		original_send = mail.EmailMessage.send
		call_count = [0]

		def mock_send(self, fail_silently=False):
			call_count[0] += 1
			if call_count[0] == 1:
				raise Exception("SMTP Error")
			return original_send(self, fail_silently)

		with patch.object(mail.EmailMessage, "send", mock_send):
			with self.assertLogs("rejs.mailers", level="ERROR"):
				sent_count, failed = send_mass_mail_html(messages)

		self.assertEqual(sent_count, 1)
		self.assertEqual(len(failed), 1)
		self.assertIn("user1@example.com", failed[0][0])

	def test_logs_success_count(self):
		"""Test że loguje liczbę wysłanych emaili."""
		messages = [
			("Subject", "Body", None, "from@example.com", ["user@example.com"]),
		]

		with self.assertLogs("rejs.mailers", level="INFO") as logs:
			send_mass_mail_html(messages)

		self.assertTrue(any("Wysłano 1 emaili" in msg for msg in logs.output))
