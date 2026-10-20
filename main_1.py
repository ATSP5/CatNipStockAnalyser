"""The entry point: fetch every ticker, score it, draw it, print the verdicts.

Prints a ranked summary table first -- best call at the top -- then a detailed
card per ticker showing what each of the three blocks found and which
individual signals drove the number, and how the technical score has fared in
a walk-forward backtest, and -- with a PriceForecaster -- where the AI model
expects the price to be FutureHorizon candles ahead. Writes the same content to
JSON and CSV beside the charts.

Nothing is hidden: a ticker Yahoo returns no candles for is still listed, as an
empty NO DATA analysis with the reason, and a ticker whose fundamentals held an
impossible value is marked "!" in the table, on its chart and in its card.
"""

import csv
import io
import json
import os
import traceback

from Backtest import Backtest
from CandleChart import CandleChart
from MarketData import MarketData
from PriceForecaster import PriceForecaster
from Recommendation import Recommendation
from Score import Score
from Settings import Settings


class Report:
    """Runs the whole pipeline and renders the result."""

    RATING_MARK = {
        "STRONG BUY": "++",
        "BUY": "+",
        "HOLD": "=",
        "SELL": "-",
        "STRONG SELL": "--",
        "NO DATA": "?",
    }
    SUSPECT_MARK = "!"

    def __init__(self, settings=None, draw=None, quiet=False, forecaster=None):
        self.settings = settings or Settings()
        self.forecaster = forecaster
        self.quiet = quiet
        self.draw = self.settings.draw_chart if draw is None else draw
        self.verdicts = []
        self.skipped = []
        self.charts = {}
        self.backtests = {}
        self.forecasts = {}
        self.run()

    # -- pipeline ----------------------------------------------------------

    def run(self):
        self._say("StockAnalyser -- %s" % self.settings.describe())
        for token in getattr(self.settings, "ignored", []):
            self._say("  ignored argument %r -- not a flag or a valid ticker"
                      % token)
        self._say("")

        for position, ticker in enumerate(self.settings.tickers, start=1):
            self._say("  [%d/%d] fetching %s ..."
                      % (position, len(self.settings.tickers), ticker))
            try:
                market = MarketData.fetch(ticker, self.settings)
            except Exception as problem:            # noqa: BLE001
                market = MarketData(ticker, self.settings)
                market.errors.append("fetch failed: %s" % problem)

            if not market.ok():
                self._say("    brak danych dla %s -- %s; pokazuję pustą analizę"
                          % (market.ticker, market.problem()))

            try:
                verdict = Recommendation(market, self.settings)
            except Exception as problem:            # noqa: BLE001
                self.skipped.append((ticker, "analysis failed: %s" % problem))
                if os.environ.get("STOCKANALYSER_DEBUG"):
                    traceback.print_exc()
                continue

            self.verdicts.append(verdict)

            if self.settings.backtest and verdict.has_data():
                try:
                    self.backtests[verdict.ticker] = Backtest(verdict, self.settings)
                except Exception as problem:        # noqa: BLE001
                    verdict.market.errors.append("backtest: %s" % problem)

            forecast = self._forecast(verdict)

            if self.draw:
                try:
                    path = CandleChart.draw(verdict, self.settings, forecast,
                                            note=self._forecast_note(forecast))
                    if path:
                        self.charts[verdict.ticker] = path
                except Exception as problem:        # noqa: BLE001
                    verdict.market.errors.append("chart: %s" % problem)

        # Strongest buy first, strongest sell last, empty analyses at the end.
        self.verdicts.sort(key=lambda v: (v.has_data(), v.score), reverse=True)

        self._say("")
        self.print_summary()
        self.print_details()
        self.write_files()
        return self

    def forecast_status(self):
        """Why there is or is not a forecast, for the summary and the JSON."""
        if self.forecaster is None:
            return "forecast off: no PriceForecaster connected"
        return self.forecaster.status()

    def _forecast_note(self, forecast):
        """Text for a chart that should carry a forecast but does not."""
        if forecast is not None or self.settings.future_horizon <= 0:
            return None
        return self.forecast_status()

    def _forecast(self, verdict):
        if self.forecaster is None or not self.forecaster.enabled():
            return None
        try:
            forecast = self.forecaster.forecast(verdict)
        except Exception as problem:                # noqa: BLE001
            verdict.market.errors.append("forecast: %s" % problem)
            return None
        if forecast is not None:
            self.forecasts[verdict.ticker] = forecast
        return forecast

    # -- rendering ---------------------------------------------------------

    def print_summary(self):
        if not self.verdicts:
            self._say("No ticker could be analysed.")
            self._print_skipped()
            return

        header = ("%-3s %-8s %-11s %8s %6s %8s %9s %8s"
                  % ("", "TICKER", "CALL", "SCORE", "DATA", "TECH", "VALUATION",
                     "SUPPLY"))
        self._say(header)
        self._say("-" * len(header))

        for verdict in self.verdicts:
            self._say("%-3s %-8s %-11s %8s %5.0f%% %8s %9s %8s" % (
                self.RATING_MARK.get(verdict.rating, "")
                + (self.SUSPECT_MARK if verdict.market.has_suspect_data() else ""),
                verdict.ticker,
                verdict.rating,
                self._cell(verdict.score if verdict.has_data() else None),
                100 * verdict.confidence,
                self._cell(verdict.block_score("technical")),
                self._cell(verdict.block_score("valuation")),
                self._cell(verdict.block_score("supply")),
            ))
        self._say("-" * len(header))
        self._say(self.forecast_status())
        self._say("DATA is how much of the intended evidence arrived, not how "
                  "likely the call is to be right.")
        pooled, samples = Backtest.pooled_ic(self.backtests.values())
        if pooled is not None:
            self._say("Backtest: technical score vs next-candle return, rank IC "
                      "%+.3f over %d candles across all tickers." % (pooled, samples))
        self._print_data_notes()
        self._print_skipped()

    def print_details(self):
        for verdict in self.verdicts:
            self._say("")
            self._say("=" * 78)
            price = verdict.market.last_price()
            self._say("%s -- %s" % (verdict.ticker, verdict.market.name()))
            self._say("  %s | %s | %s" % (
                verdict.market.exchange(), verdict.market.sector(),
                Score.human(verdict.market.market_cap()) + " cap",
            ))
            low, high = verdict.market.year_range()
            self._say("  Price %s %s   52-week range %s - %s   %d candles at %s" % (
                "n/a" if price is None else "%.2f" % price,
                verdict.market.currency(),
                "n/a" if low is None else "%.2f" % low,
                "n/a" if high is None else "%.2f" % high,
                verdict.market.bars(),
                self.settings.horizon_label(),
            ))
            self._say("")
            self._say("  CALL: %s   score %s   data coverage %.0f%%" % (
                verdict.rating,
                self._cell(verdict.score if verdict.has_data() else None),
                100 * verdict.confidence,
            ))
            if not verdict.has_data():
                self._say("  Brak danych: %s" % verdict.missing_reason())
            self._say("")

            for name in ("technical", "valuation", "supply"):
                block = verdict.blocks.get(name)
                if block is None:
                    self._say("  %-10s %8s   brak danych" % (name, "n/a"))
                    continue
                score = block.score()
                share = verdict.weights.get(name)
                points = verdict.contributions.get(name)
                self._say("  %-10s %8s   %d signals, %.0f%% coverage%s" % (
                    name,
                    self._cell(score),
                    len(block.signals),
                    100 * block.coverage(),
                    "" if share is None else ", weight %.0f%% -> %+.1f pts"
                    % (share, points),
                ))

            backtest = self.backtests.get(verdict.ticker)
            if backtest is not None:
                self._say("")
                self._say("  Backtest (technical): %s" % backtest.summary())

            forecast = self.forecasts.get(verdict.ticker)
            if forecast is not None:
                self._say("")
                self._say("  Forecast (%s, %d candles, to %s): median %.2f (%+.1f%%), "
                          "%.0f-%.0f%% band %.2f - %.2f" % (
                              forecast.model, forecast.steps,
                              str(forecast.timestamps[-1])[:16],
                              forecast.median[-1], forecast.change_pct(),
                              100 * forecast.quantiles[0], 100 * forecast.quantiles[-1],
                              forecast.low[-1], forecast.high[-1]))
                if forecast.has_inner():
                    self._say("  %s%.0f-%.0f%% band %.2f - %.2f" % (
                        " " * 10, 100 * forecast.inner_quantiles[0],
                        100 * forecast.inner_quantiles[1],
                        forecast.inner_low[-1], forecast.inner_high[-1]))

            self._print_data_quality(verdict.market)

            self._say("")
            self._print_reasons("  Supporting a buy:", verdict.reasons(3, True))
            self._print_reasons("  Arguing against:", verdict.reasons(3, False))

            notes = verdict.notes()
            if notes:
                self._say("")
                self._say("  Notes:")
                for note in notes[:6]:
                    self._say("    - %s" % note)

            chart = self.charts.get(verdict.ticker)
            if chart:
                self._say("")
                self._say("  Chart: %s" % chart)

    def _print_reasons(self, heading, reasons):
        if not reasons:
            return
        self._say(heading)
        for name, signal in reasons:
            self._say("    %+6.0f  %-30s %s" % (
                signal.score, "%s (%s)" % (signal.label, name), signal.detail,
            ))

    def _print_data_notes(self):
        """Footnotes under the table for empty and suspect analyses."""
        empty = [v for v in self.verdicts if not v.has_data()]
        suspect = [v for v in self.verdicts if v.market.has_suspect_data()]
        if not (empty or suspect):
            return
        self._say("")
        for verdict in empty:
            self._say("  NO DATA %-8s %s -- analiza pusta; sprawdź symbol w Yahoo "
                      "Finance (np. sufiks giełdy: .DE, .KS, .HK)"
                      % (verdict.ticker, verdict.missing_reason()))
        if suspect:
            self._say("  %s = możliwe błędne dane Yahoo (%s): wartość niemożliwa "
                      "lub nieprzeliczalna została pominięta w ocenie, "
                      "szczegóły w karcie tickera."
                      % (self.SUSPECT_MARK,
                         ", ".join(v.ticker for v in suspect)))

    def _print_data_quality(self, market):
        """What was wrong in Yahoo's figures: repaired, and dropped."""
        if market.data_fixes:
            self._say("")
            self._say("  Dane poprawione (Yahoo miesza waluty / liczy EV z błędnej "
                      "liczby akcji):")
            for text in market.data_fixes:
                self._say("    - %s" % text)
        if market.data_warnings:
            self._say("")
            self._say("  %s Możliwe błędne dane -- pominięte w ocenie:"
                      % self.SUSPECT_MARK)
            for text in market.data_warnings:
                self._say("    - %s" % text)

    def _print_skipped(self):
        for ticker, reason in self.skipped:
            self._say("  skipped %-8s %s" % (ticker, reason))

    @staticmethod
    def _cell(score):
        return "n/a" if score is None else "%+.1f" % score

    def _say(self, text):
        if not self.quiet:
            print(text)

    # -- files -------------------------------------------------------------

    def write_files(self):
        """Save the run as JSON and CSV next to the charts."""
        if not self.verdicts:
            return {}
        directory = self.settings.ensure_output_dir()
        written = {}

        results = []
        for verdict in self.verdicts:
            entry = verdict.to_dict()
            backtest = self.backtests.get(verdict.ticker)
            if backtest is not None:
                entry["backtest"] = backtest.to_dict()
            forecast = self.forecasts.get(verdict.ticker)
            if forecast is not None:
                entry["forecast"] = forecast.to_dict()
            results.append(entry)

        pooled, samples = Backtest.pooled_ic(self.backtests.values())
        payload = {
            "horizon": self.settings.horizon,
            "lookback": self.settings.resolved_lookback(),
            "weights": self.settings.normalised_weights(),
            "backtest_pooled_ic": None if pooled is None else round(pooled, 4),
            "backtest_samples": samples,
            "future_horizon": self.settings.future_horizon,
            "forecast_status": self.forecast_status(),
            "results": results,
            "skipped": [{"ticker": t, "reason": r} for t, r in self.skipped],
        }
        json_path = os.path.join(directory, "analysis.json") if directory \
            else "analysis.json"
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, default=str)
        written["json"] = json_path

        csv_path = os.path.join(directory, "analysis.csv") if directory \
            else "analysis.csv"
        table = self.as_csv()
        with open(csv_path, "w", encoding="utf-8", newline="") as handle:
            handle.write(table)
        written["csv"] = csv_path

        # Inside CatNip, csv.show puts the table in the Output tab beside the
        # charts. It does not exist outside the run engine, hence the check.
        if hasattr(csv, "show"):
            csv.show(table, "StockAnalyser -- %s candles"
                     % self.settings.horizon_label())

        self._say("")
        self._say("Written: %s, %s%s" % (
            json_path, csv_path,
            ", %d chart(s)" % len(self.charts) if self.charts else "",
        ))
        return written

    def as_csv(self):
        """The summary table as CSV text: one row per ticker."""
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow([
            "ticker", "name", "rating", "score", "confidence",
            "technical", "valuation", "supply", "price", "currency",
            "market_cap", "shares_outstanding", "year_low", "year_high",
            "backtest_ic", "backtest_strategy_pct", "backtest_buy_hold_pct",
            "forecast_steps", "forecast_median", "forecast_low",
            "forecast_high", "forecast_inner_low", "forecast_inner_high",
            "forecast_change_pct", "data_warnings", "data_fixes",
        ])
        for verdict in self.verdicts:
            low, high = verdict.market.year_range()
            backtest = self.backtests.get(verdict.ticker)
            tested = backtest.to_dict() if backtest is not None else {}
            forecast = self.forecasts.get(verdict.ticker)
            ahead = forecast.to_dict() if forecast is not None else {}
            writer.writerow([
                verdict.ticker,
                verdict.market.name(),
                verdict.rating,
                round(verdict.score, 1) if verdict.has_data() else None,
                round(verdict.confidence, 2),
                self._cell(verdict.block_score("technical")),
                self._cell(verdict.block_score("valuation")),
                self._cell(verdict.block_score("supply")),
                verdict.market.last_price(),
                verdict.market.currency(),
                verdict.market.market_cap(),
                verdict.market.shares_outstanding(),
                low,
                high,
                tested.get("ic"),
                tested.get("strategy_return_pct"),
                tested.get("buy_hold_return_pct"),
                ahead.get("steps"),
                ahead.get("median_end"),
                ahead.get("low_end"),
                ahead.get("high_end"),
                ahead.get("inner_low_end"),
                ahead.get("inner_high_end"),
                ahead.get("change_pct"),
                " | ".join(verdict.market.data_warnings),
                " | ".join(verdict.market.data_fixes),
            ])
        return buffer.getvalue()

    # -- reading the result programmatically -------------------------------

    def best(self):
        """The strongest buy candidate, or None."""
        return self.verdicts[0] if self.verdicts else None

    def by_rating(self, rating):
        return [v for v in self.verdicts if v.rating == rating]

    def as_dict(self):
        return dict((v.ticker, v.to_dict()) for v in self.verdicts)


if __name__ == "__main__":
    run_settings = Settings()
    Report(run_settings, forecaster=PriceForecaster(run_settings))
