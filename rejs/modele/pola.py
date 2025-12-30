"""
Niestandardowe pola modeli Django.
"""

from cryptography.fernet import Fernet
from django.conf import settings
from django.db import models

fernet = Fernet(settings.DJANGO_FIELD_ENCRYPTION_KEY.encode())


class EncryptedTextField(models.TextField):
	"""Pole tekstowe z szyfrowaniem Fernet."""

	def from_db_value(self, value, expression, connection):
		if value is None:
			return value
		return fernet.decrypt(value.encode()).decode()

	def get_prep_value(self, value):
		if value is None:
			return value
		return fernet.encrypt(value.encode()).decode()
