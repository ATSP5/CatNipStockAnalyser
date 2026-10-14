"""How many shares exist, how many actually trade, and which way that number
is moving.

Share count is the quietest of the three views and often the most telling. A
company steadily retiring its own stock lifts every per-share number without
selling a thing more; one issuing stock every year dilutes the holder even when
the business grows. On top of that this block reads the free float, who holds
it, how heavily it is shorted, and whether enough of it changes hands to get
out of a position without moving the price.
"""

import math

from Score import Score


class SupplyAnalysis:
    """Scores the share supply and ownership structure of one ticker."""

    NAME = "supply"

    WEIGHTS = {
        "share_count_trend": 2.5,
        "float_ratio": 1.0,
        "short_interest": 1.25,
        "short_ratio": 0.75,
        "insider_holding": 1.0,
        "institution_holding": 1.0,
        "market_cap_tier": 0.75,
        "turnover": 1.0,
    }

    def __init__(self, market, settings):
        self.market = market
        self.settings = settings
        self.block = Score.Block(self.NAME, sum(self.WEIGHTS.values()))
        self._analyse()

    def _add(self, key, label, score, detail="", value=None):
        self.block.add(key, label, score, self.WEIGHTS[key], detail, value)

    def score(self):
        return self.block.score()

    def _analyse(self):
        shares = self.market.shares_outstanding()
        if not shares:
            self.block.note("share count not published for this ticker")
        else:
            self.block.note(
                "%s shares in issue" % Score.human(shares)
            )
        self._share_count_trend()
        self._float_structure(shares)
        self._short_interest()
        self._ownership()
        self._size_and_liquidity(shares)

    # -- the headline signal ----------------------------------------------

    def _share_count_trend(self):
        """Buyback or dilution, measured over the last year of filings."""
        change = self.market.share_count_change()
        if change is None:
            self.block.note("no share count history -- dilution cannot be judged")
            return

        # Shrinking supply is the bullish direction, so the ramp runs backwards.
        result = Score.ramp(change, 8.0, -5.0)
        if change < -1.0:
            story = "buying back stock -- supply is shrinking"
        elif change > 2.0:
            story = "issuing stock -- holders are being diluted"
        else:
            story = "share count broadly flat"
        self._add(
            "share_count_trend",
            "Share count trend (1y)",
            result,
            "%+.2f%% over the past year -- %s" % (change, story),
            change,
        )

    def _float_structure(self, shares):
        """How much of the register is actually free to trade."""
        free_float = self.market.free_float()
        if not (free_float and shares and shares > 0):
            return
        ratio = 100.0 * free_float / shares
        if ratio < 25:
            detail = "%.0f%% of shares float freely -- thin and easily moved" % ratio
        elif ratio > 95:
            detail = "%.0f%% floats freely -- no anchor holder" % ratio
        else:
            detail = "%.0f%% of shares float freely" % ratio
        self._add(
            "float_ratio",
            "Free float share",
            Score.band(ratio, 55.0, 95.0, inside=60.0, outside=-60.0, falloff=1.2),
            detail,
            ratio,
        )

    def _short_interest(self):
        short_percent = self.market.field("shortPercentOfFloat")
        if short_percent is not None:
            percent = short_percent * 100.0 if short_percent < 1.0 else short_percent
            if percent > 20:
                detail = "%.1f%% of float sold short -- heavy bearish positioning" % percent
            elif percent > 10:
                detail = "%.1f%% of float sold short -- elevated" % percent
            else:
                detail = "%.1f%% of float sold short" % percent
            self._add("short_interest", "Short interest",
                      Score.ramp(percent, 20.0, 1.0), detail, percent)

        days_to_cover = self.market.field("shortRatio")
        if days_to_cover is not None and days_to_cover > 0:
            self._add(
                "short_ratio",
                "Days to cover",
                Score.ramp(days_to_cover, 10.0, 1.0),
                "%.1f days of average volume to close every short" % days_to_cover,
                days_to_cover,
            )

    def _ownership(self):
        """Who is holding the supply -- insiders and institutions both matter."""
        insiders = self.market.field("heldPercentInsiders")
        if insiders is not None:
            percent = insiders * 100.0 if insiders <= 1.0 else insiders
            # Some skin in the game is good; total control leaves nothing to trade.
            self._add(
                "insider_holding",
                "Insider ownership",
                Score.band(percent, 5.0, 30.0, inside=70.0, outside=-40.0,
                           falloff=1.5),
                "%.1f%% held by insiders" % percent,
                percent,
            )

        institutions = self.market.field("heldPercentInstitutions")
        if institutions is not None:
            percent = institutions * 100.0 if institutions <= 1.0 else institutions
            self._add(
                "institution_holding",
                "Institutional ownership",
                Score.band(percent, 40.0, 85.0, inside=60.0, outside=-40.0,
                           falloff=1.5),
                "%.1f%% held by institutions" % percent,
                percent,
            )

    def _size_and_liquidity(self, shares):
        market_cap = self.market.market_cap()
        if market_cap:
            # Bigger is steadier: micro caps carry real structural risk.
            self._add(
                "market_cap_tier",
                "Market capitalisation",
                Score.ramp(self._log_scale(market_cap), self._log_scale(5e7),
                           self._log_scale(2e11)),
                "%s market cap (%s)" % (
                    Score.human(market_cap), self._tier(market_cap),
                ),
                market_cap,
            )

        volume = self.market.average_volume()
        base = self.market.free_float() or shares
        if volume and base and base > 0:
            # What fraction of the tradable supply changes hands in a day.
            turnover = 100.0 * volume / base
            self._add(
                "turnover",
                "Daily turnover of float",
                Score.band(turnover, 0.3, 5.0, inside=60.0, outside=-60.0,
                           falloff=2.0),
                "%.2f%% of the float trades daily (%s shares)"
                % (turnover, Score.human(volume)),
                turnover,
            )

    @staticmethod
    def _log_scale(value):
        """Market caps span six orders of magnitude -- score them on a log axis."""
        return math.log10(max(1.0, float(value)))

    @staticmethod
    def _tier(market_cap):
        for cutoff, label in (
            (2e11, "mega cap"),
            (1e10, "large cap"),
            (2e9, "mid cap"),
            (3e8, "small cap"),
            (5e7, "micro cap"),
        ):
            if market_cap >= cutoff:
                return label
        return "nano cap"
