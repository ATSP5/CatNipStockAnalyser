"""One ticker's AI price forecast: the quantile band for every future candle."""

from dataclasses import dataclass
from typing import List, Optional

import numpy as np


@dataclass(frozen=True)
class PriceForecast:
    """Forecast closes for the candles after the last real one.

    low / median / high are the model's quantiles (by default 10%, 50%, 90%)
    for each future candle, in the ticker's currency; inner_low / inner_high
    are a narrower band around the median (by default 24% and 76%, i.e.
    median +/- 26 percentage points). timestamps are the calendar positions
    those candles would fall on.
    """

    ticker: str
    model: str
    last_close: float
    timestamps: List[object]
    low: np.ndarray
    median: np.ndarray
    high: np.ndarray
    quantiles: tuple = (0.1, 0.5, 0.9)
    inner_low: Optional[np.ndarray] = None
    inner_high: Optional[np.ndarray] = None
    inner_quantiles: Optional[tuple] = None

    @property
    def steps(self) -> int:
        return len(self.median)

    def change_pct(self) -> float:
        """Median close at the end of the horizon against the last real close."""
        return 100.0 * (float(self.median[-1]) / self.last_close - 1.0)

    def has_inner(self) -> bool:
        return self.inner_low is not None and self.inner_high is not None

    def to_dict(self) -> dict:
        inner = {}
        if self.has_inner():
            inner = {
                "inner_quantiles": list(self.inner_quantiles),
                "inner_low_end": round(float(self.inner_low[-1]), 4),
                "inner_high_end": round(float(self.inner_high[-1]), 4),
            }
        return {
            "model": self.model,
            "steps": self.steps,
            "quantiles": list(self.quantiles),
            "end": str(self.timestamps[-1]),
            "median_end": round(float(self.median[-1]), 4),
            "low_end": round(float(self.low[-1]), 4),
            "high_end": round(float(self.high[-1]), 4),
            "change_pct": round(self.change_pct(), 2),
            **inner,
        }
