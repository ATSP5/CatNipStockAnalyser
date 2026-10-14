The entry point, and the block marked as main. Constructing it runs the whole pipeline: fetch every ticker, score it, draw it, print the verdicts and write the files.

The output comes in two parts. A ranked summary table puts the strongest buy at the top and the strongest sell at the bottom, with the three block scores shown separately so it is visible *why* a call came out where it did. Then a detailed card per ticker gives the price and 52-week range, each block's score and coverage, the three strongest arguments in each direction with the reasoning behind them, any caveats, and the path to the chart.

Anything that fails is collected rather than fatal. A ticker that cannot be fetched, or that yields too little history, is listed as a skipped line with the reason, and the rest of the run carries on.

## Settings

Pass an already-built `Settings` to control the run. Left out, it constructs one, which picks up the canvas defaults and any command-line arguments.

## draw

Whether to render charts. Defaults to the setting, and can be overridden per run — turning it off makes a large watchlist noticeably faster.

## quiet

Suppresses printing while still computing everything and writing the files, for when the result is going to be read through `as_dict` instead.

## verdicts

Every `Recommendation` produced, already sorted with the best call first.

## skipped

`(ticker, reason)` for everything that could not be analysed.

## charts

Ticker to chart path, for those that were drawn.

## backtests

Ticker to `Backtest`, when `Settings.backtest` is on. Each card prints its summary, the summary table adds a pooled IC across all tickers, and both files carry the numbers.

## run

Executes the pipeline. Called from the constructor, so it does not normally need calling directly.

## print_summary

The ranked table. The leading mark is a compact form of the call — `++` for STRONG BUY down to `--` for STRONG SELL — so the shape of a watchlist is readable at a glance.

## print_details

The per-ticker cards.

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
- `analysis.csv`: kolumny `forecast_steps`, `forecast_median`, `forecast_low`, `forecast_high`, `forecast_inner_low`, `forecast_inner_high` (pasmo 24–76%), `forecast_change_pct` (puste, gdy prognozy nie ma).
- Wykres: prognoza jest przekazywana do `CandleChart.draw`.

## forecast_status()

Stan prognozy dla całego uruchomienia (z `PriceForecaster.status()`, albo `forecast off: no PriceForecaster connected`). Wypisywany pod tabelą podsumowania i zapisywany w `analysis.json` jako `forecast_status`, więc pusta kolumna prognozy w CSV zawsze ma wyjaśnienie.

## _forecast_note(forecast)

Powód braku prognozy przekazywany do `CandleChart.draw(note=…)`; `None`, gdy prognoza jest albo `future_horizon` = 0.
