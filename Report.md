The entry point, and the block marked as main. Constructing it runs the whole pipeline: fetch every ticker, score it, draw it, print the verdicts and write the files.

The output comes in two parts. A ranked summary table puts the strongest buy at the top and the strongest sell at the bottom, with the three block scores shown separately so it is visible *why* a call came out where it did. Then a detailed card per ticker gives the price and 52-week range, each block's score and coverage, the three strongest arguments in each direction with the reasoning behind them, any caveats, and the path to the chart.

Anything that fails is collected rather than fatal, and nothing is hidden. A ticker that cannot be fetched, or that yields too little history, still appears: as an empty **NO DATA** analysis at the bottom of the table (score `n/a`, DATA 0%), with its card listing every block as `brak danych`, an empty chart, rows in JSON/CSV, and a terminal note with the reason and a hint to check the Yahoo symbol. While fetching, the console also prints `brak danych dla <TICKER> -- <powód>; pokazuję pustą analizę`. Only a crash inside the analysis itself ends up in `skipped`.

## Settings

Pass an already-built `Settings` to control the run. Left out, it constructs one, which picks up the canvas defaults and any command-line arguments.

## draw

Whether to render charts. Defaults to the setting, and can be overridden per run — turning it off makes a large watchlist noticeably faster.

## quiet

Suppresses printing while still computing everything and writing the files, for when the result is going to be read through `as_dict` instead.

## verdicts

Every `Recommendation` produced, already sorted with the best call first.

## skipped

`(ticker, reason)` for tickers whose analysis raised an exception. Tickers without data are no longer skipped — they are NO DATA verdicts.

## charts

Ticker to chart path, for those that were drawn.

## backtests

Ticker to `Backtest`, when `Settings.backtest` is on. Each card prints its summary, the summary table adds a pooled IC across all tickers, and both files carry the numbers.

## run

Executes the pipeline. Called from the constructor, so it does not normally need calling directly.

## print_summary

The ranked table. The leading mark is a compact form of the call — `++` for STRONG BUY down to `--` for STRONG SELL, `?` for NO DATA — so the shape of a watchlist is readable at a glance. A trailing `!` (`SUSPECT_MARK`) marks a ticker with possibly wrong Yahoo data. Under the table, `_print_data_notes` lists every NO DATA ticker with its reason and explains the `!`.

## SUSPECT_MARK

`"!"`: znak „możliwe błędne dane”. Pojawia się przy tickerze w tabeli i w nagłówku sekcji karty, gdy `MarketData.has_suspect_data()`.

## _print_data_quality

W karcie tickera, przed argumentami za i przeciw, drukuje dwie sekcje: **„Dane poprawione”** (`market.data_fixes`, czyli co Yahoo podał, ile wyszło po przeliczeniu i dlaczego) oraz **„! Możliwe błędne dane -- pominięte w ocenie”** (`market.data_warnings`, czyli czego nie dało się naprawić). Ticker z poprawnymi danymi nie ma żadnej z nich.

## print_details

The per-ticker cards. For NO DATA the card shows `score n/a`, the reason (`Brak danych: …`) and `n/a brak danych` for each of the three blocks.

## write_files

Writes `analysis.json` and `analysis.csv` to the output directory. The JSON carries the complete structure, every individual signal included, and is the right thing to read from another tool. The CSV carries one row per ticker with the headline numbers, for a spreadsheet.

Inside CatNip it also hands the table to the run engine through `csv.show`, so the summary appears in the **Output** tab beside the charts. That function only exists inside the engine, so outside it the call is skipped.

## as_csv

The summary table as CSV text, one row per ticker. Used for both the file and the Output tab.

## best

The strongest buy candidate, or `None` when nothing could be analysed.

## by_rating

Every verdict carrying a given label, e.g. `by_rating("STRONG BUY")`.

## as_dict

The whole run keyed by ticker, for using this block's output from another block rather than reading it off the console.

## forecaster

Argument konstruktora: PriceForecaster (wejście `Forecaster` ← blok PriceForecaster). `None` → raport bez prognoz. Uruchomienie bloku jako main (`__main__`) buduje `Settings()` i `PriceForecaster(settings)` i przekazuje je do Report.

## forecasts

Słownik ticker → PriceForecast dla tickerów, dla których prognoza się udała. Błąd prognozy jednego tickera trafia do jego notatek (`forecast: …`) i nie przerywa reszty.

## Prognoza w wynikach

- Karta tickera: linia `Forecast (amazon/chronos-2, N candles, to <data>): median … (±x%), 10-90% band … - …` i pod nią `24-76% band … - …`.
- `analysis.json`: `future_horizon` w nagłówku i `forecast` w każdym wyniku (`PriceForecast.to_dict()`).
- `analysis.csv`: kolumny `data_warnings` i `data_fixes` (komunikaty rozdzielone ` | `), a dla NO DATA pusty `score`. Kolumny `forecast_steps`, `forecast_median`, `forecast_low`, `forecast_high`, `forecast_inner_low`, `forecast_inner_high` (pasmo 24–76%), `forecast_change_pct` (puste, gdy prognozy nie ma).
- Wykres: prognoza jest przekazywana do `CandleChart.draw`.

## forecast_status()

Stan prognozy dla całego uruchomienia (z `PriceForecaster.status()`, albo `forecast off: no PriceForecaster connected`). Wypisywany pod tabelą podsumowania i zapisywany w `analysis.json` jako `forecast_status`, więc pusta kolumna prognozy w CSV zawsze ma wyjaśnienie.

## _forecast_note(forecast)

Powód braku prognozy przekazywany do `CandleChart.draw(note=…)`; `None`, gdy prognoza jest albo `future_horizon` = 0.
