"""One place in a theme's ranking: the candidate, its score and why."""

from dataclasses import dataclass, field
from typing import Dict, List

from StockCandidate import StockCandidate


@dataclass(frozen=True)
class RankedPick:
    """A candidate ranked inside one theme.

    score is 0..100: the weighted average of the candidate's percentile ranks
    inside the theme, 50 being the theme's middle.
    """

    theme: str
    rank: int
    candidate: StockCandidate
    score: float
    coverage: float                               # 0..1 of factor weight with data
    factor_ranks: Dict[str, float] = field(default_factory=dict)   # 0..1
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)

    @property
    def ticker(self) -> str:
        return self.candidate.ticker

    def to_dict(self) -> dict:
        return {
            "theme": self.theme,
            "rank": self.rank,
            "score": round(self.score, 1),
            "coverage": round(self.coverage, 2),
            "strengths": list(self.strengths),
            "weaknesses": list(self.weaknesses),
            "factor_ranks": dict((k, round(v, 3))
                                 for k, v in self.factor_ranks.items()),
            **self.candidate.to_dict(),
        }
