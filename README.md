# SunCalc 3D — Live i Symulacja

Desktopowa aplikacja Python/Qt do wizualizacji położenia Słońca i Księżyca, kierunku oraz długości cienia, z trybem live i symulacją dobową. Projekt zawiera też bibliotekę `suncalc` do obliczeń astronomicznych.

## Autorstwo i źródło

Ten projekt bazuje na bibliotece **suncalc-py** autorstwa **Kyle'a Barrona**:
- oryginalny projekt: `https://github.com/kylebarron/suncalc-py`
- licencja oryginału: **MIT**

W tym repozytorium biblioteka została rozszerzona i wykorzystana jako część większej aplikacji desktopowej z interfejsem GUI, wizualizacją 3D oraz dodatkowymi helperami astronomicznymi.

## Co zawiera repozytorium

- `suncalc/` — rdzeń obliczeń astronomicznych
- `app/` — interfejs GUI i logika wizualizacji
- `main.py` — punkt startowy aplikacji desktopowej
- `tests/` — testy części obliczeniowej
- `assets/` — zasoby pomocnicze
- `pobranie.py` — pomocniczy skrypt do pobierania danych ERA5-Land

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
