"""One screened company: what is known about it before it is ranked."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class StockCandidate:
    """Raw 1-6 month factors of one ticker, measured once and shared by every
    theme the ticker appears in."""

    ticker: str
    name: str
    industry: str
    price: Optional[float]
    currency: str
    market_cap: Optional[float]
    dollar_volume: Optional[float]
    bars: int
    rating: str                                   # StockAnalyser call
    factors: Dict[str, Optional[float]] = field(default_factory=dict)
    forecast_change_pct: Optional[float] = None
    problems: List[str] = field(default_factory=list)

    def value(self, factor: str) -> Optional[float]:
        return self.factors.get(factor)

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "name": self.name,
            "industry": self.industry,
            "price": self.price,
            "currency": self.currency,
            "market_cap": self.market_cap,
            "dollar_volume": self.dollar_volume,
            "bars": self.bars,
            "rating": self.rating,
            "forecast_change_pct": self.forecast_change_pct,
            "factors": dict(self.factors),
            "problems": list(self.problems),
        }
