Rekord danych (`@dataclass(frozen=True)`) z formacją cenową — dwiema liniami trendu poprowadzonymi przez ostatnie szczyty i dołki swingów (kanał, prostokąt, trójkąt, klin, formacja rozszerzająca się). Tworzy go `PatternDetector._formation`, trafia do `PatternReading.formation`, `CandleChart` rysuje z niego dwie czarne linie, a `Report` wypisuje go w karcie tickera i w `analysis.json`. Jest osobnym blokiem, bo to czysty rekord wspólny dla wykrywania, rysowania i raportu; jako rekord nie ma połączeń na płótnie. Daje własny werdykt **BULL / BEAR / NEUTRAL** (`bias`), tak jak formacje świecowe; **nie wpływa** na score ani rekomendację.

## name
Polska nazwa formacji (`str`), np. `"Kanał wzrostowy"`, `"Trójkąt symetryczny"`. Pełna lista i reguły w dokumentacji `PatternDetector` (sekcja „Formacja cenowa”).

## code
Krótki kod do legendy wykresu (`str`): `PROST`, `KAN↑`, `KAN↓`, `TR↑`, `TR↓`, `TR=`, `KL↑`, `KL↓`, `ROZSZ`.

## direction
Wymowa formacji: `"BULL"`, `"BEAR"` albo `"NEUTRAL"` (np. klin zwyżkujący jest BEAR, bo zwykle kończy się spadkiem).

## bias
Werdykt formacji cenowej na dziś (właściwość, `str`): **wybicie decyduje** — `wybicie górą` → `"BULL"`, `wybicie dołem` → `"BEAR"`; gdy cena jest w formacji albo linie minęły wierzchołek — kierunek samej formacji (`direction`). Przykład: kanał wzrostowy z wybiciem dołem daje BEAR. Pokazywany w ramce i tytule wykresu, w kolumnie `FORMATION` tabeli, w CSV (`formation_bias`) i w JSON.

## INSIDE / BREAKOUT_UP / BREAKOUT_DOWN / PAST_APEX
Stałe klasy z możliwymi wartościami `position`; `PatternDetector` je ustawia, `bias` je czyta.

## start_bars_ago
Świeca pierwszego swingu formacji, liczona wstecz od dzisiejszej (`int ≥ 1`). Od niej zaczynają się rysowane linie; długość formacji w świecach = `start_bars_ago + 1`.

## upper_start / upper_end
Cena górnej linii (przez szczyty) na świecy `start_bars_ago` i na dzisiejszej świecy (`float`, waluta notowania).

## lower_start / lower_end
To samo dla dolnej linii (przez dołki). Gdy `upper_end < lower_end`, linie zbieżne minęły wierzchołek.

## swings
Liczba swingów, na których dopasowano linie (`int`, od 4 do `PatternDetector.formation_swings`).

## position
Położenie dzisiejszego zamknięcia: `"cena w formacji"`, `"wybicie górą"`, `"wybicie dołem"` albo `"linie przecięte (za wierzchołkiem)"`.

## upper_at(bars_ago) / lower_at(bars_ago)
Cena górnej/dolnej linii na dowolnej świecy (interpolacja liniowa między początkiem a dniem dzisiejszym; poza tym zakresem — ekstrapolacja).

## summary()
Jedna linia do karty tickera: werdykt `bias`, nazwa, kierunek, liczba swingów, długość w świecach i położenie ceny.

## to_dict()
Słownik do `analysis.json`: `name`, `code`, `direction`, `bias`, `start_bars_ago`, `upper` i `lower` (pary cen: początek, dziś), `swings`, `position`.
