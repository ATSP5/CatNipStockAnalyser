Konfiguracja skanera sektorowego (drugi main, `ScreenerReport`): jakie tematy gospodarki, którzy kandydaci w każdym z nich, jakie filtry i z jakimi wagami liczony jest wynik na horyzont 1–6 miesięcy. Wydzielona w osobny blok, żeby wszystkie „pokrętła” skanera były w jednym miejscu na kanwie, a bloki robocze (SectorUniverse, UniverseFetcher, FactorModel, ThemeRanker, ScreenerChart, ScreenerReport) dostawały ją przez wejście `screener_settings`. Sama dostaje na wejściu `Settings` (blok analizatora) i robi z niego kopię dopasowaną do skanu (`analysis_settings`), więc analiza pojedynczych spółek w obu mainach liczy się tym samym kodem.

## settings
Instancja `Settings` z bloku Settings (wejście). Nie jest modyfikowana — skaner pracuje na jej kopii z `analysis_settings()`. Z niej bierze m.in. `output_dir` (domyślnie `output`).

## THEMES
Słownik `temat -> {"tickers": [...], "industries": [...]}`. `tickers` to ręcznie dobrane spółki notowane w USA (NYSE/Nasdaq, także ADR-y), `industries` to słowa kluczowe branż Yahoo (np. `"Semiconductors"`, `"Oil & Gas"`, `"REIT"`), których największe spółki SectorUniverse dokłada do listy. Domyślnie 20 tematów: AI, hi-tech/oprogramowanie, półprzewodniki, sprzęt, cyberbezpieczeństwo, internet/media, telekomunikacja, farmacja, biotechnologia, medtech, ropa i gaz, OZE, energia jądrowa/uran, energetyka, finanse, przemysł/obronność, konsumpcja cykliczna i podstawowa, surowce, REIT. Temat bez kandydatów daje pustą tabelę; pusty słownik → `ValueError`. Dodanie tematu = nowa tabela i nowy wykres; więcej tickerów = dłuższy czas pobierania (ok. 1–2 s na ticker przy 8 wątkach).

## themes
Słownik tematów użyty w tym przebiegu (argument konstruktora, domyślnie `THEMES`).

## TOP_N / top_n
Ile spółek pokazać w każdym temacie, domyślnie `10`. Liczba całkowita ≥ 1 (mniej → `ValueError`). Gdy filtry przejdzie mniej spółek, tabela jest krótsza.

## MAX_CANDIDATES_PER_THEME / max_candidates_per_theme
Maks. liczba kandydatów w temacie (najpierw lista ręczna, potem dodatki z Yahoo), domyślnie `30`. `0` = bez limitu. Większa wartość = szerszy wybór, dłuższe pobieranie.

## SCREEN_SIZE_PER_INDUSTRY / screen_size_per_industry
Ile największych (wg kapitalizacji) spółek Yahoo dokłada z każdej dopasowanej branży, domyślnie `12`, sensownie 1–100 (Yahoo zwraca maks. 250).

## USE_YAHOO_SCREENER / use_yahoo_screener
`True` (domyślnie) — uzupełnia tematy o spółki z wyszukiwarki Yahoo; `False` — tylko listy ręczne (szybciej, w pełni powtarzalnie).

## MIN_MARKET_CAP / min_market_cap
Minimalna kapitalizacja w USD, domyślnie `2e9` (2 mld). Mniejsze spółki są odrzucane i wypisywane jako „odrzucone”. Używana też jako dolny próg w zapytaniu do Yahoo.

## MIN_DOLLAR_VOLUME / min_dollar_volume
Minimalny średni dzienny obrót w USD (średni wolumen × cena), domyślnie `20e6`. Chroni przed mało płynnymi walorami.

## MIN_PRICE / min_price
Minimalna cena akcji, domyślnie `5.0` USD — odcina penny stocks.

## MIN_BARS / min_bars
Minimalna liczba dziennych świec, domyślnie `130` (~6 mies.). Świeże debiuty bez historii są odrzucane, bo momentum nie da się policzyć.

## MIN_COVERAGE / min_coverage
Minimalny udział wag czynników, dla których są dane (0–1), domyślnie `0.60`. Spółka z mniejszym pokryciem nie jest rankowana („za mało danych”).

## MIN_ANALYSTS / min_analysts
Minimalna liczba opinii analityków, żeby liczyć `analyst_upside` i `analyst_rating`, domyślnie `3`. Mniej → oba czynniki puste.

## FETCH_WORKERS / fetch_workers
Liczba równoległych pobrań z Yahoo, domyślnie `8` (praca I/O; ten komputer ma 16 wątków logicznych). ≥ 1; powyżej ~10 Yahoo zaczyna ograniczać zapytania (błędy 429 → puste dane tickera).

## FORECAST_STEPS / forecast_steps
Horyzont prognozy Chronos-2 w świecach dziennych, domyślnie `126` (~6 mies.), zakres 0–512 (poza → `ValueError`). `0` wyłącza prognozę i usuwa czynnik `forecast`. Prognoza wymaga pakietu `chronos-forecasting` (torch); bez niego czynnik jest pusty, a skaner działa dalej.

## FACTOR_WEIGHTS / factor_weights
Waga każdego czynnika w wyniku. Wagi nie muszą sumować się do 1 (są normalizowane po czynnikach dostępnych dla spółki); ujemne/zerowe są pomijane, suma dodatnich musi być > 0. Większa waga = czynnik silniej przesuwa ranking. Domyślnie najwięcej waży momentum 12-1 (0.14) i potencjał do ceny docelowej analityków (0.10) — to czynniki z najlepiej udokumentowaną skutecznością na 1–6 mies.; prognoza AI tylko 0.03, bo model zna wyłącznie historię cen.

## FACTOR_LABELS
Polskie nazwy czynników do tabel („atuty”, „ryzyka”) i CSV.

## ANALYSIS_WEIGHTS
Wagi bloków analizatora (technical 0.45 / valuation 0.35 / supply 0.20) dla `Recommendation` liczonej w skanerze — mieszanka z `Settings.HORIZON_WEIGHTS["1mo"]`, pasująca do horyzontu miesięcy zamiast dni.

## OUTPUT_SUBDIR
Podkatalog wyników w `settings.output_dir`, domyślnie `screener` → `output/screener/`.

## DRAW_CHART / draw_chart
`True` — ScreenerChart rysuje wykres słupkowy każdego tematu; `False` — tylko tabele i pliki.

## screener_settings
Wyjście bloku: zwraca samą instancję. Celowo cały obiekt, a nie pojedyncze wartości — każdy blok skanera czyta z niego inne pola, a `analysis_settings()` musi być jedną wspólną kopią dla wszystkich.

## analysis_settings
Zwraca (raz utworzoną, potem tę samą) kopię `Settings`: świece `1d`, historia `2y` (wystarcza na momentum 12-1 i SMA200), wagi `ANALYSIS_WEIGHTS`, `future_horizon = forecast_steps`, bez wykresów świecowych i backtestu, katalog wyjściowy skanera.

## output_dir / ensure_output_dir
Ścieżka katalogu wyników skanera; `ensure_output_dir` dodatkowo go tworzy.

## label(factor)
Polska nazwa czynnika (albo jego klucz, gdy brak etykiety).

## describe
Jedna linia opisu przebiegu do nagłówka raportu.
