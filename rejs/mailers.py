import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.template import TemplateDoesNotExist
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

FROM = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@zobaczyc.morze")


def send_simple_mail(subject, to_mail, template_base, context):
	"""
	Wysyła emaila w formacie HTML i TXT jako fallback.
	Wymaga template_base.html i/lub template_base.txt
	"""
	txt_content = None
	html_content = None

	try:
		txt_content = render_to_string(template_base + ".txt", context)
	except TemplateDoesNotExist:
		logger.warning("Nie znaleziono szablonu %s.txt", template_base)

	try:
		html_content = render_to_string(template_base + ".html", context)
	except TemplateDoesNotExist:
		logger.warning("Nie znaleziono szablonu %s.html", template_base)

	if not txt_content and not html_content:
		logger.error("Brak szablonów email dla %s - email nie zostanie wysłany", template_base)
		return

	logger.debug("Wysyłanie emaila do %s: %s", to_mail, subject)

	email = EmailMultiAlternatives(
		subject=subject,
		body=txt_content or "",
		from_email=FROM,
		to=[to_mail],
	)
	if html_content:
		email.attach_alternative(html_content, "text/html")

	try:
		email.send(fail_silently=False)
		logger.info("Email wysłany do %s: %s", to_mail, subject)
	except Exception:
		logger.exception("Błąd wysyłania emaila do %s", to_mail)
		raise


def send_mass_mail_html(messages):
	"""
	Wysyła wiele emaili w jednym połączeniu SMTP.
	Kontynuuje wysyłkę nawet jeśli pojedynczy email zawiedzie.

	Args:
		messages: Lista krotek (subject, txt_content, html_content, from_email, recipient_list)

	Returns:
		Tuple (sent_count, failed_emails) - liczba wysłanych i lista nieudanych
	"""
	connection = get_connection()
	sent_count = 0
	failed_emails = []

	try:
		connection.open()
		for subject, txt_content, html_content, from_email, recipient_list in messages:
			try:
				email = EmailMultiAlternatives(
					subject=subject,
					body=txt_content or "",
					from_email=from_email,
					to=recipient_list,
					connection=connection,
				)
				if html_content:
					email.attach_alternative(html_content, "text/html")
				email.send()
				sent_count += 1
				logger.debug("Email wysłany do %s: %s", recipient_list, subject)
			except Exception as e:
				logger.error("Błąd wysyłania do %s: %s", recipient_list, e)
				failed_emails.append((recipient_list, str(e)))
	finally:
		connection.close()

	if sent_count > 0:
		logger.info("Wysłano %d emaili zbiorczych", sent_count)
	if failed_emails:
		logger.warning("Nie udało się wysłać %d emaili", len(failed_emails))

	return sent_count, failed_emails
