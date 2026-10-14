"""Does a high score actually precede a good next candle? Walk forward and see.

At every candle after a warm-up the technical block is re-scored on the history
up to and including that candle -- nothing later -- and the score is set
against the return to the next close. Every indicator in Indicators.enrich is
causal (rolling windows, EWMs, running peaks), so slicing the enriched frame
gives exactly what the block would have seen on that day.

Only the technical block is tested. Valuation and supply read today's
fundamentals snapshot; replaying them into the past would be look-ahead. On
short horizons the technical block carries almost all of the weight anyway.

Three numbers come out:

    IC        rank correlation of score with the next return. Around 0 means
              the score has no information; 0.02-0.05 is already respectable
              for daily data, and anything far above that deserves suspicion.
    strategy  long whenever the score clears the BUY band, flat otherwise,
              paying COST_BPS on every entry and exit.
    buy&hold  simply owning the stock over the same candles.
"""

import math

import pandas as pd

from Score import Score
from TechnicalAnalysis import TechnicalAnalysis


class Backtest:
    """Walk-forward check of one ticker's technical score."""

    WARMUP = 200          # candles before the first scored one (SMA200 needs them)
    MIN_WARMUP = 60
    MIN_SAMPLES = 30

    def __init__(self, recommendation, settings):
        self.ticker = recommendation.ticker
        self.settings = settings
        self.threshold = self._buy_threshold(settings)
        self.scores = pd.Series(dtype=float)
        self.returns = pd.Series(dtype=float)
        self.problem = ""
        frame = recommendation.frame
        if frame is None or len(frame) == 0:
            self.problem = "no candles"
            return
        self._walk(recommendation.market, frame)

    @staticmethod
    def _buy_threshold(settings):
        for threshold, label in settings.RATING_BANDS:
            if label == "BUY":
                return threshold
        return 15.0

    # -- the walk ----------------------------------------------------------

    def _walk(self, market, frame):
        closes = frame["Close"].astype(float)
        count = len(frame)
        start = min(self.WARMUP, max(self.MIN_WARMUP, count // 2))
        if count - start - 1 < self.MIN_SAMPLES:
            self.problem = "only %d candles -- too few to test" % count
            return

        stamps, scores, returns = [], [], []
        for index in range(start, count - 1):
            past = frame.iloc[:index + 1]
            score = TechnicalAnalysis(market, self.settings, past).score()
            now, nxt = float(closes.iloc[index]), float(closes.iloc[index + 1])
            if score is None or now <= 0:
                continue
            stamps.append(frame.index[index])
            scores.append(score)
            returns.append(nxt / now - 1.0)

        self.scores = pd.Series(scores, index=stamps, dtype=float)
        self.returns = pd.Series(returns, index=stamps, dtype=float)
        if len(self.scores) < self.MIN_SAMPLES:
            self.problem = "only %d scored candles" % len(self.scores)

    # -- the verdict -------------------------------------------------------

    def ok(self):
        return not self.problem

    def samples(self):
        return len(self.scores)

    @staticmethod
    def rank_ic(scores, returns):
        """Spearman correlation of score with next return, or None."""
        if len(scores) < 3:
            return None
        value = scores.rank().corr(returns.rank())
        return Score.num(value)

    def ic(self):
        return self.rank_ic(self.scores, self.returns)

    def ic_tstat(self):
        """Rough significance of the IC: |t| below ~2 is indistinguishable from 0."""
        ic, n = self.ic(), self.samples()
        if ic is None or n < 4 or abs(ic) >= 1.0:
            return None
        return ic * math.sqrt((n - 2) / (1.0 - ic * ic))

    def position(self):
        """1 while the score sits in a BUY band, else 0."""
        return (self.scores >= self.threshold).astype(float)

    def strategy_return(self):
        """Total return of long-on-BUY, flat otherwise, after costs, in percent."""
        if not self.samples():
            return None
        held = self.position()
        trades = held.diff().abs().fillna(held.iloc[0])
        cost = self.settings.cost_bps / 10000.0
        daily = held * self.returns - trades * cost
        return 100.0 * (float((1.0 + daily).prod()) - 1.0)

    def buy_hold_return(self):
        if not self.samples():
            return None
        return 100.0 * (float((1.0 + self.returns).prod()) - 1.0)

    def trades(self):
        if not self.samples():
            return 0
        held = self.position()
        return int(held.diff().abs().fillna(held.iloc[0]).sum())

    def exposure(self):
        """Share of candles spent holding, percent."""
        return 100.0 * float(self.position().mean()) if self.samples() else 0.0

    def hit_rate(self):
        """Share of BUY candles followed by an up close, percent, or None."""
        held = self.position() > 0
        if not held.any():
            return None
        return 100.0 * float((self.returns[held] > 0).mean())

    def summary(self):
        if not self.ok():
            return "backtest skipped -- %s" % self.problem
        ic, tstat = self.ic(), self.ic_tstat()
        hit = self.hit_rate()
        return ("IC %s (t %s, %d candles) | BUY-only %+.1f%% vs buy&hold %+.1f%% "
                "| %d trades, %.0f%% invested, hit rate %s" % (
                    "n/a" if ic is None else "%+.3f" % ic,
                    "n/a" if tstat is None else "%+.1f" % tstat,
                    self.samples(),
                    self.strategy_return(), self.buy_hold_return(),
                    self.trades(), self.exposure(),
                    "n/a" if hit is None else "%.0f%%" % hit,
                ))

    def to_dict(self):
        if not self.ok():
            return {"skipped": self.problem}

        def rounded(value, places):
            return None if value is None else round(value, places)

        return {
            "samples": self.samples(),
            "buy_threshold": self.threshold,
            "cost_bps": self.settings.cost_bps,
            "ic": rounded(self.ic(), 4),
            "ic_tstat": rounded(self.ic_tstat(), 2),
            "strategy_return_pct": rounded(self.strategy_return(), 2),
            "buy_hold_return_pct": rounded(self.buy_hold_return(), 2),
            "trades": self.trades(),
            "exposure_pct": round(self.exposure(), 1),
            "hit_rate_pct": rounded(self.hit_rate(), 1),
        }

    @classmethod
    def pooled_ic(cls, backtests):
        """One IC over every ticker's candles together, or None."""
        usable = [b for b in backtests if b.ok()]
        if not usable:
            return None, 0
        scores = pd.concat([b.scores for b in usable], ignore_index=True)
        returns = pd.concat([b.returns for b in usable], ignore_index=True)
        return cls.rank_ic(scores, returns), len(scores)

    def backtest(self):
        return
