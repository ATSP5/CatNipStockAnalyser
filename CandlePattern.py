"""One candlestick pattern found on a ticker's chart."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CandlePattern:
    """A single occurrence of a candlestick formation.

    Positions are counted back from the newest candle (bars_ago = 0 is the
    last candle), so the chart can place the pattern on any tail of the frame.
    """

    name: str                    # full name, e.g. "Bullish Engulfing"
    code: str                    # short label drawn on the chart, e.g. "ENG"
    direction: str               # "BULL" or "BEAR"
    length: int                  # candles the formation spans (1-3)
    bars_ago: int                # newest candle of the formation, 0 = today
    timestamp: object            # time of the formation's newest candle
    low: float                   # lowest low across the formation's candles
    high: float                  # highest high across the formation's candles
    strength: float              # 0..1 weight: base reliability x confirmation
    confirmed: Optional[bool] = None   # next candle agreed / disagreed / not yet

    @property
    def bullish(self) -> bool:
        return self.direction == "BULL"

    def status(self) -> str:
        """Polish word for the confirmation state."""
        if self.confirmed is None:
            return "niepotwierdzona"
        return "potwierdzona" if self.confirmed else "zanegowana"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "code": self.code,
            "direction": self.direction,
            "length": self.length,
            "bars_ago": self.bars_ago,
            "timestamp": str(self.timestamp),
            "strength": round(self.strength, 3),
            "confirmed": self.confirmed,
        }
