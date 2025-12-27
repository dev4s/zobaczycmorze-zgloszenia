# Zobaczyć Morze - System Zgłoszeń

System zgłoszeń na rejsy żeglarskie dla osób z dysfunkcją wzroku, prowadzony przez Fundację Zobaczyć Morze.

## Wymagania

- Python 3.12 lub nowszy
- pip (menedżer pakietów Python)

## Instalacja

### Instalacja z UV (zalecana)

[UV](https://github.com/astral-sh/uv) to nowoczesny, szybki menedżer pakietów Python.

1. **Zainstaluj UV** (jeśli nie masz):

   ```bash
   # Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Zainstaluj zależności:**

   ```bash
   uv sync
   ```

3. **Skonfiguruj środowisko:**

   ```bash
   cp .env.example .env
   ```

   Następnie edytuj plik `.env` i ustaw `SECRET_KEY` (instrukcja w pliku).

4. **Pierwsze uruchomienie:**

   ```bash
   uv run poe setup
   ```

### Instalacja tradycyjna (pip)

1. **Utwórz wirtualne środowisko Python:**

   ```bash
   python -m venv venv
   ```

2. **Aktywuj wirtualne środowisko:**

   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

3. **Zainstaluj zależności:**

   ```bash
   pip install -r requirements.txt
   pip install poethepoet python-dotenv
   ```

4. **Skonfiguruj środowisko:**

   ```bash
   cp .env.example .env
   ```

   Następnie edytuj plik `.env` i ustaw `SECRET_KEY`.

5. **Pierwsze uruchomienie:**

   ```bash
   poe setup
   ```

## Konfiguracja środowiska (.env)

Projekt wymaga pliku `.env` z konfiguracją. Skopiuj szablon:

```bash
cp .env.example .env
```

### Wymagane zmienne

| Zmienna | Opis | Przykład |
|---------|------|----------|
| `SECRET_KEY` | Klucz bezpieczeństwa Django | Wygeneruj komendą w `.env.example` |

### Opcjonalne zmienne

| Zmienna | Opis | Domyślna wartość |
|---------|------|------------------|
| `DEBUG` | Tryb debugowania | `True` |
| `ALLOWED_HOSTS` | Dozwolone hosty (przecinkami) | (puste) |
| `SITE_URL` | URL strony (do linków w emailach) | `http://localhost:8000` |
| `EMAIL_*` | Konfiguracja SMTP | Backend konsolowy |

**Uwaga:** Bez pliku `.env` lub bez ustawionego `SECRET_KEY` aplikacja nie uruchomi się i wyświetli komunikat z instrukcjami.

## Kolejne uruchomienia

Aby uruchomić serwer deweloperski:

```bash
# Z UV (zalecane)
uv run poe serve

# Lub tradycyjnie
poe serve
```

Następnie otwórz przeglądarkę i wpisz adres:
- **Strona główna:** http://localhost:8000
- **Panel administracyjny:** http://localhost:8000/admin

## Komendy deweloperskie

| Komenda | Opis |
|---------|------|
| `poe serve` | Uruchom serwer deweloperski |
| `poe migrate` | Zastosuj migracje bazy danych |
| `poe makemigrations` | Utwórz nowe migracje |
| `poe createsuperuser` | Utwórz konto administratora |
| `poe test` | Uruchom testy |
| `poe shell` | Uruchom shell Django |
| `poe setup` | Pierwsze uruchomienie (migrate + createsuperuser) |

**Uwaga:** Jeśli używasz UV, poprzedź komendy `uv run`, np. `uv run poe serve`.

## Uruchamianie testów

```bash
# Z UV
uv run poe test

# Lub tradycyjnie
poe test

# Lub bezpośrednio
python manage.py test
```

## Struktura projektu

```
zobaczycmorze-zgloszenia/
├── rejs/                   # Główna aplikacja Django
│   ├── migrations/         # Migracje bazy danych
│   ├── static/css/         # Arkusze stylów
│   ├── templates/          # Szablony HTML
│   ├── models.py           # Modele danych
│   ├── views.py            # Widoki
│   ├── forms.py            # Formularze
│   ├── admin.py            # Konfiguracja panelu admina
│   ├── signals.py          # Sygnały (np. wysyłanie emaili)
│   └── tests.py            # Testy
├── zm_zgloszenia/          # Ustawienia projektu Django
│   └── settings.py         # Konfiguracja
├── .env.example            # Szablon konfiguracji środowiska
├── manage.py               # Skrypt zarządzania Django
├── pyproject.toml          # Konfiguracja projektu i zadań
├── requirements.txt        # Zależności (dla pip)
└── README.md               # Ten plik
```

## Grupy użytkowników

System posiada trzy predefiniowane grupy użytkowników:

| Grupa | Uprawnienia |
|-------|-------------|
| **Administratorzy** | Pełny dostęp do wszystkich funkcji |
| **Koordynatorzy Rejsów** | Zarządzanie rejsami, wachtami i ogłoszeniami |
| **Obsługa Zgłoszeń** | Zarządzanie zgłoszeniami i wpłatami |

Grupy są tworzone automatycznie podczas migracji. Przypisz użytkowników do grup w panelu administracyjnym: http://localhost:8000/admin/auth/group/

## Panel administracyjny

Po zalogowaniu do panelu admina (http://localhost:8000/admin) możesz:

- Dodawać i edytować rejsy
- Przeglądać i zarządzać zgłoszeniami
- Rejestrować wpłaty i zwroty
- Przypisywać uczestników do wacht
- Publikować ogłoszenia dla uczestników

Panel jest zaprojektowany tak, aby był prosty i intuicyjny. Jeśli masz problemy z obsługą, zgłoś to.

## Przygotowanie do produkcji

Przed wdrożeniem na serwer produkcyjny:

1. Wygeneruj nowy `SECRET_KEY` i ustaw w `.env`
2. Ustaw `DEBUG=False`
3. Skonfiguruj `ALLOWED_HOSTS` z domeną produkcyjną
4. Skonfiguruj `SITE_URL` z pełnym adresem strony
5. Skonfiguruj prawdziwy backend email (SMTP)
6. Rozważ migrację na PostgreSQL
