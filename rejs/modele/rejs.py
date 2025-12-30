"""
Modele związane z rejsami i wachtami.
"""

from django.db import models
from django.forms import ValidationError


class Rejs(models.Model):
	nazwa = models.CharField(max_length=200, null=False, blank=False)
	od = models.DateField(null=False, blank=False, verbose_name="Data od")
	do = models.DateField(null=False, blank=False, verbose_name="Data do")
	start = models.CharField(max_length=200, null=False, blank=False, verbose_name="Port początkowy")
	koniec = models.CharField(max_length=200, null=False, blank=False, verbose_name="Port końcowy")
	cena = models.DecimalField(default=1500, max_digits=10, decimal_places=2)
	zaliczka = models.DecimalField(default=500, max_digits=10, decimal_places=2)
	opis = models.TextField(default="tutaj opis rejsu", blank=False, null=False)
	aktywna_rekrutacja = models.BooleanField(default=True, verbose_name="Aktywna rekrutacja")

	def __str__(self) -> str:
		return self.nazwa

	@property
	def reszta_do_zaplaty(self):
		return self.cena - self.zaliczka

	def clean(self):
		super().clean()
		if self.od and self.do and self.od > self.do:
			raise ValidationError({"od": "Data rozpoczęcia nie może być późniejsza niż data zakończenia."})

	class Meta:
		app_label = "rejs"
		verbose_name = "Rejs"
		verbose_name_plural = "Rejsy"


class Wachta(models.Model):
	rejs = models.ForeignKey(Rejs, on_delete=models.CASCADE, related_name="wachty")
	nazwa = models.CharField(max_length=200)

	class Meta:
		app_label = "rejs"
		verbose_name = "Wachta"
		verbose_name_plural = "Wachty"

	def __str__(self):
		return f"Wachta {self.nazwa} - {self.rejs}"
