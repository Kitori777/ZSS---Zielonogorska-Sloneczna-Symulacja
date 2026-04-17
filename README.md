# SunCalc 3D — Live i Symulacja

Desktopowa aplikacja Python/Qt do wizualizacji położenia Słońca i Księżyca, kierunku oraz długości cienia, z trybem live i symulacją dobową. Projekt zawiera też bibliotekę `suncalc` do obliczeń astronomicznych oraz rozszerzenia pogodowe, analizę punktową i eksport danych do CSV.

## Autorstwo i źródło

Ten projekt bazuje na bibliotece **suncalc-py** autorstwa **Kyle'a Barrona**:
- oryginalny projekt: `https://github.com/kylebarron/suncalc-py`
- licencja oryginału: **MIT**

W tym repozytorium biblioteka została rozszerzona i wykorzystana jako część większej aplikacji desktopowej z interfejsem GUI, wizualizacją 3D, warstwą pogodową, analizą punktową oraz dodatkowymi helperami astronomicznymi.

## Co zawiera repozytorium

- `suncalc/` — rdzeń obliczeń astronomicznych
- `app/` — interfejs GUI, logika wizualizacji, pogoda i analiza punktowa
- `data/` — lokalne dane historyczne i modelowe CSV
- `docs/` — dokumentacja techniczna projektu w HTML
- `exports/` — eksporty CSV z symulacji
- `main.py` — punkt startowy aplikacji desktopowej
- `tests/` — testy części obliczeniowej

## Najważniejsze funkcje

- tryb **Live**
- tryb **Symulacja**
- wizualizacja 3D:
  - Słońca
  - Księżyca
  - światła
  - cienia
  - chmur
  - deszczu
- integracja z **Open-Meteo**
- fallback do lokalnych plików **CSV**
- analiza punktowa toru i środka toru
- podgląd danych punktu po wskazaniu / najechaniu
- obracanie widoku 3D myszką
- zoom in / zoom out / reset zoomu
- eksport danych symulacji do **CSV**

## Jakie dane trafiają do analizy / eksportu

W zależności od źródła danych projekt może zwracać między innymi:

- `air_temperature_c`
- `air_temperature_k`
- `estimated_point_temperature_c`
- `rain_mm_h`
- `precipitation_m_per_s`
- `cloud_cover`
- `cloud_unit`
- `cloud_cover_raw`
- `cloud_unit_raw`
- `relative_humidity`
- `wind_speed_m_per_s`
- `air_pressure_pa`
- `shortwave_down_w_per_m2`
- `longwave_down_w_per_m2`
- `longwave_source`
- `solar_exposure_pct`
- `is_shaded`

## Dokumentacja

W folderze `docs/` znajduje się raport HTML opisujący:
- funkcje matematyczne projektu
- model słońca i cienia
- geometrię toru
- forcingi atmosferyczne
- model temperatury punktu
- estymację longwave
- wykresy i zależności

Główny plik dokumentacji:
- `docs/index.html`

## Instalacja

### Wersja podstawowa

```bash
pip install -e .
```

### Wersja z GUI

```bash
pip install -e .[desktop]
```



### Wszystko naraz

```bash
pip install -e .[desktop,data,test]
```

## Uruchomienie aplikacji

```bash
python main.py
```

albo po instalacji:

```bash
suncalc-gui
```

## Uruchomienie testów

```bash
pytest
```


## Licencja

Repozytorium zachowuje licencję MIT. Przy dalszej dystrybucji zachowaj informację o oryginalnym autorze biblioteki `suncalc-py` i plik `LICENSE`.
