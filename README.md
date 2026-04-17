# ZSS — Zielonogórska Słoneczna Symulacja

Desktopowa aplikacja w Pythonie i Qt do analizy położenia słońca i księżyca, cienia, pogody oraz punktowego wpływu warunków atmosferycznych na tor i środek toru. Projekt łączy obliczenia astronomiczne z wizualizacją 3D, danymi historycznymi CSV oraz danymi pogodowymi online.

---

## Najważniejsze możliwości

- tryb **Live** oparty o aktualny czas lokalny,
- tryb **Symulacja** dla wybranego dnia i godziny,
- wizualizacja 3D:
  - słońca,
  - księżyca,
  - stref światła,
  - cienia,
  - chmur,
  - deszczu,
- analiza punktowa toru i środka toru,
- eksport wyników symulacji do **CSV**,
- integracja z **Open-Meteo**,
- fallback do lokalnych plików **CSV**,
- obracanie sceny myszką,
- zoom in / zoom out / reset zoomu,
- dokumentacja techniczna w folderze **`docs/`**.

---

## Co dokładnie analizuje aplikacja

Dla każdego punktu siatki na torze lub środku toru aplikacja może wyznaczyć między innymi:

- czy punkt jest w cieniu,
- procent ekspozycji słonecznej,
- temperaturę powietrza,
- temperaturę powietrza w kelwinach,
- szacowaną temperaturę punktu,
- opad w mm/h,
- opad w m/s,
- zachmurzenie,
- wilgotność względną,
- prędkość wiatru,
- ciśnienie powietrza,
- promieniowanie krótkofalowe,
- promieniowanie długofalowe.

---

## Źródła danych

Projekt korzysta z dwóch typów źródeł:

### 1. Lokalne pliki CSV
Folder `data/` zawiera dane historyczne i modelowe, między innymi:

- dane stacyjne,
- dane modelowe,
- godzinowe opady,
- temperaturę,
- punkt rosy,
- ciśnienie,
- wiatr,
- śnieg,
- promieniowanie shortwave i longwave,
- temperatury i wilgotność warstw gruntu,
- runoff i parowanie.

### 2. Open-Meteo
Aplikacja potrafi pobierać dane online dla trybu live i przyszłych symulacji, z cache, aby nie wykonywać zbędnych zapytań.

---

## Eksport CSV

Po zakończeniu lub zatrzymaniu symulacji aplikacja zapisuje plik CSV do folderu:

```text
exports/
```

Przykładowe kolumny eksportu:

```text
frame_local_time
date
time
x
y
point_type
is_shaded
solar_exposure_pct
air_temperature_c
air_temperature_k
estimated_point_temperature_c
rain_mm_h
precipitation_m_per_s
cloud_cover
cloud_unit
cloud_cover_raw
cloud_unit_raw
relative_humidity
wind_speed_m_per_s
air_pressure_pa
shortwave_down_w_per_m2
longwave_down_w_per_m2
longwave_source
```

### Uwaga o `longwave_down_w_per_m2`
- jeżeli źródło danych zwraca wartość bezpośrednio, trafia ona do CSV,
- jeżeli źródło nie zwraca longwave, aplikacja liczy wartość estymowaną,
- kolumna `longwave_source` informuje, czy wartość pochodzi ze źródła czy z estymacji.

---

## Dokumentacja techniczna

W folderze:

```text
docs/
```

znajduje się raport HTML opisujący:

- funkcje rdzenia obliczeniowego,
- matematykę pozycji słońca i księżyca,
- model cienia,
- geometrię toru,
- forcingi atmosferyczne,
- model temperatury punktu,
- estymację longwave,
- wykresy i zależności.

Główny plik dokumentacji:

```text
docs/index.html
```

---

## Struktura projektu

```text
.
├── app/
│   ├── gui.py
│   ├── render_3d.py
│   ├── scene.py
│   ├── simulation.py
│   ├── state.py
│   └── weather_data.py
├── data/
├── docs/
│   ├── index.html
│   └── assets/
├── exports/
├── suncalc/
├── tests/
├── main.py
├── pyproject.toml
└── README.md
```

---

## Wymagania

- Python 3.10+
- PySide6
- matplotlib
- numpy
- pandas
- requests

---

## Instalacja

### Wersja podstawowa

```bash
uv sync
```

### Wersja rozwinięta

```bash
uv sync --group dev --extra desktop --extra data
```

---

## Uruchomienie

```bash
uv run --active python main.py
```


---

## Sterowanie

### Panel boczny
- wybór trybu Live / Symulacja,
- wybór daty,
- pionowy suwak czasu,
- krok symulacji,
- przełączniki widoku,
- ustawienia warstwy pogody,
- status aplikacji,
- dane punktu po najechaniu / wskazaniu.

### Widok 3D
- obrót sceny myszką,
- zachowanie kąta widoku po odświeżeniu,
- zoom `+`, `-`, `100%`,
- możliwość analizy punktów siatki.

---

## Testy

```bash
pytest
```

---

## Autorstwo i źródło

Projekt bazuje na bibliotece **suncalc-py** autorstwa **Kyle’a Barrona**:

- oryginalny projekt: `https://github.com/kylebarron/suncalc-py`
- licencja oryginału: **MIT**

W tym repozytorium biblioteka została rozszerzona o:

- aplikację desktopową,
- wizualizację 3D,
- warstwę pogodową,
- analizę punktową,
- eksport forcingów atmosferycznych,
- dokumentację raportową HTML.

---

## Licencja

Repozytorium zachowuje licencję MIT. Przy dalszej dystrybucji zachowaj informację o oryginalnym autorze biblioteki `suncalc-py` oraz plik `LICENSE`.
