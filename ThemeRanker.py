"""Ranks the candidates of one theme against each other.

Each factor becomes a percentile rank inside the theme (0 = worst,
1 = best), so a bank is compared with banks and a biotech with biotechs,
and no single outlier figure can dominate. The score is the weighted mean of
those ranks over the factors the candidate has data for, times 100.
"""

from RankedPick import RankedPick


class ThemeRanker:
    """[StockCandidate] of one theme -> its top picks as RankedPick."""

    def __init__(self, screener_settings):
        self.screener_settings = screener_settings

    def theme_ranker(self):
        return self

    # -- public ------------------------------------------------------------

    def rank(self, theme, candidates) -> tuple:
        """(top picks, rejected) -- rejected is [(ticker, reason)]."""
        eligible, rejected = [], []
        for candidate in candidates:
            reason = self._rejection(candidate)
            if reason:
                rejected.append((candidate.ticker, reason))
            else:
                eligible.append(candidate)

        ranks = self._percentiles(eligible)
        scored = []
        for candidate in eligible:
            score, coverage = self._score(ranks[candidate.ticker])
            if coverage < self.screener_settings.min_coverage:
                rejected.append((candidate.ticker,
                                 "za mało danych (%.0f%% wag)" % (100 * coverage)))
                continue
            scored.append((score, coverage, candidate))
        scored.sort(key=lambda item: item[0], reverse=True)

        picks = []
        for position, (score, coverage, candidate) in enumerate(
                scored[:self.screener_settings.top_n], start=1):
            own = ranks[candidate.ticker]
            picks.append(RankedPick(
                theme=theme, rank=position, candidate=candidate, score=score,
                coverage=coverage, factor_ranks=own,
                strengths=self._extremes(own, best=True),
                weaknesses=self._extremes(own, best=False),
            ))
        return picks, rejected

    # -- filters -----------------------------------------------------------

    def _rejection(self, candidate) -> str:
        s = self.screener_settings
        if candidate.bars < s.min_bars:
            return "za krótka historia (%d świec)" % candidate.bars
        if candidate.price is None or candidate.price < s.min_price:
            return "cena poniżej %.0f" % s.min_price
        if candidate.market_cap is None or candidate.market_cap < s.min_market_cap:
            return "kapitalizacja poniżej %.0f mld" % (s.min_market_cap / 1e9)
        if candidate.dollar_volume is None or candidate.dollar_volume < s.min_dollar_volume:
            return "obrót poniżej %.0f mln/dzień" % (s.min_dollar_volume / 1e6)
        return ""

    # -- arithmetic --------------------------------------------------------

    def _percentiles(self, candidates) -> dict:
        """{ticker: {factor: rank 0..1}} within this group of candidates."""
        ranks = dict((c.ticker, {}) for c in candidates)
        for factor in self.screener_settings.factor_weights:
            present = [(c.value(factor), c.ticker) for c in candidates
                       if c.value(factor) is not None]
            if not present:
                continue
            present.sort()
            count = len(present)
            index = 0
            while index < count:
                # Ties share the average of their positions.
                end = index
                while end + 1 < count and present[end + 1][0] == present[index][0]:
                    end += 1
                position = (index + end) / 2.0
                rank = 0.5 if count == 1 else position / (count - 1)
                for k in range(index, end + 1):
                    ranks[present[k][1]][factor] = rank
                index = end + 1
        return ranks

    def _score(self, own) -> tuple:
        weights = dict((f, w) for f, w in self.screener_settings.factor_weights.items()
                       if w > 0)
        total = sum(weights.values())
        used = sum(w for f, w in weights.items() if f in own)
        if used <= 0:
            return 0.0, 0.0
        score = 100.0 * sum(w * own[f] for f, w in weights.items() if f in own) / used
        return score, used / total

    def _extremes(self, own, best, count=3) -> list:
        weights = self.screener_settings.factor_weights
        ordered = sorted(own.items(), key=lambda item: item[1], reverse=best)
        chosen = [f for f, r in ordered if (r >= 0.7 if best else r <= 0.3)
                  and weights.get(f, 0) > 0]
        chosen.sort(key=lambda f: weights[f], reverse=True)
        return [self.screener_settings.label(f) for f in chosen[:count]]
