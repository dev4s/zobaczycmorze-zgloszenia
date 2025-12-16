from django import forms
from django.core.validators import RegexValidator

from .models import Zgloszenie

telefon_validator = RegexValidator(
    regex=r"^\+?\d{9,15}$",
    message="Numer telefonu musi zawierać 9-15 cyfr, opcjonalnie z + na początku.",
)


class ZgloszenieForm(forms.ModelForm):
    class Meta:
        model = Zgloszenie
        fields = ["imie", "nazwisko", "email", "telefon", "wzrok"]
        labels = {
            "imie": "Imię",
            "nazwisko": "Nazwisko",
            "email": "Adres e-mail",
            "telefon": "Numer telefonu",
            "wzrok": "Status wzroku",
        }
        help_texts = {
            "telefon": "Format: 9-15 cyfr, np. 123456789 lub +48123456789",
            "wzrok": "Wybierz opcję najbliższą Twojej sytuacji",
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
                    "inputmode": "tel",
                    "aria-required": "true",
                }
            ),
            "wzrok": forms.Select(
                attrs={
                    "aria-required": "true",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            describedby = []
            if field.help_text:
                describedby.append(f"id_{field_name}-hint")
            if self.errors.get(field_name):
                describedby.append(f"id_{field_name}-error")
                field.widget.attrs["aria-invalid"] = "true"
            if describedby:
                field.widget.attrs["aria-describedby"] = " ".join(describedby)

    def clean_telefon(self):
        telefon = self.cleaned_data.get("telefon", "")
        cleaned = (
            telefon.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        )
        telefon_validator(cleaned)
        return cleaned
