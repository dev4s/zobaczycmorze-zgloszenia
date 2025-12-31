# TODO

## Bezpieczenstwo / RODO

Szczegoly w [RODO.md](RODO.md)

- [ ] Endpoint do usuniecia danych (Art. 17 RODO)
- [ ] Migracja SQLite -> PostgreSQL
- [ ] Rotacja klucza szyfrowania
- [ ] Dwuskladnikowe uwierzytelnianie (2FA)

## Funkcjonalnosc

- [ ] Formularz zgody na przetwarzanie danych wrazliwych (PESEL)
- [x] Pola pokazuja "unknown" zamiast pustego (adres, kod_pocztowy, miejscowosc, data_urodzenia)
  - Zmieniono domyslne wartosci na puste stringi
  - Dodano migracje z konwersja istniejacych danych
- [ ] Przeniesienie elementow z motywu Bootstrap do glownego

## Refaktoryzacja

- [x] Refaktoryzacja kodu zgodnie z wzorcem MTV (Model-Template-View)
  - Utworzono pakiet `rejs/modele/` (modele podzielone na pliki)
  - Utworzono pakiet `rejs/serwisy/` (notyfikacje, rejestracja, wachty)
  - Utworzono pakiet `rejs/walidatory/` (walidatory PESEL i podstawowe)
  - Optymalizacja wydajnosci (batch emails, bulk_update, original value tracking)
