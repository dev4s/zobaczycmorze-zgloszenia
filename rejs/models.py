import uuid
from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms import ValidationError
from django.urls import reverse


class Rejs(models.Model):
    nazwa = models.CharField(max_length=200, null=False, blank=False)
    od = models.DateField(null=False, blank=False, verbose_name="data od")
    do = models.DateField(null=False, blank=False, verbose_name="data do")
    start = models.CharField(
        max_length=200, null=False, blank=False, verbose_name="port początkowy"
    )
    koniec = models.CharField(
        max_length=200, null=False, blank=False, verbose_name="port końcowy"
    )
    cena = models.DecimalField(default=1500, max_digits=10, decimal_places=2)
    zaliczka = models.DecimalField(default=500, max_digits=10, decimal_places=2)
    opis = models.TextField(default="tutaj opis rejsu", blank=False, null=False)

    def __str__(self) -> str:
        return self.nazwa

    @property
    def reszta_do_zaplaty(self):
        return self.cena - self.zaliczka

    class Meta:
        verbose_name = "Rejs"
        verbose_name_plural = "Rejsy"


class Wachta(models.Model):
    rejs = models.ForeignKey(Rejs, on_delete=models.CASCADE, related_name="wachty")
    nazwa = models.CharField(max_length=200)

    class Meta:
        verbose_name = "Wachta"
        verbose_name_plural = "Wachty"

    def __str__(self):
        return f"Wachta {self.nazwa} - {self.rejs}"


class Zgloszenie(models.Model):
    statusy = [
        ("QUALIFIED", "Zakwalifikowany"),
        ("NOT_QUALIFIED", "Niezakwalifikowany"),
        ("ODRZUCONE", "Odrzucone"),
    ]
    wzrok_statusy = [
        ("WIDZI", "widzący"),
        ("NIEWIDOMY", "niewidomy"),
        ("SLABO-WIDZACY", "słabo widzący"),
    ]
    role_pola = [("ZALOGANT", "załogant"), ("OFICER-WACHTY", "oficer wachty")]
    imie = models.CharField(max_length=100, null=False, blank=False)
    nazwisko = models.CharField(max_length=100, null=False, blank=False)
    email = models.EmailField(null=False, blank=False)
    telefon = models.CharField(max_length=15, blank=False, null=False)
    status = models.CharField(max_length=20, choices=statusy, default=statusy[1])
    wzrok = models.CharField(
        max_length=15, choices=wzrok_statusy, default=wzrok_statusy[0]
    )
    rola = models.CharField(max_length=25, default="ZALOGANT", choices=role_pola)
    rejs = models.ForeignKey(Rejs, on_delete=models.CASCADE, related_name="zgloszenia")
    wachta = models.ForeignKey(
        Wachta,
        related_name="czlonkowie",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    @property
    def suma_wplat(self):
        # wynik = self.wplaty.aggregate(total=Sum("kwota"))
        # return wynik['total'] or 0
        suma_wplat = sum(w.kwota for w in self.wplaty.filter(rodzaj="wplata"))
        suma_zwrotow = sum(w.kwota for w in self.wplaty.filter(rodzaj="zwrot"))
        return suma_wplat - suma_zwrotow

    @property
    def rejs_cena(self):
        return self.rejs.cena

    @property
    def do_zaplaty(self):
        return self.rejs.cena - self.suma_wplat

    def __str__(self):
        return f"{self.imie} {self.nazwisko}"

    def clean(self):
        if self.wachta and self.wachta.rejs_id != self.rejs_id:
            raise ValidationError(
                "Wachta musi należeć do tego samego rejsu co zgłoszenie."
            )

    def get_absolute_url(self):
        return reverse("zgloszenie_details", kwargs={"token": self.token})

    class Meta:
        verbose_name = "Zgłoszenie"
        verbose_name_plural = "Zgłoszenia"


class Wplata(models.Model):
    rodzaje = [("wplata", "Wpłata"), ("zwrot", "Zwrot")]
    kwota = models.DecimalField(
        default=0, blank=False, null=False, max_digits=10, decimal_places=2
    )
    data = models.DateTimeField(auto_now_add=True)
    rodzaj = models.CharField(max_length=7, default=rodzaje[1], choices=rodzaje)
    zgloszenie = models.ForeignKey(
        Zgloszenie,
        related_name="wplaty",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "wpłata"
        verbose_name_plural = "wpłaty"

    def __str__(self):
        return f"Wpłata: {self.kwota} zł"


class Ogloszenie(models.Model):
    rejs = models.ForeignKey(Rejs, on_delete=models.CASCADE, related_name="ogloszenia")
    data = models.DateTimeField(auto_now_add=True)
    tytul = models.CharField(
        default="nowe ogłoszenie",
        max_length=100,
        null=False,
        blank=False,
        verbose_name="tytuł",
    )
    text = models.TextField(default="krótka informacja o rejsie", verbose_name="tekst")

    class Meta:
        verbose_name = "ogłoszenie"
        verbose_name_plural = "ogłoszenia"

    def __str__(self):
        return self.tytul
