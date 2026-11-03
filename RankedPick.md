Rekord jednego miejsca w rankingu tematu: kandydat (StockCandidate), jego wynik 0–100 i powody. Tworzy go ThemeRanker, czyta ScreenerReport (tabele, JSON, CSV) i ScreenerChart (wykres). Czysty model danych — niepodłączony na kanwie.

## theme
Nazwa tematu z `ScreenerSettings.THEMES`.

## rank
Miejsce w temacie, od 1 (najlepsze) do `top_n`.

## candidate
StockCandidate z surowymi danymi i czynnikami.

## score
Wynik 0–100: średnia ważona percentyli czynników spółki w obrębie tematu × 100. 50 = środek tematu, 100 = najlepsza w temacie we wszystkich czynnikach. Ranking względny — nie jest prawdopodobieństwem wzrostu.

## coverage
Udział wag czynników, dla których były dane (0–1). Poniżej `min_coverage` spółka nie trafia do rankingu.

## factor_ranks
`czynnik -> percentyl 0..1` w temacie (0 = najgorsza, 1 = najlepsza).

## strengths
Do 3 najważniejszych (wg wagi) czynników z percentylem ≥ 0.7 — kolumna „ATUTY”.

## weaknesses
Do 3 najważniejszych czynników z percentylem ≤ 0.3 — linia „ryzyka”.

## ticker
Skrót do `candidate.ticker`.

## to_dict
Słownik do JSON (wynik, pokrycie, atuty, ryzyka, percentyle i dane kandydata).
