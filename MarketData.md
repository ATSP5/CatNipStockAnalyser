Everything known about one ticker, fetched from Yahoo through yfinance: candles at the chosen horizon, published fundamentals, and the share count history that the supply block reads.

Two price series are always fetched. `history` uses the requested horizon and drives the chart and the technicals. `daily` is always two years of 1-day candles, so that a 5-minute run still knows where the 52-week range sits and how far price has drifted from its 200-day average. Without that second series, an intraday horizon would have no long-range context to value against.

Network failure is recorded, never raised. A ticker that cannot be fetched is collected in `errors`, reported as a skipped line, and the rest of the run continues.

## fetch

Pulls one ticker and returns a populated `MarketData`. Retries the history request before giving up, since Yahoo intermittently returns an empty frame for a perfectly valid symbol.

## fetch_many

Fetches every ticker in the settings, in order, optionally calling a `progress` callback with `(position, total, ticker)`.

## ok

True when at least 20 candles arrived — the minimum for any indicator to mean anything. The report skips anything that fails this.

## problem

A one-line explanation of why this ticker cannot be analysed, or `""` when it can.

## field

Returns the first present, numeric value among the names given. Yahoo renames fields without warning and omits them freely, so every call site lists the spellings it knows about: `field("pegRatio", "trailingPegRatio")`. Anything missing, `None`, boolean or non-numeric is skipped.

## text

The string equivalent of `field`.

## shares_outstanding

Shares in issue — the denominator behind every per-share figure, and the starting point of the supply analysis.

## free_float

Shares actually available to trade, with insider and strategic holdings excluded. Usually smaller than `shares_outstanding`, sometimes far smaller.

## market_cap

The published market capitalisation, falling back to price times share count when Yahoo does not supply one.

## year_range

`(low, high)` over the trailing 52 weeks. Prefers Yahoo's own figures and falls back to measuring the daily series directly.

## share_count_change

Percent change in shares outstanding over the last year, or `None` when no history is published.

This is the single most informative number in the supply block. Negative means the company has been retiring its own stock, which lifts every per-share figure without the business doing anything more. Positive means shareholders are being diluted, which quietly erodes a holding even while the company grows.

## average_volume

Average daily volume, from Yahoo where available and measured over the last 60 daily candles otherwise.
