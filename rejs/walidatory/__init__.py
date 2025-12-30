"""
Moduł walidatorów dla aplikacji rejs.

Zawiera walidatory dla:
- PESEL (walidatory.pesel)
- Telefon, kod pocztowy (walidatory.podstawowe)
"""

from .pesel import validate_pesel
from .podstawowe import kod_pocztowy_validator, telefon_validator

__all__ = [
	"validate_pesel",
	"telefon_validator",
	"kod_pocztowy_validator",
]
