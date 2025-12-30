"""
Model logów audytu dla zgodności z RODO.
"""

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


class AuditLog(models.Model):
	"""
	Model przechowujący logi dostępu do danych wrażliwych.

	Zgodnie z Art. 30 RODO - rejestr czynności przetwarzania.
	"""

	AKCJA_CHOICES = [
		("odczyt", "Odczyt danych"),
		("utworzenie", "Utworzenie danych"),
		("modyfikacja", "Modyfikacja danych"),
		("usuniecie", "Usunięcie danych"),
		("eksport", "Eksport danych"),
	]

	timestamp = models.DateTimeField(default=timezone.now, verbose_name="Data i czas", db_index=True)
	uzytkownik = models.ForeignKey(
		get_user_model(),
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		verbose_name="Użytkownik",
		related_name="audit_logs",
	)
	akcja = models.CharField(max_length=20, choices=AKCJA_CHOICES, verbose_name="Akcja")
	model_name = models.CharField(max_length=100, verbose_name="Model")
	object_id = models.PositiveIntegerField(verbose_name="ID obiektu", null=True, blank=True)
	object_repr = models.CharField(max_length=200, verbose_name="Reprezentacja obiektu", blank=True)
	ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Adres IP")
	user_agent = models.TextField(blank=True, verbose_name="User Agent")
	szczegoly = models.TextField(blank=True, verbose_name="Szczegóły operacji")

	class Meta:
		app_label = "rejs"
		verbose_name = "Log audytu"
		verbose_name_plural = "Logi audytu"
		ordering = ["-timestamp"]
		indexes = [
			models.Index(fields=["model_name", "object_id"]),
			models.Index(fields=["uzytkownik", "timestamp"]),
		]

	def __str__(self):
		user_str = self.uzytkownik.username if self.uzytkownik else "System"
		return f"{self.timestamp:%Y-%m-%d %H:%M} | {user_str} | {self.get_akcja_display()} | {self.model_name}"
