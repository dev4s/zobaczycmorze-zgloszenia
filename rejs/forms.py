from django import forms

from .models import Dane_Dodatkowe, Zgloszenie
from .walidatory import kod_pocztowy_validator, telefon_validator, validate_pesel


class AccessibleFormMixin:
	"""Mixin dodający atrybuty ARIA dla dostępności formularzy."""

	def _setup_aria_attributes(self):
		"""Konfiguruje atrybuty aria-describedby i aria-invalid dla pól formularza."""
		for field_name, field in self.fields.items():
			describedby = []
			if field.help_text:
				describedby.append(f"id_{field_name}-hint")
			if self.errors.get(field_name):
				describedby.append(f"id_{field_name}-error")
				field.widget.attrs["aria-invalid"] = "true"
			if describedby:
				field.widget.attrs["aria-describedby"] = " ".join(describedby)


class ZgloszenieForm(AccessibleFormMixin, forms.ModelForm):
	class Meta:
		model = Zgloszenie
		fields = [
			"imie",
			"nazwisko",
			"email",
			"telefon",
			"data_urodzenia",
			"adres",
			"kod_pocztowy",
			"miejscowosc",
			"wzrok",
			"obecnosc",
			"rodo",
		]
		labels = {
			"imie": "Imię",
			"nazwisko": "Nazwisko",
			"email": "Adres e-mail",
			"telefon": "Numer telefonu",
			"data_urodzenia": "Data urodzenia",
			"adres": "Adres",
			"kod_pocztowy": "Kod pocztowy",
			"miejscowosc": "Miejscowość",
			"wzrok": "Status wzroku",
			"obecnosc": "Udział w poprzednich rejsach",
			"rodo": "Wyrażam zgodę na przetwarzanie moich danych osobowych zgodnie z polityką prywatności Zobaczyć Morze",
		}
		help_texts = {
			"telefon": "Wpisz 9 cyfr numeru (bez prefiksu +48)",
			"kod_pocztowy": "Format: XX-XXX (np. 00-001)",
			"wzrok": "Wybierz opcję najbliższą Twojej sytuacji",
			"obecnosc": "Czy brałeś/aś już udział w rejsach Zobaczyć Morze?",
		}
		widgets = {
			"imie": forms.TextInput(
				attrs={
					"autocomplete": "given-name",
					"aria-required": "true",
				}
			),
			"nazwisko": forms.TextInput(
				attrs={
					"autocomplete": "family-name",
					"aria-required": "true",
				}
			),
			"email": forms.EmailInput(
				attrs={
					"autocomplete": "email",
					"aria-required": "true",
				}
			),
			"telefon": forms.TextInput(
				attrs={
					"autocomplete": "tel",
					"inputmode": "numeric",
					"aria-required": "true",
					"maxlength": "11",
					"pattern": r"\d{3}\s?\d{3}\s?\d{3}",
					"title": "9 cyfr numeru telefonu",
				}
			),
			"data_urodzenia": forms.DateInput(
				attrs={
					"type": "date",
					"autocomplete": "bday",
					"aria-required": "true",
				},
			),
			"adres": forms.TextInput(
				attrs={
					"autocomplete": "street-address",
					"aria-required": "true",
				}
			),
			"kod_pocztowy": forms.TextInput(
				attrs={
					"autocomplete": "postal-code",
					"inputmode": "numeric",
					"aria-required": "true",
					"maxlength": "6",
					"pattern": r"\d{2}-\d{3}",
					"title": "Format: XX-XXX (np. 00-001)",
				}
			),
			"miejscowosc": forms.TextInput(
				attrs={
					"autocomplete": "address-level2",
					"aria-required": "true",
				}
			),
			"wzrok": forms.Select(
				attrs={
					"aria-required": "true",
				}
			),
			"obecnosc": forms.Select(
				attrs={
					"aria-required": "true",
				}
			),
			"rodo": forms.CheckboxInput(
				attrs={
					"aria-required": "true",
				}
			),
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._setup_aria_attributes()

	def clean(self):
		cleaned = super().clean()
		imie = cleaned.get("imie")
		nazwisko = cleaned.get("nazwisko")
		email = cleaned.get("email")

		if not (imie and nazwisko and email):
			return cleaned

		rejs = self.initial.get("rejs") or self.instance.rejs

		if rejs:
			istnieje = Zgloszenie.objects.filter(
				rejs=rejs,
				imie__iexact=imie,
				nazwisko__iexact=nazwisko,
				email__iexact=email,
			).exists()

			if istnieje:
				raise forms.ValidationError("Na ten rejs istnieje już zgłoszenie dla tej osoby.")

		return cleaned

	def clean_telefon(self):
		telefon = self.cleaned_data.get("telefon", "")
		# Usuń wszystkie znaki oprócz cyfr
		cleaned = "".join(c for c in telefon if c.isdigit())
		# Sprawdź czy mamy dokładnie 9 cyfr
		if len(cleaned) != 9:
			raise forms.ValidationError("Numer telefonu musi zawierać dokładnie 9 cyfr.")
		# Dodaj prefiks +48 i zapisz
		return f"+48{cleaned}"

	def clean_kod_pocztowy(self):
		kod = self.cleaned_data.get("kod_pocztowy", "").strip()

		# normalizacja: usuń spacje
		kod = kod.replace(" ", "")

		# jeśli użytkownik wpisał 5 cyfr (np. 00123) → zamień na 00-123
		if kod.isdigit() and len(kod) == 5:
			kod = f"{kod[:2]}-{kod[2:]}"

		# walidacja właściwa
		kod_pocztowy_validator(kod)

		return kod


class Dane_DodatkoweForm(AccessibleFormMixin, forms.ModelForm):
	class Meta:
		model = Dane_Dodatkowe
		fields = ["poz1", "poz2", "poz3", "zgoda_dane_wrazliwe"]
		labels = {
			"poz1": "PESEL",
			"poz2": "Typ dokumentu",
			"poz3": "Numer dokumentu",
			"zgoda_dane_wrazliwe": "Zgoda na przetwarzanie danych",
		}
		help_texts = {
			"poz1": "Podaj swój numer PESEL (11 cyfr).",
			"poz2": "Wybierz dokument, który zgodnie z procedurami oddasz przy zaokrętowaniu.",
			"poz3": "Podaj numer dokumentu, który oddasz przy zaokrętowaniu.",
			"zgoda_dane_wrazliwe": "Wyrażam zgodę na przetwarzanie moich danych osobowych (PESEL, numer dokumentu) "
			"w celu realizacji procedur zaokrętowania zgodnie z wymogami kapitana. "
			"Dane zostaną usunięte w ciągu 30 dni po zakończeniu rejsu.",
		}
		widgets = {
			"poz1": forms.TextInput(
				attrs={
					"aria-required": "true",
					"inputmode": "numeric",
					"maxlength": "11",
					"pattern": "[0-9]{11}",
				}
			),
			"poz2": forms.Select(
				attrs={
					"aria-required": "true",
				}
			),
			"poz3": forms.TextInput(
				attrs={
					"aria-required": "true",
				}
			),
			"zgoda_dane_wrazliwe": forms.CheckboxInput(
				attrs={
					"aria-required": "true",
				}
			),
		}

	def clean_poz1(self):
		pesel = self.cleaned_data.get("poz1", "")
		return validate_pesel(pesel)

	def clean_zgoda_dane_wrazliwe(self):
		zgoda = self.cleaned_data.get("zgoda_dane_wrazliwe")
		if not zgoda:
			raise forms.ValidationError("Musisz wyrazić zgodę na przetwarzanie danych wrażliwych, aby kontynuować.")
		return zgoda

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._setup_aria_attributes()
