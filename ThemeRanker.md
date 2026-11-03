Układa ranking kandydatów jednego tematu. Każdy czynnik zamienia na percentyl w obrębie tematu (0 = najgorszy, 1 = najlepszy) — bank porównywany jest z bankami, biotech z biotechami, a pojedyncza skrajna liczba nie zdominuje wyniku. Wynik = średnia ważona percentyli po czynnikach, dla których spółka ma dane, × 100. Osobny blok, bo to sama arytmetyka rankingu, niezależna od źródła danych i od prezentacji. Wejście `screener_settings`, wyjście `theme_ranker` do ScreenerReport.

## screener_settings
ScreenerSettings: filtry (`min_bars`, `min_price`, `min_market_cap`, `min_dollar_volume`, `min_coverage`), `factor_weights`, `top_n`, `label()`.

## theme_ranker
Wyjście bloku: zwraca samą instancję, bo ScreenerReport woła `rank` raz na temat z jego własną grupą kandydatów.

## rank(theme, candidates)
Zwraca `(picks, rejected)`: `picks` — do `top_n` obiektów RankedPick posortowanych malejąco po wyniku; `rejected` — `[(ticker, powód)]` dla spółek odrzuconych przez filtry lub za małe pokrycie danych. Kolejność filtrów: historia, cena, kapitalizacja, obrót, pokrycie. Percentyle liczone są tylko wśród spółek, które przeszły filtry; remisy dostają średnią pozycję; jedyna wartość w temacie dostaje 0.5. Zmiana wag w `FACTOR_WEIGHTS` przesuwa kolejność; zaostrzenie filtrów skraca listy i zmienia percentyle pozostałych.
