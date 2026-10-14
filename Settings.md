Holds one run's configuration: the tickers to look at, how wide a candle should be, and how much each of the three analysis blocks counts toward the final call. Every other block reads its settings from an instance of this class, so this is the one place to change what a run does.

Values written on the canvas act as defaults. When the project is run from a terminal through `run.py`, command-line arguments override them, and the `STOCKANALYSER_TICKERS` environment variable overrides the ticker list.

## TICKERS

The default list of symbols to analyse, e.g. `["AAPL", "MSFT", "NVDA"]`. Yahoo symbols are accepted as-is, so non-US listings (`0700.HK`, `SAP.DE`), indices (`^GSPC`) and crypto pairs (`BTC-USD`) all work.

## HORIZON

The width of a single candle, and the default is `"1d"` — one candle per trading day. Valid values are `1m`, `2m`, `5m`, `15m`, `30m`, `60m`, `1h`, `90m`, `1d`, `5d`, `1wk`, `1mo` and `3mo`.

The horizon decides the timeframe being judged. Every indicator window is counted in candles, so a 50-candle average means fifty days at `1d` and fifty hours at `1h`.

## LOOKBACK

How far back the history reaches, as a Yahoo period string (`6mo`, `2y`, `max`). Leave it as `""` to let the horizon choose a sensible window for itself. Yahoo caps intraday history — a minute chart cannot reach back further than seven days — and `HORIZONS` records each cap.

## WEIGHTS

`None` by default, which lets the horizon choose the weights from `HORIZON_WEIGHTS`. Set a dict such as `{"technical": 0.6, "valuation": 0.3, "supply": 0.1}`, or pass `--weights 0.6,0.3,0.1`, to pin them for every horizon. They do not need to add up to 1; they are normalised. Set one to `0` to switch that view off entirely.

## HORIZON_WEIGHTS

Default block weights per horizon. P/E, ROE, market cap and ownership have practically no predictive power for the next candle, so intraday and `1d` runs are 90% technical, 10% valuation and 0% supply. `5d`/`1wk` move to 65/25/10, `1mo` to 45/35/20, and `3mo` to 30/45/25. Intraday horizons use the `1d` weights (`SHORT_TERM_WEIGHTS`).

## horizon_weights

The default weights for a given horizon.

## BACKTEST

Whether the report runs the walk-forward backtest of the technical score. Turn it off with `--no-backtest`.

## COST_BPS

The one-way trading cost the backtest charges on every entry and exit, in basis points. Default 10.

## HORIZONS

Maps each interval to `(default lookback, Yahoo's cap, bars per year, label)`. The bars-per-year figure is what lets `bars_for_days` convert a span in days into a number of candles at the current horizon.

## RATING_BANDS

The score thresholds that produce the five verdicts, checked from the top down: `+45` and over is STRONG BUY, `+15` is BUY, `-15` is HOLD, `-45` is SELL, and anything lower is STRONG SELL.

## resolved_lookback

The history window this run will actually request: `LOOKBACK` when it is set, otherwise the horizon's own default.

## bars_for_days

How many candles at the current horizon roughly span the given number of calendar days. The technical block uses it to ask for "about ninety days of momentum" without caring which horizon is in force.

## normalised_weights

The block weights rescaled to add up to 1.

## rating_for

Maps a composite score onto its label. A class method, so it can be called without an instance.

## ensure_output_dir

Creates the output directory if it is missing and returns its path. Charts, `analysis.json` and `analysis.csv` are all written there.

## describe

A one-line summary of the run, printed as the report's banner. Ends with `forecast N candles` or `forecast off`.

## ignored

Command-line arguments that matched neither a flag nor a plausible ticker. The report prints them so a typo is visible rather than silently dropped.

## FUTURE_HORIZON / future_horizon (FutureHorizon)

Horyzont prognozy AI: ile świec interwału `horizon` za ostatnią prawdziwą świecą prognozuje model Chronos-2 (blok PriceForecaster). Dla `horizon = '1d'` i `future_horizon = 30` to 30 dni sesyjnych (~6 tygodni); dla `'1wk'` — 30 tygodni.

- Typ: `int`, liczba świec. Domyślnie `FUTURE_HORIZON = 30`.
- Ustawiany w INITIALISERZE (argument konstruktora `future_horizon`; `None` = wartość domyślna), w kodzie (`FUTURE_HORIZON`) albo z terminala: `--future 20`.
- Zakres: `0 … MAX_FUTURE_HORIZON` (512). `0` wyłącza prognozę (wykres bez pasma i bez linii „dziś”). Poza zakresem → `ValueError` przy tworzeniu Settings.
- Wpływ: dłuższy horyzont wydłuża wykres w prawo i poszerza pasmo 10–90% (niepewność rośnie z odległością); czas liczenia rośnie nieznacznie. Prognozy dalsze niż natywny horyzont modelu są liczone autoregresyjnie i są mniej wiarygodne.

## MAX_FUTURE_HORIZON

Górna granica `future_horizon` (512 świec) — chroni przed przypadkowo ogromnym horyzontem, przy którym prognoza traci sens.

## settings

Wyjście bloku: zwraca tę instancję (wcześniej zwracało `None`). Podłączone do Report i PriceForecaster.
