Drugi main projektu (`main_2.py`): skaner sektorowy, który z amerykańskiej giełdy wybiera 10 spółek w każdym temacie gospodarki (AI, hi-tech, półprzewodniki, farmacja, biotech, ropa i gaz, OZE, energia jądrowa, finanse, przemysł, konsumpcja, surowce, REIT…) z największą szansą na wzrost w horyzoncie 1–6 miesięcy. To nie lista „top gainers”: ranking łączy czynniki o udokumentowanej skuteczności na tym horyzoncie (momentum 12-1 i 6-1, bliskość szczytu 52 tyg., ceny docelowe i rekomendacje analityków, oczekiwany wzrost EPS, wzrost, jakość, wycena do wzrostu, niska zmienność) z karą za świeże przegrzanie, plus ocenę StockAnalysera i prognozę Chronos-2. Blok tylko orkiestruje — dane, czynniki, ranking i wykresy robią bloki podłączone do jego wejść. Wynik jest rankingiem względnym w temacie, nie gwarancją ani poradą inwestycyjną.

## screener_settings
ScreenerSettings (wejście): opis przebiegu, `top_n`, `factor_weights`, katalog wyników.

## universe
SectorUniverse (wejście): `themes()` i `all_tickers()` — kto jest kandydatem.

## universe_fetcher
UniverseFetcher (wejście): `fetch_all()` — równoległe pobranie danych z Yahoo.

## factor_model
FactorModel (wejście): `measure()` — czynniki każdej spółki, liczone raz, nawet gdy spółka jest w kilku tematach.

## theme_ranker
ThemeRanker (wejście): `rank()` — percentyle w temacie, filtry, top N.

## screener_chart
ScreenerChart (wejście): `draw()` — wykres słupkowy na temat.

## quiet
`True` wycisza wydruk w terminalu (pliki i tak powstają). Domyślnie `False`.

## candidates / picks / rejected / charts
Wyniki przebiegu: `ticker -> StockCandidate`, `temat -> [RankedPick]`, `temat -> [(ticker, powód)]`, `temat -> ścieżka PNG`.

## run
Cały skan: uniwersum → pobranie → czynniki → ranking i wykres każdego tematu → tabele → pliki. Czas: zwykle kilka minut przy ~350 tickerach (zależy od Yahoo i `fetch_workers`). Zwraca `self`.

## print_themes
Tabela na temat: miejsce, ticker, nazwa, WYNIK (0–100), cena, momentum 6-1, potencjał do ceny docelowej (CEL), oczekiwany wzrost EPS (EPS F), prognoza AI, atuty; pod spodem ryzyka i lista odrzuconych z powodem.

## write_files
Zapisuje `output/screener/screener.json` (pełne dane, percentyle, odrzucone) i `screener.csv` (jeden wiersz na spółkę w temacie, wszystkie czynniki); w CatNip pokazuje CSV w zakładce Output.

## as_csv
Tabela CSV jako tekst.
