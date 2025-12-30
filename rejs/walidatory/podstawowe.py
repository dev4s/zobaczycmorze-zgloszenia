"""
Podstawowe walidatory dla pól formularzy.

Zawiera walidatory dla:
- Numer telefonu
- Kod pocztowy
"""

from django.core.validators import RegexValidator

telefon_validator = RegexValidator(
	regex=r"^\+?\d{9,15}$",
	message="Numer telefonu musi zawierać 9-15 cyfr, opcjonalnie z + na początku.",
)

kod_pocztowy_validator = RegexValidator(
	regex=r"^\d{2}-\d{3}$",
	message="Kod pocztowy musi mieć format XX-XXX (np. 00-001).",
)
