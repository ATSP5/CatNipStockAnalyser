Technical indicator maths, written directly on pandas so the project needs no TA-Lib or other native dependency. Every function takes and returns pandas objects and is safe on short history: when there are not enough candles to fill a window the result is `NaN` rather than an exception, and the analysis blocks skip that signal.

All windows are counted in candles, never in days. At the default `1d` horizon a 14-candle RSI is the familiar 14-day RSI; at `1h` the same code gives a 14-hour RSI. The horizon is what decides the timeframe.

## sma

Simple moving average. Returns `NaN` until the window is full, so a 200-candle average on 150 candles of history is honestly empty rather than quietly computed from less.

## ema

Exponentially weighted moving average, which reacts faster to recent candles than `sma`.

## rsi

Wilder's Relative Strength Index over `window` candles, on a 0–100 scale. Below 30 is conventionally oversold, above 70 overbought. A stretch with no down-candles at all is reported as a legitimate 100 rather than a gap.

## macd

Moving Average Convergence Divergence. Returns `(macd line, signal line, histogram)`. The histogram is the gap between the first two: its sign gives direction, and a change of sign is a crossover.

## stochastic

Returns `(%K, %D)` — where the close sits inside its recent high-low range, and a smoothed version of the same.

## bollinger

Returns `(middle, upper, lower, %B)`. The bands sit a number of standard deviations either side of the moving average. `%B` locates the price inside them: `0` is exactly on the lower band, `1` on the upper.

## true_range

The larger of the candle's own range and either gap to the previous close — the building block for `atr`.

## atr

Average True Range: how large a typical candle is, in price units. Divide by the price to compare volatility across tickers.

## adx

Returns `(ADX, DI+, DI-)`. ADX measures how *trending* the tape is without saying which way — below 20 means range-bound. Direction comes from whether DI+ sits above DI-.

## obv

On-Balance Volume: volume signed by each candle's direction and accumulated. A rising OBV says buying is behind the move.

## slope

Least-squares gradient over the last `window` points, expressed as a percent of the mean level so it can be compared across tickers of very different price.

## zscore

How many standard deviations the latest point sits from its mean over the window. Used to ask whether today's price is unusual by this stock's own recent standards.

## drawdown

Percent below the running peak, as a negative number.

## range_position

Where a value sits between a low and a high, as 0–100. Used for the 52-week range.

## enrich

Takes an OHLCV frame and returns a copy with every indicator above added as a column. Both `TechnicalAnalysis` and `CandleChart` read from the result, which is what guarantees that what gets scored and what gets drawn can never drift apart.
