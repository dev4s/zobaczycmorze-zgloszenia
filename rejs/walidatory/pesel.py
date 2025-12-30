"""
Walidator numeru PESEL.

Implementuje algorytm sumy kontrolnej zgodny z polskimi przepisami.
"""

from django.core.exceptions import ValidationError


def validate_pesel(pesel: str) -> str:
	"""
	Waliduje numer PESEL zgodnie z polskim algorytmem sumy kontrolnej.

	Algorytm:
	1. PESEL musi mieć dokładnie 11 cyfr
	2. Suma kontrolna: każda cyfra mnożona przez wagę [1,3,7,9,1,3,7,9,1,3,1]
	3. Suma modulo 10 musi równać się 0

	Args:
		pesel: Numer PESEL do walidacji

	Returns:
		Oczyszczony numer PESEL (bez spacji i myślników)

	Raises:
		ValidationError: Gdy PESEL jest nieprawidłowy
	"""
	if not pesel:
		raise ValidationError("Numer PESEL jest wymagany.")

	cleaned = pesel.strip().replace(" ", "").replace("-", "")

	if len(cleaned) != 11:
		raise ValidationError("Numer PESEL musi składać się z dokładnie 11 cyfr.")

	if not cleaned.isdigit():
		raise ValidationError("Numer PESEL może zawierać tylko cyfry.")

	wagi = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3, 1]
	suma = sum(int(cyfra) * waga for cyfra, waga in zip(cleaned, wagi))

	if suma % 10 != 0:
		raise ValidationError("Nieprawidłowy numer PESEL - błędna suma kontrolna.")

	return cleaned
