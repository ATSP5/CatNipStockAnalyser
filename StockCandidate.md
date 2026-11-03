Rekord jednej przeskanowanej spółki: dane i surowe czynniki 1–6 mies., zmierzone raz przez FactorModel i współdzielone przez wszystkie tematy, w których ticker występuje (np. NVDA w AI i w półprzewodnikach). Czysty model danych — nie jest podłączony na kanwie; importują go FactorModel i RankedPick.

## ticker
Symbol Yahoo, wielkie litery (np. `NVDA`, `BRK-B`).

## name
Pełna nazwa spółki z Yahoo (albo ticker, gdy brak).

## industry
Branża Yahoo (albo sektor, gdy branży brak).

## price
Ostatnie zamknięcie w walucie notowań; `None` bez danych. Filtr `min_price`.

## currency
Waluta notowań, zwykle `USD`.

## market_cap
Kapitalizacja w walucie notowań (z Yahoo albo cena × liczba akcji). Filtr `min_market_cap`.

## dollar_volume
Średni dzienny obrót = średni wolumen × cena. Filtr `min_dollar_volume`.

## bars
Liczba dziennych świec w historii. Filtr `min_bars`.

## rating
Werdykt StockAnalysera (`STRONG BUY` … `STRONG SELL`, `NO DATA`) policzony z wagami `ANALYSIS_WEIGHTS` — informacyjnie; do wyniku wchodzi jego liczba jako czynnik `analysis_score`.

## factors
Słownik `czynnik -> wartość` (ułamki, nie procenty; orientacja „więcej = lepiej”, tzn. zmienność, PEG, zwrot 1 mies. i średnia rekomendacja są z minusem). `None` = brak danych; taki czynnik nie dostaje wagi.

## forecast_change_pct
Zmiana mediany prognozy Chronos-2 na końcu `forecast_steps` względem ostatniego zamknięcia, w procentach; `None` gdy prognoza wyłączona lub niedostępna.

## problems
Lista problemów z danymi (błędy pobierania, analizy, prognozy) — do JSON.

## value(factor)
Wartość czynnika albo `None`.

## to_dict
Słownik do JSON/CSV.
