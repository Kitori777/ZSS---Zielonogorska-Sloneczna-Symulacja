# Changelog

## [0.5.0] - 2026-05-22

### Dodano
- Dodano docelowy entry point `zss-gui` obok istniejącego `falubaz-zss`.
- Dodano jawne pakowanie plików CSV z `app/zss/data/`, żeby dane pogodowe były dostępne również po instalacji pakietu.
- Rozszerzono `.gitignore` o lokalne katalogi środowiska i artefakty `uv`: `.uv-cache/`, `.uv-python/`, `.venv/`, `.local/` oraz katalog eksportów symulacji.

### Zmieniono
- Podniesiono wersję projektu w `pyproject.toml` do `0.5.0`.
- Uporządkowano konfigurację pakietu tak, aby głównym źródłem kodu był moduł `app.zss`.
- Zaktualizowano adres repozytorium projektu w metadanych `pyproject.toml`.
- Uporządkowano konfigurację Ruff po przeniesieniu testów i modułów do docelowej struktury ZSS.

### Usunięto
- Usunięto zdublowaną, starszą warstwę aplikacji z katalogu `app/`.
- Usunięto zdublowaną, starszą kopię biblioteki `suncalc/` z katalogu głównego; projekt korzysta teraz z wersji vendoryzowanej w `app/zss/_vendor/suncalc/`.
- Usunięto zdublowane testy dla starej struktury `app/` i `suncalc/`, pozostawiając testy dla `falubaz_track_model.zss`.
- Usunięto wygenerowane artefakty z repozytorium: `__pycache__/`, `ZSS.egg-info/`, stare eksporty CSV oraz zdublowane pliki danych pogodowych z katalogu głównego `data/`.

### Naprawiono
- Ograniczono ryzyko przypadkowego commitowania lokalnych środowisk Pythona, cache `uv` i plików eksportowanych przez aplikację.
- Zmniejszono bałagan w repozytorium przez pozostawienie jednego źródła prawdy dla aplikacji ZSS.

Projekt bazuje na bibliotece `suncalc-py` autorstwa Kyle’a Barrona i został rozszerzony o własną aplikację desktopową do wizualizacji 3D położenia słońca, księżyca oraz cienia.

## [0.4.2] - 2026-04-17

### Dodano
- Rozszerzony zestaw testów jednostkowych dla modułów:
  - `app/simulation.py`
  - `app/scene.py`
  - `app/state.py`
  - `app/weather_data.py`
  - `app/render_3d.py`
  - wybranych helperów z `app/gui.py`
  - `suncalc/astro_helpers.py`
- Dodatkowe testy dla analizy punktowej, forcingów atmosferycznych i eksportu danych.
- Obsługę uruchamiania środowiska developerskiego przez `uv`.
- Konfigurację developerską pod `uv sync --group dev`.

### Zmieniono
- Zaktualizowano konfigurację projektu do wersji `0.4.2`.
- Uporządkowano pracę z zależnościami developerskimi i testowymi.
- Usprawniono sposób uruchamiania testów i narzędzi lintujących w środowisku `uv`.
- Doprecyzowano README i komendy instalacyjne pod nowy workflow.

### Naprawiono
- Naprawiono testy niezgodne z Pythonem 3.8+ / 3.10+ w zależności od środowiska.
- Naprawiono testy `test_suncalc.py`, w tym problemy z:
  - `NameError: times is not defined`
  - niestabilnym zachowaniem testów pandasowych przy danych seryjnych i tablicowych.
- Naprawiono błędy Ruff zgłaszane dla:
  - niejawnego `zip()` bez `strict=`,
  - nieużywanych zmiennych w testach.
- Poprawiono stabilność i zgodność testów w różnych środowiskach uruchomieniowych.

## [0.4.1] - 2026-04-17

### Dodano
- Rozszerzony eksport danych z symulacji do CSV o dodatkowe forcingi atmosferyczne.
- Eksport wartości:
  - `air_temperature_k`,
  - `relative_humidity`,
  - `wind_speed_m_per_s`,
  - `precipitation_m_per_s`,
  - `air_pressure_pa`,
  - `shortwave_down_w_per_m2`,
  - `longwave_down_w_per_m2`.
