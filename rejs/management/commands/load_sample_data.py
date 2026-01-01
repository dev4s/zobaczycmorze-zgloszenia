"""Management command to generate sample data with dynamic dates."""

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from rejs.models import Ogloszenie, Rejs, Wachta, Wplata, Zgloszenie


class Command(BaseCommand):
	"""Generate sample data with dates relative to today."""

	help = "Generuje dane testowe z datami relatywnymi do dzisiaj"

	def handle(self, *args, **options):
		today = timezone.localdate()

		# Clear existing data
		self._clear_data()

		# Generate trips
		future_trips = self._create_future_trips(today)
		past_trips = self._create_past_trips(today)
		all_trips = future_trips + past_trips

		# Generate watches for all trips
		watches_map = self._create_watches(all_trips)

		# Generate registrations
		registrations = self._create_registrations(all_trips, watches_map)

		# Generate payments
		self._create_payments(registrations)

		# Generate announcements
		self._create_announcements(all_trips)

		# Summary
		self.stdout.write("")
		self.stdout.write(self.style.SUCCESS("Dane testowe zostaly wygenerowane."))
		self.stdout.write(f"  - {len(future_trips)} rejsow przyszlych (widocznych na stronie)")
		self.stdout.write(f"  - {len(past_trips)} rejsow przeszlych (archiwalnych)")
		self.stdout.write(f"  - {Zgloszenie.objects.count()} zgloszen")
		self.stdout.write(f"  - {Wplata.objects.count()} wplat")
		self.stdout.write(f"  - {Ogloszenie.objects.count()} ogloszen")
		self.stdout.write("")

	def _clear_data(self):
		"""Usuwa istniejace dane testowe."""
		Ogloszenie.objects.all().delete()
		Wplata.objects.all().delete()
		Zgloszenie.objects.all().delete()
		Wachta.objects.all().delete()
		Rejs.objects.all().delete()

	def _create_future_trips(self, today):
		"""Tworzy 5 rejsow z datami w przyszlosci."""
		trips_data = [
			{
				"nazwa": "Rejs Baltycki",
				"months_offset": 1,
				"duration": 14,
				"start": "Gdynia",
				"koniec": "Sztokholm",
				"cena": Decimal("3500.00"),
				"zaliczka": Decimal("500.00"),
				"opis": "Dwutygodniowy rejs po Baltyku. Odwiedzimy malownicze porty Szwecji i poznamy uroki zeglarstwa morskiego. Rejs przeznaczony dla osob niewidomych i slabowidzacych oraz ich przewodnikow.",
			},
			{
				"nazwa": "Rejs Finski",
				"months_offset": 2,
				"duration": 14,
				"start": "Gdynia",
				"koniec": "Helsinki",
				"cena": Decimal("4000.00"),
				"zaliczka": Decimal("600.00"),
				"opis": "Rejs do stolicy Finlandii z postojami w portach Estonii. Niezapomniane widoki archipelagu finskiego i biale noce polnocy.",
			},
			{
				"nazwa": "Rejs Norweski",
				"months_offset": 3,
				"duration": 14,
				"start": "Gdansk",
				"koniec": "Bergen",
				"cena": Decimal("5500.00"),
				"zaliczka": Decimal("800.00"),
				"opis": "Wyprawa do krainy fiordow. Dwutygodniowa przygoda wzdluz norweskiego wybrzeza z wizyta w Bergen - bramie do fiordow.",
			},
			{
				"nazwa": "Rejs Dunski",
				"months_offset": 4,
				"duration": 10,
				"start": "Swinoujscie",
				"koniec": "Kopenhaga",
				"cena": Decimal("2800.00"),
				"zaliczka": Decimal("400.00"),
				"opis": "Krotszy rejs do dunskiej stolicy. Idealny dla osob, ktore chca sprobowac zeglarstwa morskiego bez dlugiego zobowiazania czasowego.",
			},
			{
				"nazwa": "Rejs Estonski",
				"months_offset": 5,
				"duration": 14,
				"start": "Gdynia",
				"koniec": "Tallinn",
				"cena": Decimal("3200.00"),
				"zaliczka": Decimal("500.00"),
				"opis": "Rejs do Estonii. Zlota polska jesien na morzu i wizyta w sredniowiecznym Tallinnie.",
			},
		]

		trips = []
		for data in trips_data:
			od = today + timedelta(days=data["months_offset"] * 30)
			do = od + timedelta(days=data["duration"])
			trip = Rejs.objects.create(
				nazwa=data["nazwa"],
				od=od,
				do=do,
				start=data["start"],
				koniec=data["koniec"],
				cena=data["cena"],
				zaliczka=data["zaliczka"],
				opis=data["opis"],
				aktywna_rekrutacja=True,
			)
			trips.append(trip)

		return trips

	def _create_past_trips(self, today):
		"""Tworzy 2 rejsy z datami w przeszlosci."""
		trips_data = [
			{
				"nazwa": "Rejs Litewski (archiwalny)",
				"months_offset": -3,
				"duration": 10,
				"start": "Gdynia",
				"koniec": "Klajpeda",
				"cena": Decimal("2500.00"),
				"zaliczka": Decimal("400.00"),
				"opis": "Rejs do Litwy zakonczony. Uczestnicy odwiedzili Klajpede i poznali litewskie wybrzeze.",
			},
			{
				"nazwa": "Rejs Bornholmski (archiwalny)",
				"months_offset": -1,
				"duration": 7,
				"start": "Gdansk",
				"koniec": "Bornholm",
				"cena": Decimal("1800.00"),
				"zaliczka": Decimal("300.00"),
				"opis": "Krotki rejs na duska wyspe Bornholm. Rejs zakonczony sukcesem.",
			},
		]

		trips = []
		for data in trips_data:
			od = today + timedelta(days=data["months_offset"] * 30)
			do = od + timedelta(days=data["duration"])
			trip = Rejs.objects.create(
				nazwa=data["nazwa"],
				od=od,
				do=do,
				start=data["start"],
				koniec=data["koniec"],
				cena=data["cena"],
				zaliczka=data["zaliczka"],
				opis=data["opis"],
				aktywna_rekrutacja=False,  # Rekrutacja zamknieta dla przeszlych rejsow
			)
			trips.append(trip)

		return trips

	def _create_watches(self, trips):
		"""Tworzy wachty dla kazdego rejsu."""
		watch_names = ["Alfa", "Beta", "Gamma"]
		watches_map = {}

		for trip in trips:
			watches_map[trip.id] = []
			for name in watch_names:
				watch = Wachta.objects.create(rejs=trip, nazwa=name)
				watches_map[trip.id].append(watch)

		return watches_map

	def _create_registrations(self, trips, watches_map):
		"""Tworzy zgloszenia dla rejsow."""
		# Dane uczestnikow
		participants = [
			{
				"imie": "Jan",
				"nazwisko": "Kowalski",
				"email": "jan.kowalski@example.com",
				"telefon": "501234567",
				"data_urodzenia": "1985-03-15",
				"adres": "ul. Morska 12/5",
				"kod_pocztowy": "81-350",
				"miejscowosc": "Gdynia",
				"wzrok": "NIEWIDOMY",
				"rola": "ZALOGANT",
			},
			{
				"imie": "Anna",
				"nazwisko": "Nowak",
				"email": "anna.nowak@example.com",
				"telefon": "502345678",
				"data_urodzenia": "1990-07-22",
				"adres": "ul. Sloneczna 5",
				"kod_pocztowy": "80-001",
				"miejscowosc": "Gdansk",
				"wzrok": "SLABO-WIDZACY",
				"rola": "ZALOGANT",
			},
			{
				"imie": "Piotr",
				"nazwisko": "Wisniewski",
				"email": "piotr.wisniewski@example.com",
				"telefon": "503456789",
				"data_urodzenia": "1978-11-30",
				"adres": "ul. Lesna 8",
				"kod_pocztowy": "81-100",
				"miejscowosc": "Gdynia",
				"wzrok": "NIEWIDOMY",
				"rola": "ZALOGANT",
			},
			{
				"imie": "Maria",
				"nazwisko": "Wojcik",
				"email": "maria.wojcik@example.com",
				"telefon": "504567890",
				"data_urodzenia": "1995-02-14",
				"adres": "ul. Kwiatowa 3/10",
				"kod_pocztowy": "00-001",
				"miejscowosc": "Warszawa",
				"wzrok": "WIDZI",
				"rola": "OFICER-WACHTY",
			},
			{
				"imie": "Tomasz",
				"nazwisko": "Kaminski",
				"email": "tomasz.kaminski@example.com",
				"telefon": "505678901",
				"data_urodzenia": "1982-06-08",
				"adres": "ul. Parkowa 15",
				"kod_pocztowy": "30-001",
				"miejscowosc": "Krakow",
				"wzrok": "NIEWIDOMY",
				"rola": "ZALOGANT",
			},
			{
				"imie": "Katarzyna",
				"nazwisko": "Lewandowska",
				"email": "katarzyna.lewandowska@example.com",
				"telefon": "506789012",
				"data_urodzenia": "1988-09-25",
				"adres": "ul. Glowna 22",
				"kod_pocztowy": "50-001",
				"miejscowosc": "Wroclaw",
				"wzrok": "SLABO-WIDZACY",
				"rola": "ZALOGANT",
			},
			{
				"imie": "Michal",
				"nazwisko": "Zielinski",
				"email": "michal.zielinski@example.com",
				"telefon": "507890123",
				"data_urodzenia": "1992-12-03",
				"adres": "ul. Nadmorska 7",
				"kod_pocztowy": "76-200",
				"miejscowosc": "Slupsk",
				"wzrok": "NIEWIDOMY",
				"rola": "ZALOGANT",
			},
			{
				"imie": "Agnieszka",
				"nazwisko": "Szymanska",
				"email": "agnieszka.szymanska@example.com",
				"telefon": "508901234",
				"data_urodzenia": "1975-04-18",
				"adres": "ul. Portowa 1",
				"kod_pocztowy": "70-001",
				"miejscowosc": "Szczecin",
				"wzrok": "WIDZI",
				"rola": "OFICER-WACHTY",
			},
			{
				"imie": "Robert",
				"nazwisko": "Dabrowski",
				"email": "robert.dabrowski@example.com",
				"telefon": "509012345",
				"data_urodzenia": "1980-08-12",
				"adres": "ul. Zeglarska 9",
				"kod_pocztowy": "81-300",
				"miejscowosc": "Gdynia",
				"wzrok": "NIEWIDOMY",
				"rola": "ZALOGANT",
			},
			{
				"imie": "Ewa",
				"nazwisko": "Mazur",
				"email": "ewa.mazur@example.com",
				"telefon": "510123456",
				"data_urodzenia": "1998-01-28",
				"adres": "ul. Baltycka 14",
				"kod_pocztowy": "84-100",
				"miejscowosc": "Puck",
				"wzrok": "SLABO-WIDZACY",
				"rola": "ZALOGANT",
			},
			{
				"imie": "Krzysztof",
				"nazwisko": "Jankowski",
				"email": "krzysztof.jankowski@example.com",
				"telefon": "511234567",
				"data_urodzenia": "1970-05-05",
				"adres": "ul. Kapitanska 2",
				"kod_pocztowy": "81-400",
				"miejscowosc": "Gdynia",
				"wzrok": "WIDZI",
				"rola": "OFICER-WACHTY",
			},
			{
				"imie": "Magdalena",
				"nazwisko": "Krawczyk",
				"email": "magdalena.krawczyk@example.com",
				"telefon": "512345678",
				"data_urodzenia": "1993-10-17",
				"adres": "ul. Marynarska 6",
				"kod_pocztowy": "81-200",
				"miejscowosc": "Gdynia",
				"wzrok": "NIEWIDOMY",
				"rola": "ZALOGANT",
			},
		]

		# Statusy do przypisania (roznorodnosc)
		statuses = [
			Zgloszenie.STATUS_ZAKWALIFIKOWANY,
			Zgloszenie.STATUS_ZAKWALIFIKOWANY,
			Zgloszenie.STATUS_NIEZAKWALIFIKOWANY,
			Zgloszenie.STATUS_ZAKWALIFIKOWANY,
			Zgloszenie.STATUS_ODRZUCONE,
			Zgloszenie.STATUS_NIEZAKWALIFIKOWANY,
			Zgloszenie.STATUS_ZAKWALIFIKOWANY,
			Zgloszenie.STATUS_ZAKWALIFIKOWANY,
			Zgloszenie.STATUS_NIEZAKWALIFIKOWANY,
			Zgloszenie.STATUS_ZAKWALIFIKOWANY,
			Zgloszenie.STATUS_ZAKWALIFIKOWANY,
			Zgloszenie.STATUS_NIEZAKWALIFIKOWANY,
		]

		registrations = []
		participant_idx = 0

		for trip_idx, trip in enumerate(trips):
			# Przypisz 2-3 uczestnikow do kazdego rejsu
			num_participants = 2 if trip_idx % 2 == 0 else 3
			watches = watches_map.get(trip.id, [])

			for i in range(num_participants):
				if participant_idx >= len(participants):
					participant_idx = 0  # Zacznij od poczatku

				p = participants[participant_idx]
				status = statuses[participant_idx % len(statuses)]

				# Przypisz wachte tylko zakwalifikowanym
				wachta = None
				if status == Zgloszenie.STATUS_ZAKWALIFIKOWANY and watches:
					wachta = watches[i % len(watches)]

				# Dla przeszlych rejsow - wszyscy zakwalifikowani
				if not trip.aktywna_rekrutacja:
					status = Zgloszenie.STATUS_ZAKWALIFIKOWANY
					if watches:
						wachta = watches[i % len(watches)]

				reg = Zgloszenie.objects.create(
					imie=p["imie"],
					nazwisko=p["nazwisko"],
					email=f"{trip_idx}_{p['email']}",  # Unikalne emaile per rejs
					telefon=p["telefon"],
					data_urodzenia=p["data_urodzenia"],
					adres=p["adres"],
					kod_pocztowy=p["kod_pocztowy"],
					miejscowosc=p["miejscowosc"],
					obecnosc="tak" if i % 2 == 0 else "nie",
					rodo=True,
					status=status,
					wzrok=p["wzrok"],
					rola=p["rola"],
					rejs=trip,
					wachta=wachta,
				)
				registrations.append(reg)
				participant_idx += 1

		return registrations

	def _create_payments(self, registrations):
		"""Tworzy wplaty dla zgloszen."""
		for reg in registrations:
			if reg.status == Zgloszenie.STATUS_ZAKWALIFIKOWANY:
				# Zaliczka
				Wplata.objects.create(
					kwota=reg.rejs.zaliczka,
					rodzaj=Wplata.RODZAJ_WPLATA,
					zgloszenie=reg,
				)

				# Dla niektorych - pelna wplata
				if reg.id % 3 == 0:
					reszta = reg.rejs.cena - reg.rejs.zaliczka
					Wplata.objects.create(
						kwota=reszta,
						rodzaj=Wplata.RODZAJ_WPLATA,
						zgloszenie=reg,
					)

			# Dla odrzuconych - zwrot
			if reg.status == Zgloszenie.STATUS_ODRZUCONE:
				Wplata.objects.create(
					kwota=Decimal("100.00"),
					rodzaj=Wplata.RODZAJ_ZWROT,
					zgloszenie=reg,
				)

	def _create_announcements(self, trips):
		"""Tworzy ogloszenia dla rejsow."""
		announcements_templates = [
			{
				"tytul": "Informacja o zaokretwaniu",
				"text": "Zaokretwanie odbedzie sie o godzinie 10:00 w porcie. Prosimy o punktualne przybycie z dokumentem tozsamosci.",
			},
			{
				"tytul": "Lista rzeczy do zabrania",
				"text": "Prosimy o zabranie: cieplej kurtki, nieprzemakalnego ubrania, wygodnego obuwia z antyposlizgowa podeszwa, lekow (jesli sa potrzebne), okularow przeciwslonecznych.",
			},
		]

		for trip in trips:
			# Dodaj 1-2 ogloszenia per rejs
			for i, template in enumerate(announcements_templates):
				if i == 0 or trip.id % 2 == 0:
					Ogloszenie.objects.create(
						rejs=trip,
						tytul=template["tytul"],
						text=template["text"],
					)
