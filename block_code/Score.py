"""Scoring primitives every analysis block builds on.

Everything in StockAnalyser is scored on one scale: -100 is maximally bearish,
0 is neutral, +100 is maximally bullish. A Signal is a single scored
observation; a Block is a weighted bundle of them. Signals that cannot be
computed are simply left out and the remaining weights are renormalised, so a
ticker with no published fundamentals still yields an honest technical-only
verdict instead of a silently wrong one.
"""

import math


class Score:
    """Helpers for turning raw numbers into -100..+100 scores."""

    NEUTRAL = 0.0

    @staticmethod
    def clamp(value, low=-100.0, high=100.0):
        """Pin a number inside [low, high]."""
        return max(low, min(high, float(value)))

    @staticmethod
    def is_num(value):
        """True for a real, finite number. Yahoo hands back None and NaN freely."""
        if value is None or isinstance(value, bool):
            return False
        try:
            number = float(value)
        except (TypeError, ValueError):
            return False
        return math.isfinite(number)

    @staticmethod
    def num(value, default=None):
        """Coerce to float, or return `default` when the value is unusable."""
        return float(value) if Score.is_num(value) else default

    @staticmethod
    def ramp(value, bear, bull):
        """Linear score: `bear` maps to -100, `bull` to +100, clamped either side.

        Works in both directions -- pass bear > bull when the *lower* reading is
        the bullish one, as with a cheap P/E.
        """
        if bull == bear:
            return 0.0
        return Score.clamp(200.0 * (float(value) - bear) / (bull - bear) - 100.0)

    @staticmethod
    def band(value, low, high, inside=100.0, outside=-100.0, falloff=1.0):
        """Score peaks at `inside` within [low, high] and decays outside it.

        `falloff` is how many band-widths away the score takes to reach
        `outside`.
        """
        value = float(value)
        if low <= value <= high:
            return Score.clamp(inside)
        width = (high - low) or abs(high) or 1.0
        distance = (low - value) if value < low else (value - high)
        travelled = min(1.0, distance / (width * falloff))
        return Score.clamp(inside - (inside - outside) * travelled)

    @staticmethod
    def pct_change(new, old):
        """Percent change from `old` to `new`, or None if that is meaningless."""
        if not (Score.is_num(new) and Score.is_num(old)) or float(old) == 0:
            return None
        return 100.0 * (float(new) - float(old)) / abs(float(old))

    @staticmethod
    def human(value, suffix="", decimals=2):
        """Compact human rendering: 1.2B, 45.3M, 12.34."""
        if not Score.is_num(value):
            return "n/a"
        value = float(value)
        for cutoff, unit in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")):
            if abs(value) >= cutoff:
                return "%.2f%s%s" % (value / cutoff, unit, suffix)
        return ("%." + str(decimals) + "f%s") % (value, suffix)

    # -- the two carriers -------------------------------------------------

    class Signal:
        """One scored observation, with the reasoning that produced it."""

        def __init__(self, key, label, score, weight=1.0, detail="", value=None):
            self.key = key
            self.label = label
            self.score = Score.clamp(score)
            self.weight = float(weight)
            self.detail = detail
            self.value = value

        def direction(self):
            if self.score > 5:
                return "bullish"
            if self.score < -5:
                return "bearish"
            return "neutral"

        def to_dict(self):
            return {
                "key": self.key,
                "label": self.label,
                "score": round(self.score, 1),
                "weight": self.weight,
                "detail": self.detail,
                "value": self.value,
            }

        def __repr__(self):
            return "<Signal %s %+.0f>" % (self.key, self.score)

    class Block:
        """A named bundle of signals -- one of supply / valuation / technical."""

        def __init__(self, name, expected_weight=0.0):
            self.name = name
            self.signals = []
            self.notes = []
            self.expected_weight = float(expected_weight)

        def add(self, key, label, score, weight=1.0, detail="", value=None):
            """Record a signal. A score of None means 'no data' and is skipped."""
            if not Score.is_num(score):
                return None
            signal = Score.Signal(key, label, score, weight, detail, value)
            self.signals.append(signal)
            return signal

        def note(self, text):
            """Attach a caveat that is worth printing but is not itself scored."""
            self.notes.append(text)
            return text

        def weight_total(self):
            return sum(s.weight for s in self.signals)

        def score(self):
            """Weighted mean of the signals present, or None when empty."""
            total = self.weight_total()
            if total <= 0:
                return None
            return Score.clamp(
                sum(s.score * s.weight for s in self.signals) / total
            )

        def coverage(self):
            """Fraction of the intended evidence that was actually available."""
            if self.expected_weight <= 0:
                return 1.0 if self.signals else 0.0
            return Score.clamp(self.weight_total() / self.expected_weight, 0.0, 1.0)

        def top(self, count=3, bullish=True):
            """The signals pulling hardest in one direction, strongest first."""
            ordered = sorted(
                self.signals,
                key=lambda s: s.score * s.weight,
                reverse=bullish,
            )
            keep = [s for s in ordered if (s.score > 5 if bullish else s.score < -5)]
            return keep[:count]

        def to_dict(self):
            score = self.score()
            return {
                "name": self.name,
                "score": None if score is None else round(score, 1),
                "coverage": round(self.coverage(), 2),
                "signals": [s.to_dict() for s in self.signals],
                "notes": list(self.notes),
            }

        def __repr__(self):
            score = self.score()
            shown = "n/a" if score is None else "%+.0f" % score
            return "<Block %s %s from %d signal(s)>" % (
                self.name, shown, len(self.signals),
            )
