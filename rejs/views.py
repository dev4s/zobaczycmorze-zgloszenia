"""
Widoki aplikacji rejs.

Obsługuje żądania HTTP dla rejestracji na rejsy.
"""

from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import localdate

from .forms import Dane_DodatkoweForm, ZgloszenieForm
from .models import Rejs, Zgloszenie
from .serwisy.rejestracja import serwis_rejestracji


def index(request):
	"""Wyświetla listę dostępnych rejsów."""
	dzis = localdate()
	rejsy = Rejs.objects.filter(
		aktywna_rekrutacja=True,
		od__gte=dzis,
	).order_by("od")
	return render(request, "rejs/index.html", {"rejsy": rejsy})


def zgloszenie_utworz(request, rejs_id):
	"""Obsługuje formularz tworzenia zgłoszenia na rejs."""
	rejs = get_object_or_404(Rejs, id=rejs_id)

	# Sprawdzenie czy można się zarejestrować
	mozna, _ = serwis_rejestracji.czy_mozna_rejestrowac(rejs)
	if not mozna:
		return redirect("index")

	if request.method == "POST":
		form = ZgloszenieForm(request.POST, initial={"rejs": rejs})
		if form.is_valid():
			zgl = form.save(commit=False)
			zgl.rejs = rejs
			zgl.save()
			return redirect("zgloszenie_details", token=zgl.token)
	else:
		form = ZgloszenieForm(initial={"rejs": rejs})

	return render(request, "rejs/zgloszenie_form.html", {"form": form, "rejs": rejs})


def dane_dodatkowe_form(request, token):
	"""Obsługuje formularz danych dodatkowych (PESEL, dokument)."""
	zgloszenie = get_object_or_404(Zgloszenie, token=token)
	rejs = zgloszenie.rejs

	if request.method == "POST":
		form = Dane_DodatkoweForm(request.POST)
		if form.is_valid():
			dane = form.save(commit=False)
			dane.zgloszenie = zgloszenie
			dane.save()
			return redirect(zgloszenie.get_absolute_url())
	else:
		form = Dane_DodatkoweForm()

	return render(
		request,
		"rejs/dane_dodatkowe_form.html",
		{"form": form, "zgloszenie": zgloszenie, "rejs": rejs},
	)


def zgloszenie_details(request, token):
	"""Wyświetla szczegóły zgłoszenia."""
	zgloszenie = get_object_or_404(Zgloszenie, token=token)

	# Przekierowanie do formularza danych dodatkowych jeśli wymagane
	if serwis_rejestracji.czy_wymaga_danych_dodatkowych(zgloszenie):
		return redirect("dane_dodatkowe_form", token=token)

	return render(request, "rejs/zgloszenie_details.html", {"zgloszenie": zgloszenie})


def rodo_info(request):
	"""Wyświetla informacje o przetwarzaniu danych osobowych (RODO)."""
	return render(request, "rejs/rodo_info.html")
