"""
Serwis zarządzania wachtami.

Odpowiada za logikę biznesową związaną z przypisywaniem członków do wacht.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from django import forms

if TYPE_CHECKING:
	from django.db.models import QuerySet

	from rejs.models import Rejs, Wachta, Zgloszenie


class SerwisWacht:
	"""
	Serwis obsługujący zarządzanie wachtami.

	Metody:
		przypisz_czlonka - przypisuje zgłoszenie do wachty
		usun_czlonka - usuwa zgłoszenie z wachty
		pobierz_dostepnych_czlonkow - zwraca zgłoszenia bez wachty
	"""

	def przypisz_czlonka(self, wachta: Wachta, zgloszenie: Zgloszenie) -> None:
		"""
		Przypisuje zgłoszenie do wachty.

		Args:
			wachta: Wachta do której przypisujemy
			zgloszenie: Zgłoszenie do przypisania

		Raises:
			forms.ValidationError: Gdy zgłoszenie nie należy do rejsu wachty
		"""
		if zgloszenie.rejs_id != wachta.rejs_id:
			raise forms.ValidationError(f"Zgłoszenie {zgloszenie} nie należy do rejsu {wachta.rejs}")

		zgloszenie.wachta = wachta
		zgloszenie.save(update_fields=["wachta"])

	def usun_czlonka(self, zgloszenie: Zgloszenie) -> None:
		"""
		Usuwa zgłoszenie z wachty.

		Args:
			zgloszenie: Zgłoszenie do usunięcia z wachty
		"""
		zgloszenie.wachta = None
		zgloszenie.save(update_fields=["wachta"])

	def pobierz_dostepnych_czlonkow(self, rejs: Rejs) -> QuerySet[Zgloszenie]:
		"""
		Zwraca zgłoszenia z danego rejsu, które nie są przypisane do żadnej wachty.

		Args:
			rejs: Rejs dla którego szukamy dostępnych członków

		Returns:
			QuerySet zgłoszeń bez przypisanej wachty
		"""
		from rejs.models import Zgloszenie

		return Zgloszenie.objects.filter(rejs=rejs, wachta=None)

	def aktualizuj_czlonkow_wachty(self, wachta: Wachta, nowi_czlonkowie: list[Zgloszenie]) -> None:
		"""
		Aktualizuje listę członków wachty używając bulk_update dla wydajności.

		Usuwa członków którzy nie są na nowej liście i dodaje nowych.
		Używa bulk_update zamiast pojedynczych save() - nie wywołuje sygnałów,
		co jest pożądane przy operacjach zbiorczych w adminie.

		Args:
			wachta: Wachta do aktualizacji
			nowi_czlonkowie: Lista zgłoszeń które mają być członkami wachty
		"""
		from rejs.models import Zgloszenie

		obecni = set(wachta.czlonkowie.all())
		nowi = set(nowi_czlonkowie)

		# Usuń tych którzy nie są na nowej liście (bulk_update)
		do_usuniecia = obecni - nowi
		if do_usuniecia:
			for zgloszenie in do_usuniecia:
				zgloszenie.wachta = None
			Zgloszenie.objects.bulk_update(list(do_usuniecia), ["wachta"])

		# Dodaj nowych (z walidacją, potem bulk_update)
		do_dodania = nowi - obecni
		if do_dodania:
			for zgloszenie in do_dodania:
				if zgloszenie.rejs_id != wachta.rejs_id:
					raise forms.ValidationError(f"Zgłoszenie {zgloszenie} nie należy do rejsu {wachta.rejs}")
				zgloszenie.wachta = wachta
			Zgloszenie.objects.bulk_update(list(do_dodania), ["wachta"])


# Domyślna instancja serwisu
serwis_wacht = SerwisWacht()
