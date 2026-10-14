"""Folds supply, valuation and technicals into one call.

The three blocks are weighted into a single -100..+100 composite. The weights
follow the horizon (on 1d candles: technical 90%, valuation 10%, supply 0%;
see Settings.HORIZON_WEIGHTS). The composite lands in one of five bands:

    >= +45  STRONG BUY        -15 .. -45  SELL
    >= +15  BUY               <  -45      STRONG SELL
    -15 .. +15  HOLD

A block that produced nothing is dropped and the remaining weights are
renormalised, so a ticker with no fundamentals still gets a verdict -- with a
confidence figure that says how much of the intended evidence was really there.
That figure is data coverage only: 1.0 means nothing was missing, not that the
call is likely to be right. The bands themselves are untested until the
Backtest block says otherwise.
"""

from Indicators import Indicators
from Score import Score
from SupplyAnalysis import SupplyAnalysis
from TechnicalAnalysis import TechnicalAnalysis
from ValuationAnalysis import ValuationAnalysis


class Recommendation:
    """The verdict on one ticker, with the reasoning kept attached."""

    def __init__(self, market, settings):
        self.market = market
        self.settings = settings
        self.ticker = market.ticker

        # One enriched frame, shared by the technicals and the chart.
        self.frame = Indicators.enrich(market.history) if market.ok() else None

        self.technical = TechnicalAnalysis(market, settings, self.frame) \
            if self.frame is not None else None
        self.valuation = ValuationAnalysis(market, settings, self.frame)
        self.supply = SupplyAnalysis(market, settings)

        self.blocks = {}
        for analysis in (self.technical, self.valuation, self.supply):
            if analysis is not None:
                self.blocks[analysis.NAME] = analysis.block

        self.score = 0.0
        self.rating = "HOLD"
        self.confidence = 0.0
        self.weights = {}           # block -> share of the call, percent
        self.contributions = {}     # block -> points it added to the score
        self._combine()

    # -- the arithmetic ----------------------------------------------------

    def _combine(self):
        weights = self.settings.normalised_weights()
        used, total_weight, confidence = {}, 0.0, 0.0

        for name, weight in weights.items():
            block = self.blocks.get(name)
            block_score = block.score() if block is not None else None
            if block_score is None:
                continue
            used[name] = (weight, block_score)
            total_weight += weight
            confidence += weight * block.coverage()

        if not used:
            self.rating = "NO DATA"
            self.score = 0.0
            self.confidence = 0.0
            return

        self.score = Score.clamp(
            sum(weight * value for weight, value in used.values()) / total_weight
        )
        # Renormalised weights, so the parts add to 100%.
        self.weights = dict(
            (name, 100.0 * weight / total_weight) for name, (weight, _) in used.items()
        )
        # What each block actually added; these sum to the composite score.
        self.contributions = dict(
            (name, weight * value / total_weight)
            for name, (weight, value) in used.items()
        )
        self.rating = self.settings.rating_for(self.score)
        # Confidence is docked both for missing blocks and for missing signals.
        self.confidence = Score.clamp(confidence / max(total_weight, 1e-9), 0.0, 1.0) \
            * Score.clamp(total_weight, 0.0, 1.0)

    # -- reading the result ------------------------------------------------

    def block_score(self, name):
        block = self.blocks.get(name)
        return None if block is None else block.score()

    def conviction(self):
        """How far from the fence this call sits, 0..100."""
        return abs(self.score)

    def reasons(self, count=3, bullish=True):
        """The strongest arguments either way, gathered across all three blocks."""
        gathered = []
        for name, block in self.blocks.items():
            for signal in block.top(count, bullish):
                gathered.append((name, signal))
        gathered.sort(key=lambda pair: pair[1].score * pair[1].weight,
                      reverse=bullish)
        return gathered[:count]

    def notes(self):
        """Every caveat the three blocks raised, prefixed with their origin."""
        collected = []
        for name, block in self.blocks.items():
            for text in block.notes:
                collected.append("%s: %s" % (name, text))
        collected.extend("data: %s" % problem for problem in self.market.errors)
        return collected

    def headline(self):
        """One line summarising the call, for the summary table."""
        price = self.market.last_price()
        shown = "n/a" if price is None else "%.2f" % price
        return "%-8s %-11s %+6.1f  conf %3.0f%%  %s %s" % (
            self.ticker, self.rating, self.score, 100 * self.confidence,
            shown, self.market.currency(),
        )

    def to_dict(self):
        return {
            "ticker": self.ticker,
            "rating": self.rating,
            "score": round(self.score, 1),
            "confidence": round(self.confidence, 2),
            "horizon": self.settings.horizon,
            "market": self.market.to_dict(),
            "blocks": dict((n, b.to_dict()) for n, b in self.blocks.items()),
            "weights": dict(
                (n, round(v, 1)) for n, v in self.weights.items()
            ),
            "contributions": dict(
                (n, round(v, 1)) for n, v in self.contributions.items()
            ),
            "bullish": [s.to_dict() for _, s in self.reasons(3, True)],
            "bearish": [s.to_dict() for _, s in self.reasons(3, False)],
            "notes": self.notes(),
        }

    @classmethod
    def for_market(cls, market, settings):
        """Build a verdict, or None when the ticker could not be fetched."""
        if not market.ok():
            return None
        return cls(market, settings)

    def recommendation(self):
        return