- Dodatkowe pola eksportowe związane z zachmurzeniem:
  - `cloud_cover_raw`,
  - `cloud_unit_raw`.
- Kolumnę `longwave_source` informującą, czy wartość promieniowania długofalowego pochodzi bezpośrednio ze źródła danych, czy z estymacji.
- Rozbudowaną dokumentację techniczną w folderze `docs/` w formie raportu HTML.
- Wykresy i materiały pomocnicze w `docs/assets/`, opisujące działanie modeli i zależności.

### Zmieniono
- Ujednolicono zapis zachmurzenia w eksporcie CSV do postaci znormalizowanej jako `cloud_cover` w zakresie `[0,1]`.
- Zachowano jednocześnie wartości surowe zachmurzenia i ich oryginalne jednostki w osobnych kolumnach eksportu.
- Rozszerzono analizę punktową o dodatkowe forcingi wykorzystywane przy późniejszej analizie danych.
- Zaktualizowano README o aktualny zakres możliwości aplikacji, źródła danych, eksport i dokumentację.

### Naprawiono
- Naprawiono brakujące wartości `longwave_down_w_per_m2` w eksporcie dla przypadków, w których źródło nie zwracało danych bezpośrednio.
- Dodano estymację `longwave_down_w_per_m2` na podstawie temperatury powietrza, wilgotności i zachmurzenia.
- Poprawiono spójność jednostek eksportowanych danych pogodowych i forcingów atmosferycznych.
- Poprawiono kompletność danych eksportowanych po zakończeniu symulacji, tak aby lepiej nadawały się do dalszych analiz.

## [0.4.0] - 2026-04-17

### Dodano
- Integrację z Open-Meteo jako źródłem danych pogodowych dla trybu live i symulacji przyszłych dni.
- Hybrydowy mechanizm pogody: Open-Meteo + lokalne pliki CSV jako fallback.
- Obsługę prognoz opadu, temperatury oraz zachmurzenia w symulacji.
- Wizualizację deszczu na torze i środku toru na podstawie danych pogodowych.
- Wizualizację zachmurzenia wpływającą na odbiór sceny 3D.
- Pionowy suwak czasu po lewej stronie panelu sterowania.
- Przyciski powiększania, pomniejszania i resetu przybliżenia widoku 3D.
- Możliwość obracania sceny 3D myszką z zachowaniem ustawionego kąta widoku po odświeżeniu.
- Analizę punktową toru i środka toru dla każdej klatki symulacji.
- Podgląd danych punktu po najechaniu / wskazaniu punktu na siatce toru.
- Odczyt dla punktów obejmujący m.in.:
  - stan nasłonecznienia lub zacienienia,
  - procentową ekspozycję na słońce,
  - temperaturę powietrza,
  - szacowaną temperaturę punktu,
  - intensywność opadu,
  - zachmurzenie.
- Automatyczny eksport danych z symulacji do pliku CSV po zakończeniu lub zatrzymaniu odtwarzania.
- Folder `exports` do zapisu wyników symulacji.

### Zmieniono
- Przebudowano panel boczny tak, aby poprawnie działał przy maksymalizacji i fullscreen.
- Zmieniono układ sekcji czasu, aby był czytelniejszy i wygodniejszy przy sterowaniu symulacją.
- Rozszerzono status aplikacji o informacje o źródle danych pogodowych i stanie połączenia z Open-Meteo.
- Usprawniono sposób odświeżania danych pogodowych przez użycie cache, aby ograniczyć zbędne zapytania do API.
- Poprawiono obsługę jednostek zachmurzenia dla danych lokalnych i danych Open-Meteo.
- Zachowano styl aplikacji przy jednoczesnym rozszerzeniu funkcjonalności interfejsu.

