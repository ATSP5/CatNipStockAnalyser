Answers whether the price is high or low — against earnings, against assets, against cash, and against where this stock has traded before. Thirteen signals in three groups.

The *multiples* — P/E, PEG, P/B, P/S, EV/EBITDA — say whether the price is high relative to the business. The *positional* signals — 52-week range and analyst target — say whether it is high relative to its own history. The stretch from the 200-day average and the yearly price z-score used to sit here too. They were removed because they repeated the technical trend signal and the range position with the opposite sign, so the same fact was counted twice and cancelled itself out. The *quality* signals — margin, return on equity, leverage — are the check on both, because a low multiple on a deteriorating business is a trap rather than a bargain.

When Yahoo publishes no fundamentals at all, the multiples simply drop out and the block scores on price position alone, with the reduced coverage carried through to the run's confidence figure.

## WEIGHTS

How much each signal counts within the block. Trailing P/E carries the most at 2.0; the quality checks are deliberately light, since their job is to qualify the multiples rather than to drive the call.

## pe

Trailing price to earnings. Scored from 45x as expensive down to 8x as cheap. A negative P/E means the company is lossmaking and scores firmly negative rather than being discarded as missing data.

## forward_pe

Price against next year's expected earnings. Where a trailing figure also exists, the detail line notes whether earnings are expected to grow or shrink, which is often more informative than either number alone. When trailing P/E is more than 2.5× forward, a note flags that trailing earnings are probably depressed by one-off charges.

## peg

The P/E divided by the growth rate, scored on a band around 1.0 — the point at which the price paid is fair for the growth being bought.

Yahoo's PEG rests on a growth forecast it does not publish. The trailing/forward P/E pair implies a growth rate of its own, and `_peg_conflict` compares the two. When they disagree by more than 3× (and by more than 10 points), or the P/E pair expects earnings to shrink, the PEG is dropped with a note instead of being scored.

## pb

Price to book value. Most meaningful for asset-heavy businesses and close to meaningless for software.

## ps

Price to trailing revenue. The fallback multiple for a company with no earnings to divide by.

## ev_ebitda

Enterprise value to EBITDA — a P/E that accounts for debt, which is why it is weighted above P/B and P/S. Negative EBITDA is noted rather than scored.

## fcf_yield

Free cash flow as a percentage of market cap, scored against the risk-free rate from the settings. This is the most direct statement of what the business actually returns for the price paid.

## dividend

Dividend yield, scored on a band. A yield well above the market's is attractive up to a point; past roughly 12% it usually signals a dividend about to be cut, and the signal turns negative and says so.

The yield comes from `_dividend_yield`, which avoids Yahoo's `dividendYield` field: it switched from a fraction to a percent, and 0.43 is plausible on either scale. It uses `dividendRate / price` first, then `trailingAnnualDividendYield` (still a fraction). A bare `dividendYield` is noted and left unscored.

## range_position

Where the price sits in its 52-week range, from 0 at the low to 100 at the high. Near the low scores well on the reasoning that the good news is not yet priced in — which is exactly where it will disagree with the technical block during a downtrend, as it should.

## analyst_target

Upside to the mean published analyst target.

## margin

What share of revenue reaches the bottom line.

## roe

Return on shareholder equity.

## leverage

Debt against equity, reported by Yahoo as a percentage. High leverage makes every other number on this page less reliable.
