"""One turning point of the ZigZag drawn over the price chart."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SwingPoint:
    """A swing high or swing low found by PatternDetector's ZigZag.

    Positions are counted back from the newest candle (bars_ago = 0 is the
    last candle), so the chart can place the point on any tail of the frame.
    """

    bars_ago: int                # candle of the extreme, 0 = today
    price: float                 # the candle's High (swing high) or Low (swing low)
    kind: str                    # "HIGH" or "LOW"
    confirmed: bool = True       # False: the extreme the price is still moving into

    @property
    def is_high(self) -> bool:
        return self.kind == "HIGH"

    def to_dict(self) -> dict:
        return {
            "bars_ago": self.bars_ago,
            "price": round(self.price, 4),
            "kind": self.kind,
            "confirmed": self.confirmed,
        }
