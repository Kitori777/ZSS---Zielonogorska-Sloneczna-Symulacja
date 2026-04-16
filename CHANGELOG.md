# Changelog


Projekt bazuje na bibliotece `suncalc-py` autorstwa Kyle’a Barrona i został rozszerzony o własną aplikację desktopową do wizualizacji 3D położenia słońca, księżyca oraz cienia.

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
