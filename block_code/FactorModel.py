"""Measures the 1-6 month factors of one fetched ticker.

Every factor is oriented so that a higher value is better: volatility, PEG,
last month's return and the analyst rating (1 = strong buy) are negated.
A factor that cannot be measured is None and simply carries no weight later.
"""

import math

import numpy as np

from StockCandidate import StockCandidate


class FactorModel:
    """MarketData -> StockCandidate with raw factor values."""

    TRADING_DAYS = 252
    MONTH = 21
    HALF_YEAR = 126
    # Caps against Yahoo outliers (ratios as fractions, not percent).
    CAPS = {
        "analyst_upside": (-0.9, 3.0),
        "forward_eps_growth": (-1.0, 3.0),
        "earnings_growth": (-1.0, 5.0),
        "revenue_growth": (-1.0, 3.0),
        "return_on_equity": (-1.0, 1.5),
        "profit_margin": (-1.0, 1.0),
    }

    def __init__(self, screener_settings, Recommendation, forecaster=None):
        self.screener_settings = screener_settings
        self.recommendation = Recommendation     # the Recommendation class (block 9)
        self.forecaster = forecaster             # PriceForecaster or None

    def factor_model(self):
        return self

    # -- public ------------------------------------------------------------

    def measure(self, market) -> StockCandidate:
        """All factors of one ticker; never raises."""
        settings = self.screener_settings.analysis_settings()
        candidate = StockCandidate(
            ticker=market.ticker,
            name=market.name(),
            industry=market.text("industry", default=market.sector()),
            price=market.last_price(),
            currency=market.currency(),
            market_cap=market.market_cap(),
            dollar_volume=self._dollar_volume(market),
            bars=len(market.daily),
            rating="NO DATA",
        )
        candidate.problems.extend(market.errors)
        if not market.ok():
            candidate.problems.append(market.problem() or "no candles")
            return candidate

        verdict = None
        try:
            verdict = self.recommendation(market, settings)
            candidate.rating = verdict.rating
        except Exception as problem:                # noqa: BLE001
            candidate.problems.append("analysis failed: %s" % problem)

        factors = {}
        factors.update(self._price_factors(market))
        factors.update(self._analyst_factors(market, candidate.price))
        factors.update(self._fundamental_factors(market))
        factors["analysis_score"] = (verdict.score if verdict is not None
                                     and verdict.has_data() else None)
        factors["forecast"] = self._forecast(verdict, candidate)
        candidate.factors = dict((k, v) for k, v in factors.items()
                                 if k in self.screener_settings.factor_weights)
        return candidate

    # -- price history -----------------------------------------------------

    def _price_factors(self, market) -> dict:
        closes = market.daily["Close"].dropna().to_numpy(dtype=float)
        highs = market.daily["High"].dropna().to_numpy(dtype=float) \
            if "High" in market.daily else closes
        count = len(closes)
        last = closes[-1] if count else None
        out = {}
        out["momentum_12_1"] = self._change(closes, self.TRADING_DAYS, self.MONTH)
        out["momentum_6_1"] = self._change(closes, self.HALF_YEAR, self.MONTH)
        month = self._change(closes, self.MONTH, 0)
        out["reversal_1m"] = None if month is None else -month
        year_high = highs[-self.TRADING_DAYS:].max() if len(highs) else None
        out["high_proximity"] = (last / year_high if last and year_high else None)
        out["trend"] = (last / closes[-200:].mean() - 1.0 if count >= 200 else None)
        if count > self.HALF_YEAR:
            returns = np.diff(np.log(closes[-self.HALF_YEAR - 1:]))
            out["low_volatility"] = -float(np.std(returns) * math.sqrt(self.TRADING_DAYS))
        else:
            out["low_volatility"] = None
        return out

    @staticmethod
    def _change(closes, start_back, end_back):
        """Return from `start_back` candles ago to `end_back` candles ago."""
        if len(closes) <= start_back:
            return None
        start = closes[-1 - start_back]
        end = closes[-1 - end_back]
        return float(end / start - 1.0) if start > 0 else None

    # -- analysts ----------------------------------------------------------

    def _analyst_factors(self, market, price) -> dict:
        opinions = market.field("numberOfAnalystOpinions") or 0
        if opinions < self.screener_settings.min_analysts:
            return {"analyst_upside": None, "analyst_rating": None}
        target = market.field("targetMeanPrice")
        upside = target / price - 1.0 if target and price else None
        mean = market.field("recommendationMean")
        return {
            "analyst_upside": self._cap("analyst_upside", upside),
            "analyst_rating": None if mean is None else -mean,
        }

    # -- fundamentals ------------------------------------------------------

    def _fundamental_factors(self, market) -> dict:
        trailing = market.field("trailingEps")
        forward = market.field("forwardEps")
        eps_growth = (forward / trailing - 1.0
                      if trailing and forward and trailing > 0 else None)
        peg = market.field("trailingPegRatio", "pegRatio")
        fcf = market.free_cash_flow_yield()          # percent, checked
        return {
            "forward_eps_growth": self._cap("forward_eps_growth", eps_growth),
            "earnings_growth": self._cap("earnings_growth", market.field(
                "earningsQuarterlyGrowth", "earningsGrowth")),
            "revenue_growth": self._cap("revenue_growth",
                                        market.field("revenueGrowth")),
            "return_on_equity": self._cap("return_on_equity",
                                          market.field("returnOnEquity")),
            "profit_margin": self._cap("profit_margin",
                                       market.field("profitMargins")),
            "fcf_yield": None if fcf is None else fcf / 100.0,
            "peg": -peg if peg and peg > 0 else None,
        }

    def _cap(self, name, value):
        if value is None:
            return None
        low, high = self.CAPS[name]
        return max(low, min(high, float(value)))

    @staticmethod
    def _dollar_volume(market):
        volume = market.average_volume()
        price = market.last_price()
        return volume * price if volume and price else None

    # -- AI forecast -------------------------------------------------------

    def _forecast(self, verdict, candidate):
        if (self.forecaster is None or verdict is None
                or "forecast" not in self.screener_settings.factor_weights
                or not self.forecaster.enabled()):
            return None
        try:
            forecast = self.forecaster.forecast(verdict)
        except Exception as problem:                # noqa: BLE001
            candidate.problems.append("forecast: %s" % problem)
            return None
        if forecast is None:
            return None
        candidate.forecast_change_pct = forecast.change_pct()
        return forecast.change_pct() / 100.0
