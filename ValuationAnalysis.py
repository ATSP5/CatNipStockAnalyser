"""Is the price high or low -- against earnings, against assets, against cash,
and against where this stock has traded before.

Two kinds of signal live here. The multiples (P/E, P/B, EV/EBITDA and friends)
say whether the price is high relative to the business. The positional ones
(52-week range, analyst target) say whether it is high relative to its own
recent history. Distance from the 200-day average and the yearly z-score used
to live here too, but they restated the technical trend and the range position
with the opposite sign, so they were removed. A few quality measures --
margin, return on equity, leverage -- sit alongside them, because a low
multiple on a deteriorating business is a trap rather than a bargain.

P/B, P/S, EV/EBITDA and the free cash flow yield come from MarketData's
checked readers, which convert foreign statements to the quote currency and
withhold impossible values -- a withheld ratio is simply not scored.
"""

from Indicators import Indicators
from Score import Score


class ValuationAnalysis:
    """Scores how expensive one ticker looks right now."""

    NAME = "valuation"

    WEIGHTS = {
        "pe": 2.0,
        "forward_pe": 1.5,
        "peg": 1.5,
        "pb": 1.0,
        "ps": 1.0,
        "ev_ebitda": 1.25,
        "fcf_yield": 1.5,
        "dividend": 0.75,
        "range_position": 1.5,
        "analyst_target": 1.25,
        "margin": 0.75,
        "roe": 0.75,
        "leverage": 0.75,
    }

    def __init__(self, market, settings, frame=None):
        self.market = market
        self.settings = settings
        self.frame = frame
        self.block = Score.Block(self.NAME, sum(self.WEIGHTS.values()))
        self._analyse()

    def _add(self, key, label, score, detail="", value=None):
        self.block.add(key, label, score, self.WEIGHTS[key], detail, value)

    def score(self):
        return self.block.score()

    def _analyse(self):
        if not self.market.info:
            self.block.note(
                "no published fundamentals -- judged on price position alone"
            )
        self._earnings_multiples()
        self._asset_and_sales_multiples()
        self._cash_returns()
        self._price_position()
        self._analyst_view()
        self._quality()

    # -- multiples ---------------------------------------------------------

    def _earnings_multiples(self):
        trailing = self.market.field("trailingPE")
        if trailing is not None:
            if trailing <= 0:
                self._add("pe", "Trailing P/E", -55.0,
                          "negative -- the company is lossmaking", trailing)
            else:
                self._add("pe", "Trailing P/E", Score.ramp(trailing, 45.0, 8.0),
                          "%.1fx trailing earnings" % trailing, trailing)
        elif self.market.field("trailingEps") is not None:
            self.block.note("no trailing P/E published")

        forward = self.market.field("forwardPE")
        if forward is not None and forward > 0:
            detail = "%.1fx next year's earnings" % forward
            if trailing and trailing > 0:
                # Forward below trailing means earnings are expected to grow.
                direction = "growing" if forward < trailing else "shrinking"
                detail += " -- earnings expected to be %s" % direction
            self._add("forward_pe", "Forward P/E",
                      Score.ramp(forward, 38.0, 7.0), detail, forward)

        if trailing and forward and trailing > 0 and forward > 0 \
                and trailing / forward > 2.5:
            self.block.note(
                "trailing P/E %.1f vs forward %.1f -- trailing earnings are "
                "probably depressed by one-off charges" % (trailing, forward)
            )

        peg = self.market.field("pegRatio", "trailingPegRatio")
        if peg is not None and peg > 0:
            conflict = self._peg_conflict(peg, trailing, forward)
            if conflict:
                self.block.note("PEG %.2f ignored -- %s" % (peg, conflict))
            else:
                # Around 1.0 the price is fair for the growth being bought.
                self._add("peg", "PEG ratio",
                          Score.band(peg, 0.5, 1.2, falloff=1.5),
                          "%.2f (near 1.0 is priced fairly for its growth)" % peg,
                          peg)

    @staticmethod
    def _peg_conflict(peg, trailing, forward):
        """Why a published PEG disagrees with the P/E pair, or '' if it doesn't.

        PEG is P/E over a growth forecast Yahoo does not show. The trailing and
        forward P/E imply a growth rate of their own; when the two stories are
        far apart the PEG is built on a forecast nobody else in the data
        believes, and scoring it is garbage in, garbage out.
        """
        if not (trailing and forward and trailing > 0 and forward > 0):
            return ""
        implied_by_pe = 100.0 * (trailing / forward - 1.0)
        implied_by_peg = trailing / peg
        if implied_by_pe <= 0:
            return ("P/E pair expects earnings to shrink (%+.0f%%) while PEG "
                    "assumes %.1f%% growth" % (implied_by_pe, implied_by_peg))
        low, high = sorted((implied_by_pe, implied_by_peg))
        if high / max(low, 1e-9) > 3.0 and high - low > 10.0:
            return ("P/E pair implies %.0f%% earnings growth, PEG implies %.1f%%"
                    % (implied_by_pe, implied_by_peg))
        return ""

    def _asset_and_sales_multiples(self):
        price_to_book = self.market.price_to_book()
        if price_to_book is not None and price_to_book > 0:
            self._add("pb", "Price / book", Score.ramp(price_to_book, 8.0, 1.0),
                      "%.2fx book value" % price_to_book, price_to_book)

        price_to_sales = self.market.price_to_sales()
        if price_to_sales is not None and price_to_sales > 0:
            self._add("ps", "Price / sales",
                      Score.ramp(price_to_sales, 12.0, 1.0),
                      "%.2fx revenue" % price_to_sales, price_to_sales)

        ev_ebitda = self.market.enterprise_to_ebitda()
        if ev_ebitda is not None:
            if ev_ebitda <= 0:
                self.block.note("EV/EBITDA is negative -- EBITDA does not cover")
            else:
                self._add("ev_ebitda", "EV / EBITDA",
                          Score.ramp(ev_ebitda, 22.0, 6.0),
                          "%.1fx enterprise value to EBITDA" % ev_ebitda,
                          ev_ebitda)

    def _cash_returns(self):
        """What the business hands back, measured against the risk-free rate."""
        yield_pct = self.market.free_cash_flow_yield()
        if yield_pct is not None:
            hurdle = 100.0 * self.settings.risk_free_rate
            self._add(
                "fcf_yield",
                "Free cash flow yield",
                Score.ramp(yield_pct, -2.0, 2.5 * hurdle),
                "%.2f%% against a %.1f%% risk-free rate" % (yield_pct, hurdle),
                yield_pct,
            )

        yield_pct, source = self._dividend_yield()
        if yield_pct is not None and yield_pct > 0:
            detail = "%.2f%% dividend yield (%s)" % (yield_pct, source)
            # Anything extreme is usually a dividend about to be cut.
            result = Score.band(yield_pct, 2.0, 6.0, inside=70.0,
                                outside=-30.0, falloff=1.5)
            if yield_pct > 12:
                result = -40.0
                detail += " -- suspiciously high, check it is sustainable"
            self._add("dividend", "Dividend yield", result, detail, yield_pct)

    def _dividend_yield(self):
        """(yield in percent, where it came from), or (None, reason).

        Yahoo's `dividendYield` changed from a fraction (0.0043) to a percent
        (0.43), so its scale cannot be guessed from the value -- 0.43 is
        plausible either way. Fields with a fixed meaning are preferred: the
        annual dividend per share over the price, then the trailing yield,
        which is still a fraction. A bare `dividendYield` is not scored.
        """
        price = self.market.last_price()
        rate = self.market.field("dividendRate", "trailingAnnualDividendRate")
        trailing = self.market.field("trailingAnnualDividendYield")

        if rate is not None and price and price > 0:
            return 100.0 * rate / price, "annual dividend / price"
        if trailing is not None:
            return 100.0 * trailing, "trailing 12 months"

        published = self.market.field("dividendYield")
        if published is None:
            return None, "not published"
        self.block.note("dividend yield %.4g ignored -- its scale (fraction or "
                        "percent) cannot be confirmed" % published)
        return None, "unconfirmed scale"

    # -- where the price sits ---------------------------------------------

    def _price_position(self):
        price = self.market.last_price()
        low, high = self.market.year_range()
        if price and low and high and high > low:
            position = Indicators.range_position(price, low, high)
            if position is not None:
                # Near the low is cheap; near the high, the good news is priced in.
                self._add(
                    "range_position",
                    "Position in 52-week range",
                    Score.ramp(position, 95.0, 5.0),
                    "%.0f%% of the way up the %.2f-%.2f range" % (position, low, high),
                    position,
                )

    def _analyst_view(self):
        target = self.market.field("targetMeanPrice")
        price = self.market.last_price()
        if not (target and price and price > 0):
            return
        upside = 100.0 * (target - price) / price
        self._add(
            "analyst_target",
            "Upside to analyst target",
            Score.ramp(upside, -15.0, 35.0),
            "%+.1f%% to the mean target of %.2f" % (upside, target),
            upside,
        )

    # -- is the cheapness real? -------------------------------------------

    def _quality(self):
        margin = self.market.field("profitMargins")
        if margin is not None:
            margin_pct = margin * 100.0
            self._add("margin", "Profit margin",
                      Score.ramp(margin_pct, -5.0, 25.0),
                      "%.1f%% of revenue reaches the bottom line" % margin_pct,
                      margin_pct)

        roe = self.market.field("returnOnEquity")
        if roe is not None:
            roe_pct = roe * 100.0
            self._add("roe", "Return on equity",
                      Score.ramp(roe_pct, 0.0, 30.0),
                      "%.1f%% return on shareholder equity" % roe_pct, roe_pct)

        debt_to_equity = self.market.field("debtToEquity")
        if debt_to_equity is not None:
            # Yahoo reports this as a percentage: 150 means 1.5x equity.
            self._add("leverage", "Debt / equity",
                      Score.ramp(debt_to_equity, 250.0, 20.0),
                      "%.0f%% of equity carried as debt" % debt_to_equity,
                      debt_to_equity)

    def valuationanalysis(self):
        return
