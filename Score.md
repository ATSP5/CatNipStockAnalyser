The scoring primitives every analysis block is built from. Everything in StockAnalyser is measured on one scale: `-100` is maximally bearish, `0` is neutral, `+100` is maximally bullish. Keeping one scale is what makes a P/E ratio and an RSI reading comparable enough to average together.

A `Signal` is a single scored observation with the reasoning attached. A `Block` is a weighted bundle of signals. Signals that cannot be computed are left out rather than guessed at, and the remaining weights are renormalised — so a ticker with no published fundamentals still produces an honest technical-only verdict, reported with lower confidence.

## clamp

Pins a number inside a range, `-100..100` unless told otherwise.

## is_num

True only for a real, finite number. Yahoo returns `None`, `NaN` and occasionally a string for fields it does not have, and every one of those must be treated as missing rather than as zero.

## ramp

A linear score between two reference points: `bear` maps to `-100`, `bull` to `+100`, and anything beyond either end is clamped.

It runs in both directions. Pass `bear` above `bull` when the lower reading is the bullish one — `ramp(pe, 45, 8)` scores a P/E of 8 at `+100` and a P/E of 45 at `-100`.

## band

Scores highest inside a range and decays outside it, for readings where both extremes are bad. Insider ownership is the clearest case: a little is reassuring, none is indifferent, and ninety per cent means there is barely a company to buy into. `falloff` sets how many band-widths away the score takes to bottom out.

## pct_change

Percent change from an old value to a new one, or `None` when that would be meaningless.

## human

Compact rendering of a large number: `4.62T`, `388.74B`, `14.59M`.

## Signal

One scored observation. Carries `key`, `label`, the `score`, its `weight` within the block, a `detail` string explaining the number in words, and the raw `value` it came from. The detail string is what the report prints, so it should read as an explanation rather than a restatement.

## Block

A named bundle of signals — one of `technical`, `valuation` or `supply`.

`add` records a signal, skipping it when the score is not a real number. `note` attaches a caveat that gets printed but not scored. `score` is the weighted mean of whatever is present, or `None` when the block is empty. `coverage` reports what fraction of the intended evidence actually arrived, which is what drives the confidence figure. `top` returns the signals pulling hardest in one direction, ranked by their weighted contribution rather than by raw score.
