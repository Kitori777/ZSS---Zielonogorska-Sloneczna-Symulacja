# Changelog


Projekt bazuje na bibliotece `suncalc-py` autorstwa Kyle’a Barrona i został rozszerzony o własną aplikację desktopową do wizualizacji 3D położenia słońca, księżyca oraz cienia.

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
