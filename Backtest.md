Checks whether a high score actually came before a good next candle. Without this, a BUY is just a number that crossed an arbitrary line.

It walks forward through the history. After a warm-up (200 candles, so that SMA200 exists, or half the history if that is shorter), the technical block is re-scored at each candle using only the data up to that candle. That score is then compared with the return to the next close. Every indicator in `Indicators.enrich` is causal, so slicing the enriched frame reproduces exactly what the block would have seen that day.

Only the technical block is tested. Valuation and supply read today's fundamentals snapshot, and replaying them into the past would be look-ahead. On short horizons the technical block carries almost all the weight anyway.

## recommendation

The `Recommendation` whose enriched frame and market data are replayed.

## settings

The run's `Settings`. They provide the BUY threshold (from `RATING_BANDS`), the horizon and `cost_bps`.

## ic

Spearman rank correlation of the score with the next candle's return. Near 0 means the score carries no information. On daily data, 0.02–0.05 is already respectable, and anything much higher deserves suspicion.

## ic_tstat

Rough significance of the IC. An |t| below about 2 cannot be told apart from noise.

## strategy_return

Total return, in percent, of being long whenever the score clears the BUY band and flat otherwise, after `COST_BPS` per entry and exit.

## buy_hold_return

Total return, in percent, of simply holding the stock over the same candles. This is the bar the strategy has to clear.

## trades

How many entries and exits the strategy made.

## exposure

The share of candles spent holding, in percent.

## hit_rate

Of the candles spent in a BUY, the share followed by an up close, in percent.

## summary

A one-line digest for the report card.

## to_dict

The numbers as plain data, for the JSON and CSV files. Returns `{"skipped": reason}` when the history was too short.

## pooled_ic

One IC over every ticker's candles combined, with the sample count. More stable than any single ticker's IC.
