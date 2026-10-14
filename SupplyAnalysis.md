How many shares exist, how many actually trade, and which way that number is moving.

Share count is the quietest of the three views and often the most telling. A company steadily retiring its own stock lifts every per-share figure without selling a thing more; one issuing stock every year dilutes the holder even while the business grows. Neither shows up in a price chart, and neither shows up in a P/E ratio taken on its own.

On top of the count itself this block reads the free float, who is holding it, how heavily it is shorted, and whether enough of it changes hands to get out of a position without moving the price.

## WEIGHTS

How much each signal counts within the block. `share_count_trend` carries 2.5 — more than double anything else here — because dilution and buybacks act directly on the value of a single share.

## share_count_trend

Percent change in shares outstanding over the past year, taken from the filed share count history. Scored backwards: a shrinking count is the bullish direction.

Roughly, a company retiring more than 1% of its stock a year is returning capital meaningfully, and one issuing more than 2% is funding itself from its shareholders. When no history is published the signal drops out and the block notes that dilution could not be judged.

## float_ratio

What share of the issued stock actually floats freely. A thin float — under about a quarter — moves violently on ordinary volume. A float at essentially 100% means no anchor holder, which is its own mild risk. The comfortable range sits between.

## short_interest

Percentage of the float sold short. Heavy short interest is scored bearishly: it is a standing bet against the company by people who have done the work. It also creates squeeze potential, which this block does not attempt to price.

## short_ratio

Days of average volume needed to close every short position. High values mean the shorts cannot exit quickly.

## insider_holding

What management and founders hold. Scored on a band: some skin in the game is reassuring, none is indifferent, and near-total control leaves little genuinely tradable and few checks on the people running it.

## institution_holding

What professional funds hold. Scored on a band for the same reason — meaningful institutional ownership implies scrutiny, but a register that is entirely institutional has nobody left to do the buying.

## market_cap_tier

Size, scored on a log axis because market caps span six orders of magnitude. Bigger is steadier; micro and nano caps carry structural risk that has nothing to do with the business.

## turnover

What fraction of the float changes hands on a typical day. Too little and a position cannot be exited without moving the price; far too much suggests the stock is being traded rather than held.