### Naprawiono
- Naprawiono błędy związane z pobieraniem prognozy z Open-Meteo.
- Naprawiono problem z niepoprawnym zakresem zapytania do forecast API powodującym błąd `400 Bad Request`.
- Naprawiono problem z resetowaniem widoku 3D po każdej aktualizacji sceny.
- Naprawiono błędy związane z obsługą kliknięcia punktów i tablic indeksów z Matplotlib.
- Naprawiono problem z układem interfejsu po przejściu w fullscreen lub po maksymalizacji okna.
- Naprawiono błędy związane z konwersją znaczników czasu i ostrzeżeniami o nanosekundach.

## [0.3.0] - 2026-04-16

### Dodano
- Warstwę pogodową w aplikacji 3D.
- Obsługę lokalnych danych pogodowych z plików CSV w katalogu `data`.
- Wizualizację opadu na scenie w postaci deszczu oraz oznaczeń punktów objętych opadem.
- Wizualizację zachmurzenia nad sceną.
- Przewijany panel boczny oparty o `QScrollArea`, poprawiający działanie interfejsu przy pełnym ekranie.

### Zmieniono
- Rozszerzono interfejs GUI o sekcję **Pogoda**.
- Rozszerzono stan aplikacji o parametry związane z pogodą, statystykami oraz kamerą.
- Zmieniono render sceny 3D tak, aby uwzględniał:
  - opad,
  - chmury,
  - aktualne informacje pogodowe,
  - ustawienia kąta widoku.
- Poprawiono czytelność nakładanych informacji tekstowych na scenie.
- Uporządkowano układ aplikacji dla pracy w trybie pełnoekranowym.

### Techniczne
- Dodano moduł `weather_data` odpowiedzialny za wczytywanie i przygotowanie danych pogodowych.
- Przygotowano obsługę danych lokalnych oraz integrację pod przyszłe źródła online.
- Rozszerzono `render_3d`, `gui` oraz `state` o nowe elementy związane z pogodą i analizą warunków atmosferycznych.
- Zachowano dotychczasową logikę symulacji słońca, księżyca, cienia oraz sceny toru jako bazę aplikacji.

## [0.2.0] - 2026-04-01

### Dodano
- Aplikację desktopową uruchamianą z `main.py`.
- Interfejs GUI oparty o `PySide6`.
- Wizualizację 3D sceny w `matplotlib`.
- Tryb **live** oparty o aktualny czas lokalny.
- Tryb **simulation** do ręcznej symulacji wybranego dnia i godziny.
- Wizualizację położenia słońca nad sceną.
- Wizualizację księżyca w uproszczonej, stylizowanej formie.
- Mapę oświetlenia i zacienienia analizowanego obszaru.
- Obsługę przeszkód terenowych / obiektów wpływających na cień.
- Podsumowanie dnia obejmujące m.in. wschód i zachód słońca.
- Dodatkowe funkcje astronomiczne rozszerzające bazowe możliwości `suncalc`, m.in.:
  - obliczenia w stopniach,
  - kierunek cienia,
  - wektor słońca,
  - uproszczone dane księżyca,
  - podsumowanie dnia.

### Zmieniono
- Rozszerzono projekt z biblioteki obliczeniowej do formy aplikacji wizualnej.
- Uporządkowano kod przez rozdzielenie logiki na moduły:
  - `gui`,
  - `simulation`,
  - `render_3d`,
  - `scene`,
  - `state`.
- Dodano lokalną konwersję czasu na UTC do obliczeń astronomicznych.
- Dodano czytelniejsze opisy kierunków świata i prezentację danych w języku polskim.

### Techniczne
- Zachowano oryginalny moduł `suncalc` jako bazę obliczeniową projektu.
- Dodano własną warstwę aplikacyjną nad biblioteką.
- Przygotowano projekt do dalszego uporządkowania pod publikację na GitHubie.

---

## [0.1.0] - 2026-03-24

### Dodano
- Pierwszą roboczą wersję aplikacji do wizualizacji słońca i cienia.
- Integrację z biblioteką `suncalc-py`.
- Podstawową scenę 3D z torem, przeszkodami i analizą nasłonecznienia.
- Mechanizm uruchamiania lokalnego projektu jako aplikacji Python.

### Uwagi
- Wersja robocza rozwijana na bazie oryginalnego projektu `suncalc-py`.
