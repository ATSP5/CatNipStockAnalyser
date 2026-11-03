"""Builds the candidate list of every theme: the curated tickers, topped up
with the largest US-listed members of the theme's Yahoo industries."""

import logging
import os
import re

if not os.environ.get("STOCKANALYSER_DEBUG"):
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)


class SectorUniverse:
    """theme -> candidate tickers, resolved once per run."""

    US_EXCHANGES = ("NMS", "NGM", "NCM", "NYQ", "ASE")   # Nasdaq x3, NYSE, NYSE American

    def __init__(self, screener_settings):
        self.screener_settings = screener_settings
        self.notes = []
        self._themes = None

    def universe(self):
        return self

    # -- public ------------------------------------------------------------

    def themes(self) -> dict:
        """{theme: [ticker, ...]} -- curated first, Yahoo additions after."""
        if self._themes is None:
            self._themes = dict((theme, self._candidates(spec))
                                for theme, spec in
                                self.screener_settings.themes.items())
        return self._themes

    def all_tickers(self) -> list:
        """Every distinct ticker across the themes, in first-seen order."""
        seen = []
        for tickers in self.themes().values():
            for ticker in tickers:
                if ticker not in seen:
                    seen.append(ticker)
        return seen

    # -- building ----------------------------------------------------------

    def _candidates(self, spec) -> list:
        limit = self.screener_settings.max_candidates_per_theme
        tickers = self._clean(spec.get("tickers", []))
        if self.screener_settings.use_yahoo_screener:
            for industry in self._industries(spec.get("industries", [])):
                for ticker in self._screen(industry):
                    if ticker not in tickers:
                        tickers.append(ticker)
        return tickers[:limit] if limit else tickers

    @staticmethod
    def _clean(raw) -> list:
        seen = []
        for item in raw:
            symbol = str(item).strip().upper()
            if symbol and symbol not in seen:
                seen.append(symbol)
        return seen

    @staticmethod
    def _plain(text) -> str:
        """Yahoo spells 'Banks—Regional' with an em dash; compare in ASCII."""
        return re.sub(r"[^a-z0-9&]+", " ", str(text).lower()).strip()

    def _industries(self, keywords) -> list:
        """Yahoo industry names matching the theme's keywords."""
        if not keywords:
            return []
        try:
            from yfinance.const import EQUITY_SCREENER_EQ_MAP
        except Exception as problem:                # noqa: BLE001
            self._note("Yahoo industry list unavailable: %s" % problem)
            return []
        known = []
        for names in EQUITY_SCREENER_EQ_MAP.get("industry", {}).values():
            known.extend(names)
        matched = []
        for keyword in keywords:
            wanted = self._plain(keyword)
            hits = [name for name in known if wanted in self._plain(name)]
            if not hits:
                self._note("no Yahoo industry matches %r" % keyword)
            for name in hits:
                if name not in matched:
                    matched.append(name)
        return matched

    def _screen(self, industry) -> list:
        """The largest US-listed companies of one Yahoo industry."""
        try:
            import yfinance as yf
            from yfinance import EquityQuery as Q
            query = Q("and", [
                Q("eq", ["region", "us"]),
                Q("is-in", ["exchange"] + list(self.US_EXCHANGES)),
                Q("eq", ["industry", industry]),
                Q("gt", ["intradaymarketcap", self.screener_settings.min_market_cap]),
            ])
            found = yf.screen(query, size=self.screener_settings.screen_size_per_industry,
                              sortField="intradaymarketcap", sortAsc=False)
        except Exception as problem:                # noqa: BLE001
            self._note("Yahoo screener failed for %s: %s" % (industry, problem))
            return []
        quotes = (found or {}).get("quotes", [])
        return self._clean(q.get("symbol", "") for q in quotes
                           if q.get("quoteType", "EQUITY") == "EQUITY")

    def _note(self, text):
        if text not in self.notes:
            self.notes.append(text)
