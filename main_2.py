"""Second entry point: the top 10 US stocks of every sector theme for a
1-6 month holding period.

Not a list of top gainers: each candidate is ranked inside its theme on the
factors with a documented record over that horizon -- medium-term momentum
(12-1 and 6-1 months), closeness to the 52-week high, analysts' targets and
earnings expectations, growth, quality, valuation against growth, and low
volatility -- with a penalty for a stock that has just run hot, plus the
StockAnalyser composite and, when installed, the Chronos-2 forecast.

Prints a table per theme, draws one bar chart per theme, and writes
screener.json and screener.csv into output/screener.
"""

import csv
import io
import json
import os

from FactorModel import FactorModel
from MarketData import MarketData
from PriceForecaster import PriceForecaster
from Recommendation import Recommendation
from ScreenerChart import ScreenerChart
from ScreenerSettings import ScreenerSettings
from SectorUniverse import SectorUniverse
from Settings import Settings
from ThemeRanker import ThemeRanker
from UniverseFetcher import UniverseFetcher


class ScreenerReport:
    """Runs the sector screen and renders the result."""

    def __init__(self, screener_settings, universe, universe_fetcher,
                 factor_model, theme_ranker, screener_chart, quiet=False):
        self.screener_settings = screener_settings
        self.universe = universe
        self.universe_fetcher = universe_fetcher
        self.factor_model = factor_model
        self.theme_ranker = theme_ranker
        self.screener_chart = screener_chart
        self.quiet = quiet
        self.candidates = {}        # ticker -> StockCandidate
        self.picks = {}             # theme -> [RankedPick]
        self.rejected = {}          # theme -> [(ticker, reason)]
        self.charts = {}            # theme -> png path

    # -- pipeline ----------------------------------------------------------

    def run(self):
        self._say("StockAnalyser screener -- %s" % self.screener_settings.describe())
        themes = self.universe.themes()
        tickers = self.universe.all_tickers()
        for note in self.universe.notes:
            self._say("  universe: %s" % note)
        self._say("  %d themes, %d distinct tickers -- downloading ..."
                  % (len(themes), len(tickers)))

        snapshots = self.universe_fetcher.fetch_all(tickers, self._progress)
        self._say("  measuring factors ...")
        for ticker in tickers:
            self.candidates[ticker] = self.factor_model.measure(snapshots[ticker])

        for theme, members in themes.items():
            group = [self.candidates[t] for t in members if t in self.candidates]
            picks, rejected = self.theme_ranker.rank(theme, group)
            self.picks[theme] = picks
            self.rejected[theme] = rejected
            try:
                path = self.screener_chart.draw(theme, picks)
                if path:
                    self.charts[theme] = path
            except Exception as problem:            # noqa: BLE001
                self._say("  chart for %s failed: %s" % (theme, problem))

        self._say("")
        self.print_themes()
        self.write_files()
        return self

    def _progress(self, done, total, ticker):
        if done == total or done % 25 == 0:
            self._say("    %d/%d downloaded (last: %s)" % (done, total, ticker))

    # -- rendering ---------------------------------------------------------

    def print_themes(self):
        for theme, picks in self.picks.items():
            self._say("=" * 100)
            self._say("%s -- top %d z %d kandydatów" % (
                theme, len(picks), len(self.universe.themes()[theme])))
            self._say("=" * 100)
            if not picks:
                self._say("  brak spółek spełniających filtry")
            else:
                self._say("  %-3s %-7s %-26s %6s %9s %8s %8s %8s %7s  %s" % (
                    "#", "TICKER", "NAZWA", "WYNIK", "CENA", "6-1M", "CEL", "EPS F",
                    "AI", "ATUTY"))
                for pick in picks:
                    self._say(self._row(pick))
                    if pick.weaknesses:
                        self._say("  %s ryzyka: %s" % (" " * 64,
                                                       ", ".join(pick.weaknesses)))
            dropped = self.rejected.get(theme, [])
            if dropped:
                self._say("  odrzucone (%d): %s" % (len(dropped), "; ".join(
                    "%s %s" % (t, r) for t, r in dropped[:8])
                    + (" ..." if len(dropped) > 8 else "")))
            chart = self.charts.get(theme)
            if chart:
                self._say("  wykres: %s" % chart)
            self._say("")
        self._say("WYNIK to średnia ważona percentyli czynników w danym temacie "
                  "(50 = środek tematu). To ranking względny, nie gwarancja wzrostu.")

    def _row(self, pick):
        c = pick.candidate
        f = c.factors
        return "  %-3d %-7s %-26s %6.1f %9s %8s %8s %8s %7s  %s" % (
            pick.rank, c.ticker, c.name[:26], pick.score,
            "n/a" if c.price is None else "%.2f" % c.price,
            self._pct(f.get("momentum_6_1")), self._pct(f.get("analyst_upside")),
            self._pct(f.get("forward_eps_growth")),
            "n/a" if c.forecast_change_pct is None else "%+.0f%%" % c.forecast_change_pct,
            ", ".join(pick.strengths))

    @staticmethod
    def _pct(value):
        return "n/a" if value is None else "%+.0f%%" % (100 * value)

    def _say(self, text):
        if not self.quiet:
            print(text, flush=True)

    # -- files -------------------------------------------------------------

    def write_files(self):
        directory = self.screener_settings.ensure_output_dir()
        payload = {
            "settings": self.screener_settings.describe(),
            "factor_weights": self.screener_settings.factor_weights,
            "themes": dict((theme, [p.to_dict() for p in picks])
                           for theme, picks in self.picks.items()),
            "rejected": dict((theme, [{"ticker": t, "reason": r} for t, r in items])
                             for theme, items in self.rejected.items()),
        }
        json_path = os.path.join(directory, "screener.json")
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, default=str, ensure_ascii=False)

        table = self.as_csv()
        csv_path = os.path.join(directory, "screener.csv")
        with open(csv_path, "w", encoding="utf-8", newline="") as handle:
            handle.write(table)
        if hasattr(csv, "show"):
            csv.show(table, "Screener -- top %d per theme, 1-6 months"
                     % self.screener_settings.top_n)
        self._say("Written: %s, %s, %d chart(s)" % (json_path, csv_path,
                                                    len(self.charts)))
        return {"json": json_path, "csv": csv_path}

    def as_csv(self):
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        factors = list(self.screener_settings.factor_weights)
        writer.writerow(["theme", "rank", "ticker", "name", "industry", "score",
                         "coverage", "price", "currency", "market_cap",
                         "analyser_rating", "forecast_change_pct", "strengths",
                         "weaknesses"] + factors)
        for theme, picks in self.picks.items():
            for p in picks:
                c = p.candidate
                writer.writerow([theme, p.rank, c.ticker, c.name, c.industry,
                                 round(p.score, 1), round(p.coverage, 2), c.price,
                                 c.currency, c.market_cap, c.rating,
                                 None if c.forecast_change_pct is None
                                 else round(c.forecast_change_pct, 2),
                                 " | ".join(p.strengths), " | ".join(p.weaknesses)]
                                + [None if c.value(f) is None else round(c.value(f), 4)
                                   for f in factors])
        return buffer.getvalue()


if __name__ == "__main__":
    run_settings = Settings(argv=[])
    screener_settings = ScreenerSettings(run_settings)
    analysis_settings = screener_settings.analysis_settings()
    forecaster = (PriceForecaster(analysis_settings)
                  if screener_settings.forecast_steps > 0 else None)
    ScreenerReport(
        screener_settings,
        SectorUniverse(screener_settings),
        UniverseFetcher(screener_settings, MarketData),
        FactorModel(screener_settings, Recommendation, forecaster),
        ThemeRanker(screener_settings),
        ScreenerChart(screener_settings),
    ).run()
