"""
Modele związane z komunikacją (ogłoszenia).
"""

from django.db import models

from rejs.modele.rejs import Rejs


class Ogloszenie(models.Model):
	rejs = models.ForeignKey(Rejs, on_delete=models.CASCADE, related_name="ogloszenia")
	data = models.DateTimeField(auto_now_add=True)
	tytul = models.CharField(
		default="nowe ogłoszenie",
		max_length=100,
		null=False,
		blank=False,
		verbose_name="Tytuł",
	)
	text = models.TextField(default="krótka informacja o rejsie", verbose_name="Tekst")

	class Meta:
		app_label = "rejs"
		verbose_name = "Ogłoszenie"
		verbose_name_plural = "Ogłoszenia"

	def __str__(self):
		return self.tytul
