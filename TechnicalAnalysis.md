Reads what the chart is doing: trend, momentum, volatility and participation. Takes the enriched candle frame from `Indicators` and produces a weighted `Score.Block` of eleven signals.

Every window is counted in candles, so this block judges whatever timeframe the horizon selects. At the default `1d` it is reading a daily chart; at `1h` the identical code reads an hourly one. That is the intended way to ask the same question over a different span.

Momentum-style signals and mean-reversion signals deliberately disagree with each other. A stock in a strong uptrend scores well on `trend` and badly on `rsi` at the same time, and the weighted average is what settles it — which is why a single overbought reading does not by itself produce a SELL.

## WEIGHTS

How much each signal counts within the block. `trend` carries the most at 2.5 because price against its own moving averages is the most robust single technical reading; the oscillators are deliberately lighter.

## score

The block's weighted score, or `None` when there was not enough history to compute anything.

## trend

Price measured against its 50 and 200-candle averages, plus the crossover between them — a golden cross when the 50 sits above the 200, a death cross when it does not. The backbone signal of the block.

## ma_slope

Whether the medium-term average is itself rising or rolling over, as a least-squares gradient over the last 20 candles. Price above a falling average is a weaker position than price above a rising one.

## macd

The MACD histogram, normalised by price so the figure means the same across tickers. A histogram that has just changed sign earns an extra push in that direction, since a fresh crossover carries more information than an established one.

## rsi

Read as mean reversion: oversold is scored as opportunity and overbought as risk. This is the signal most likely to argue against `trend`, and that tension is intentional.

## momentum

Return over roughly the last 90 calendar days, converted to a candle count for whatever horizon is in force.

## bollinger

Position inside the volatility envelope. Near the lower band scores well, near the upper band poorly.

## volume

Whether money is flowing in behind the move, from the slope of On-Balance Volume. Unusually heavy volume amplifies the score rather than setting it, on the reasoning that volume confirms whichever way the tape is already leaning.

## adx

Trend strength from ADX, with direction taken from DI+ against DI-. Below 20 the market is range-bound and the signal correctly scores close to neutral regardless of direction.

## stochastic

Where the close sits in its recent range, scored like RSI.

## drawdown

Distance below the highest close on the chart. A modest dip is treated as a discount; a collapse is treated as evidence that something is broken, not as a bargain.

## volatility

Current ATR against this ticker's own typical ATR. Volatility well above a stock's own norm is a mild warning rather than a verdict, and it is weighted accordingly.
