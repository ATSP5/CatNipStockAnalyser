Folds the three views into one call. This is where a technical score, a valuation score and a supply score become STRONG BUY, BUY, HOLD, SELL or STRONG SELL.

The blocks are weighted by horizon (see `Settings.HORIZON_WEIGHTS`; at `1d` it is technical 90%, valuation 10%, supply 0%) into a single composite on the `-100..+100` scale, which then lands in one of five bands:

| Composite | Call |
| --- | --- |
| `+45` and above | STRONG BUY |
| `+15` to `+45` | BUY |
| `-15` to `+15` | HOLD |
| `-45` to `-15` | SELL |
| below `-45` | STRONG SELL |

A block that produced nothing is dropped and the remaining weights are renormalised, so a ticker with no published fundamentals still gets a verdict rather than a crash — with a confidence figure that says how much of the intended evidence was really there.

Expect the blocks to disagree. A stock at the top of its 52-week range on a strong uptrend scores well technically and badly on valuation, and the HOLD that comes out of it is the honest answer rather than a failure to decide. The interesting cases are the ones where all three agree.

## frame

The enriched candle frame, built once here and shared with both `TechnicalAnalysis` and `CandleChart` so that the scored data and the drawn data are guaranteed to be the same data.

## score

The composite, from `-100` to `+100`.

## rating

The label the composite falls into. `"NO DATA"` when no block produced anything at all.

## confidence

How much of the intended evidence actually arrived, from 0 to 1. Docked both for blocks that produced nothing and for individual signals that were missing inside the blocks that did.

A confident HOLD and a HOLD that simply had nothing to work with are very different statements, and this is what separates them. It measures **data completeness only**: 1.0 does not mean the forecast is likely to be right. The report prints it as "data coverage" for that reason. The band thresholds are untested; check them against the `Backtest` block.

## weights

Each block's renormalised weight, as percentages that add to 100.

## contributions

The points each block actually added to the score (`weight × block score`). They add up to `score`.

## block_score

The score of one named block — `"technical"`, `"valuation"` or `"supply"` — or `None` when it produced nothing.

## conviction

How far from the fence this call sits, as an absolute score. Useful for ranking several HOLDs against each other.

## reasons

The strongest arguments in one direction, gathered across all three blocks and ranked by weighted contribution rather than by raw score. A moderate reading on a heavily weighted signal outranks an extreme reading on a light one, which is why the printed list is not always in descending numeric order.

## notes

Every caveat the three blocks raised, prefixed with where it came from, plus any errors recorded while fetching.

## to_dict

The whole verdict as plain data, including every individual signal, for the JSON output.

## for_market

Builds a verdict, or returns `None` when the ticker could not be fetched well enough to judge.
