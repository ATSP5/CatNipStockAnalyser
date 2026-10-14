"""Forecasts future closes with Chronos-2, a pretrained time-series model.

Chronos-2 (Amazon, 2025) is a foundation model trained on a large corpus of
time series; it forecasts a series it has never seen without any fitting
("zero-shot") and returns quantiles, so the chart can show a band instead of
a single line. It knows only the price history it is given -- no news, no
fundamentals -- so the band is a statistical continuation, not a prophecy.

Needs the pip package `chronos-forecasting` (it brings torch and
transformers). The weights (~0.5 GB) are downloaded from Hugging Face on the
first use and kept in MODEL_CACHE beside the project.
"""

import os

import numpy as np
import pandas as pd

from PriceForecast import PriceForecast


class PriceForecaster:
    """Turns a verdict's close prices into a PriceForecast."""

    MODEL_ID = "amazon/chronos-2"
    MODEL_CACHE = "models"
    QUANTILES = (0.1, 0.5, 0.9)              # outer band and median
    INNER_QUANTILES = (0.24, 0.76)           # median +/- 26 pp; None = off
    MAX_CONTEXT = 2048           # the newest candles the model gets to read
    MIN_CONTEXT = 32             # fewer than this and no forecast is made

    # interval -> pandas frequency of the future candles (for the time axis)
    FREQUENCIES = {
        "1m": "1min", "2m": "2min", "5m": "5min", "15m": "15min",
        "30m": "30min", "60m": "60min", "1h": "60min", "90m": "90min",
        "1d": "B", "5d": "7D", "1wk": "7D", "1mo": "MS", "3mo": "QS",
    }

    def __init__(self, settings, model_id=MODEL_ID, cache_dir=MODEL_CACHE):
        self.settings = settings
        self.model_id = model_id
        self.cache_dir = cache_dir
        self.problem = None          # why forecasts are off, once known
        self._pipeline = None

    def forecaster(self):
        return self

    # -- public ------------------------------------------------------------

    def enabled(self):
        return self.settings.future_horizon > 0 and self.problem is None

    def status(self):
        """One line for the report: what the forecast is, or why there is none."""
        if self.settings.future_horizon <= 0:
            return "forecast off: future_horizon is 0"
        if self.problem is not None:
            return self.problem
        if self._pipeline is None:
            return "forecast not run yet"
        bands = "%d-%d%%" % (round(100 * self.QUANTILES[0]),
                             round(100 * self.QUANTILES[-1]))
        if self.INNER_QUANTILES:
            bands += " and %d-%d%%" % (round(100 * self.INNER_QUANTILES[0]),
                                       round(100 * self.INNER_QUANTILES[1]))
        return "forecast: %s, %d candles ahead, %s bands" % (
            self.model_id, self.settings.future_horizon, bands)

    def forecast(self, verdict):
        """PriceForecast for the verdict's ticker, or None when there is none."""
        if not self.enabled() or verdict.frame is None:
            return None
        closes = verdict.frame["Close"].dropna()
        if len(closes) < self.MIN_CONTEXT:
            return None
        pipeline = self._load()
        if pipeline is None:
            return None

        steps = int(self.settings.future_horizon)
        context = closes.to_numpy(dtype=np.float32)[-self.MAX_CONTEXT:]
        levels = sorted(set(self.QUANTILES) | set(self.INNER_QUANTILES or ()))
        quantiles, _ = pipeline.predict_quantiles(
            [context], prediction_length=steps, quantile_levels=levels,
        )
        band = quantiles[0][0].cpu().numpy()          # (steps, levels)
        at = dict((level, band[:, i]) for i, level in enumerate(levels))
        inner = self.INNER_QUANTILES
        return PriceForecast(
            ticker=verdict.ticker,
            model=self.model_id,
            last_close=float(context[-1]),
            timestamps=self.future_timestamps(closes.index[-1], steps),
            low=at[self.QUANTILES[0]], median=at[self.QUANTILES[1]],
            high=at[self.QUANTILES[2]],
            quantiles=self.QUANTILES,
            inner_low=at[inner[0]] if inner else None,
            inner_high=at[inner[1]] if inner else None,
            inner_quantiles=inner,
        )

    def future_timestamps(self, last, steps):
        """Where the next `steps` candles fall: business days for 1d, etc.

        Intraday candles are spaced evenly and ignore market hours, so their
        labels are approximate.
        """
        frequency = self.FREQUENCIES.get(self.settings.horizon, "B")
        return list(pd.date_range(start=last, periods=steps + 1,
                                  freq=frequency)[1:])

    # -- model -------------------------------------------------------------

    def _load(self):
        if self._pipeline is not None or self.problem is not None:
            return self._pipeline
        try:
            import torch
            import chronos
        except ImportError as missing:
            self.problem = ("forecast off: %s -- install the pip package "
                            "chronos-forecasting" % missing)
            print(self.problem, flush=True)
            return None
        Chronos2Pipeline = getattr(chronos, "Chronos2Pipeline", None)
        if Chronos2Pipeline is None:
            # `import chronos` also matches unrelated PyPI packages, and
            # chronos-forecasting before 2.0 has no Chronos-2.
            self.problem = ("forecast off: the installed 'chronos' module has no "
                            "Chronos2Pipeline -- install chronos-forecasting>=2.0 "
                            "(and uninstall the unrelated 'chronos' package)")
            print(self.problem, flush=True)
            return None
        device = "cuda" if torch.cuda.is_available() else "cpu"
        if self.cache_dir:
            os.makedirs(self.cache_dir, exist_ok=True)
        print("Loading %s on %s ..." % (self.model_id, device), flush=True)
        try:
            self._pipeline = Chronos2Pipeline.from_pretrained(
                self.model_id, device_map=device, cache_dir=self.cache_dir,
            )
        except Exception as problem:            # noqa: BLE001
            self.problem = "forecast off: could not load %s: %s" % (
                self.model_id, problem)
            print(self.problem)
        return self._pipeline
