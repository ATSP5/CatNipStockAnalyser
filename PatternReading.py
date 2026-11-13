"""What the candlestick patterns of one ticker add up to."""

from dataclasses import dataclass, field
from typing import List

from CandlePattern import CandlePattern


@dataclass(frozen=True)
class PatternReading:
    """The patterns found in the automatically chosen window and their verdict.

    bias is "BULL", "BEAR", "NEUTRAL" (both sides about equally strong) or
    "NONE" (no pattern in the window).
    """

    window: int                          # candles back from today that were searched
    window_reason: str                   # how the window length was chosen
    patterns: List[CandlePattern] = field(default_factory=list)
    bull_score: float = 0.0              # recency-weighted strength of bull patterns
    bear_score: float = 0.0              # recency-weighted strength of bear patterns
    bias: str = "NONE"

    def net(self) -> float:
        """-1 (only bear) .. +1 (only bull); 0 when there is nothing."""
        total = self.bull_score + self.bear_score
        return 0.0 if total <= 0 else (self.bull_score - self.bear_score) / total

    def count(self, direction: str) -> int:
        return sum(1 for p in self.patterns if p.direction == direction)

    def summary(self) -> str:
        """One line: bias, counts and window."""
        return "%s (net %+.2f)  bull %d / bear %d  w oknie %d świec -- %s" % (
            self.bias, self.net(), self.count("BULL"), self.count("BEAR"),
            self.window, self.window_reason)

    def to_dict(self) -> dict:
        return {
            "bias": self.bias,
            "net": round(self.net(), 3),
            "window": self.window,
            "window_reason": self.window_reason,
            "bull_score": round(self.bull_score, 3),
            "bear_score": round(self.bear_score, 3),
            "patterns": [p.to_dict() for p in self.patterns],
        }
