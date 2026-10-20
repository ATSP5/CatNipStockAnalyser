Draws the candlestick chart at whatever horizon the run asked for, and saves it as a PNG in the output directory.

Four stacked panels share one x axis: candles with the 20, 50 and 200 moving averages and the Bollinger envelope, then volume, then RSI, then MACD. The rating appears in the top right and the composite score in the title, so a chart read on its own still carries the verdict.

Candles are plotted against their position in the series rather than against real time. That is deliberate — plotting against real timestamps opens blank stretches across every weekend and, on an intraday horizon, across every overnight gap, which squeezes the actual trading into a fraction of the width.

The matplotlib Agg backend is selected on import, so this never tries to open a window and is safe to run headless.

Inside CatNip the run engine replaces `plt.show()` with its own capture, which puts the figure straight into the **Output** tab. The block calls `show()` only when it has been replaced that way — calling the real Agg version outside CatNip would do nothing but warn that it cannot display anything.

## draw

`draw(verdict, settings, forecast=None, note=None)` — z `forecast` (PriceForecast) rysuje też prognozę AI; `note` to powód jej braku, pokazywany na wykresie.

Renders a verdict and saves it and returns the file path. The class method is the intended entry point. A verdict with fewer than 2 candles (NO DATA) gets an empty chart from `_render_empty`, so its analysis is still visible.

## render

Does the work behind `draw` on an already-constructed instance.

## UP / DOWN

The candle colours — teal for a close at or above the open, red below.

## RATING_COLOUR

Maps each verdict to the colour it is printed in, green through amber to red.

## path

Where the PNG was written, set once `render` has run. The filename is `<TICKER>_<horizon>.png`, so charts for different horizons sit side by side rather than overwriting each other.

## Panel layout

The price panel takes a little over three times the height of the others, since it carries the candles, three moving averages and the Bollinger envelope at once. A candle with no body — where open and close match exactly — is drawn as a hairline so that a doji stays visible rather than disappearing.

The number of candles drawn comes from `Settings.CHART_CANDLES`, defaulting to the most recent 180. The indicators are calculated over the full history and only then trimmed for drawing, so a 200-candle average is still correct on the left-hand edge of the chart.

## Time axis

Roughly ten evenly spaced candles are labelled with their real timestamps, formatted with the time included on intraday horizons and as a plain date otherwise.

## forecast

PriceForecast z bloku PriceForecaster albo `None`. Gdy jest, panel ceny ciągnie się za ostatnią świecę o `forecast.steps` pozycji: fioletowa linia to mediana prognozy (start od ostatniego zamknięcia), jasne pasmo to przedział 10–90%. Tytuł dostaje dopisek `forecast N candles: ±x%` (zmiana mediany na końcu horyzontu względem ostatniego zamknięcia). `None` → wykres jak dawniej.

## _today_line

Pionowa kreskowana linia między ostatnią prawdziwą świecą a pierwszą prognozowaną, na wszystkich widocznych panelach (cena, wolumen, RSI, MACD), z podpisami „history” / „forecast”. Rysowana tylko wtedy, gdy jest prognoza.

## Oś czasu z prognozą

Etykiety osi obejmują też przyszłe świece — ich daty pochodzą z `forecast.timestamps` (dni sesyjne dla `1d`, co 7 dni dla `1wk`/`5d`, pierwsze dni miesięcy dla `1mo`; dla interwałów śróddziennych odstępy są równe i pomijają godziny sesji, więc daty są przybliżone).

## SUSPECT_TEXT

Napis `! Możliwe błędne dane`, rysowany na czerwono pod rekomendacją w prawym górnym rogu (`_suspect_mark`), gdy `MarketData.has_suspect_data()`, czyli gdy jakąś wartość Yahoo trzeba było pominąć jako niemożliwą (np. free float ASML 5520%). Szczegóły są w karcie tickera w terminalu. Wartości, które udało się poprawić (np. P/B po przeliczeniu waluty), nie dają tego napisu.

## _render_empty

Wykres dla tickera bez danych: tytuł `<TICKER> -- <interwał> candles | score n/a`, etykieta NO DATA i na środku „Brak danych” z powodem (`Recommendation.missing_reason()`). Zapisywany pod tą samą nazwą `<TICKER>_<interwał>.png` i pokazywany w zakładce Output jak każdy inny.

## FORECAST

Kolor prognozy (`#7b1fa2`).

## note

Tekst (albo `None`) pokazywany w czerwonej ramce w prawym dolnym rogu panelu ceny, gdy prognoza była zamówiona (`future_horizon > 0`), ale jej nie ma — np. `forecast off: No module named 'torch' -- install the pip package chronos-forecasting`. Przy narysowanej prognozie jest ignorowany. Dostarcza go Report (`_forecast_note`).

## Pasmo 24–76%

Gdy `forecast.has_inner()`, wewnątrz jasnego pasma 10–90% rysowane jest ciemniejsze pasmo `inner_low`–`inner_high` (domyślnie 24–76%, w legendzie „median ±26 pp”), też startujące od ostatniego zamknięcia.
