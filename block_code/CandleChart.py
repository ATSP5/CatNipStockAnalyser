"""Draws the candlestick chart, at whatever horizon the run asked for.

Four stacked panels share one x axis: candles with moving averages and the
Bollinger envelope, then volume, then RSI, then MACD. Candles are plotted
against their position in the series rather than against real time, so weekends
and overnight gaps do not open blank stretches in the middle of the chart.

With a PriceForecast the price panel continues past the last candle: the AI
model's median close and its 10-90% band, separated from the real candles by
a vertical dashed line drawn through every panel.
"""

import os

import matplotlib

matplotlib.use("Agg")               # write files; never try to open a window

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


class CandleChart:
    """Renders one enriched OHLCV frame to a PNG."""

    UP = "#26a69a"
    DOWN = "#ef5350"
    INK = "#2b2b2b"
    MUTED = "#8a8a8a"
    FORECAST = "#7b1fa2"

    RATING_COLOUR = {
        "STRONG BUY": "#1b7f3b",
        "BUY": "#4caf50",
        "HOLD": "#c9a227",
        "SELL": "#ef5350",
        "STRONG SELL": "#b71c1c",
        "NO DATA": "#8a8a8a",
    }

    def __init__(self, verdict, settings, forecast=None, note=None):
        self.verdict = verdict
        self.settings = settings
        self.forecast = forecast
        self.note = note
        self.market = verdict.market
        self.path = None

    # -- entry point -------------------------------------------------------

    @classmethod
    def draw(cls, verdict, settings, forecast=None, note=None):
        """Render and save. Returns the file path, or None if it could not.

        note: shown on the price panel when a forecast was wanted but is
        missing, so a chart without one says why.
        """
        chart = cls(verdict, settings, forecast, note)
        return chart.render()

    def render(self):
        frame = self.verdict.frame
        if frame is None or len(frame) < 2:
            return None

        window = frame.tail(max(20, self.settings.chart_candles))
        positions = range(len(window))

        figure, axes = plt.subplots(
            4, 1, figsize=(13, 10), sharex=True,
            gridspec_kw={"height_ratios": [3.2, 0.9, 1.0, 1.0]},
        )
        figure.subplots_adjust(hspace=0.08, left=0.07, right=0.94,
                               top=0.92, bottom=0.08)

        self._price_panel(axes[0], window, positions)
        self._volume_panel(axes[1], window, positions)
        self._rsi_panel(axes[2], window, positions)
        self._macd_panel(axes[3], window, positions)
        self._forecast(axes[0], window)
        self._note(axes[0])
        self._time_axis(axes[3], window)
        self._today_line(axes, window)

        for axis in axes:
            axis.grid(True, alpha=0.15, linewidth=0.6)
            axis.set_axisbelow(True)
            for side in ("top", "right"):
                axis.spines[side].set_visible(False)

        figure.suptitle(self._title(), fontsize=13, fontweight="bold",
                        color=self.INK, x=0.07, ha="left")
        figure.text(0.94, 0.955, self.verdict.rating, ha="right", fontsize=14,
                    fontweight="bold",
                    color=self.RATING_COLOUR.get(self.verdict.rating, self.INK))

        self.path = self._destination()
        figure.savefig(self.path, dpi=110, facecolor="white")

        # CatNip's run engine replaces show() with its own capture, which puts
        # the figure in the Output tab. Calling the real Agg show() would only
        # warn that it cannot display anything, so do it only when replaced.
        if getattr(plt.show, "__module__", "") != "matplotlib.pyplot":
            plt.show()
        plt.close(figure)
        return self.path

    # -- panels ------------------------------------------------------------

    def _price_panel(self, axis, window, positions):
        opens = window["Open"].to_numpy()
        highs = window["High"].to_numpy()
        lows = window["Low"].to_numpy()
        closes = window["Close"].to_numpy()

        # One thin line for the wick, one rectangle for the body.
        width = 0.62
        for index in positions:
            rising = closes[index] >= opens[index]
            colour = self.UP if rising else self.DOWN
            axis.vlines(index, lows[index], highs[index], color=colour,
                        linewidth=0.8, zorder=2)
            bottom = min(opens[index], closes[index])
            height = abs(closes[index] - opens[index])
            if height < 1e-9:
                # A doji has no body -- draw a hairline so it stays visible.
                axis.hlines(closes[index], index - width / 2, index + width / 2,
                            color=colour, linewidth=1.0, zorder=3)
            else:
                axis.add_patch(Rectangle(
                    (index - width / 2, bottom), width, height,
                    facecolor=colour, edgecolor=colour, linewidth=0.5, zorder=3,
                ))

        if "BB_UPPER" in window and window["BB_UPPER"].notna().any():
            axis.fill_between(list(positions), window["BB_LOWER"],
                              window["BB_UPPER"], color="#5c6bc0", alpha=0.07,
                              zorder=1, label="Bollinger (20, 2)")

        for column, colour, label in (
            ("SMA20", "#1e88e5", "SMA 20"),
            ("SMA50", "#fb8c00", "SMA 50"),
            ("SMA200", "#6a1b9a", "SMA 200"),
        ):
            if column in window and window[column].notna().any():
                axis.plot(list(positions), window[column], color=colour,
                          linewidth=1.2, label=label, zorder=4)

        axis.set_ylabel("Price (%s)" % self.market.currency(), fontsize=9)
        axis.legend(loc="upper left", fontsize=8, framealpha=0.85, ncol=4)

    def _volume_panel(self, axis, window, positions):
        if "Volume" not in window:
            axis.set_visible(False)
            return
        opens = window["Open"].to_numpy()
        closes = window["Close"].to_numpy()
        colours = [self.UP if closes[i] >= opens[i] else self.DOWN
                   for i in positions]
        axis.bar(list(positions), window["Volume"], color=colours, width=0.62,
                 alpha=0.65)
        if "VOL_SMA20" in window and window["VOL_SMA20"].notna().any():
            axis.plot(list(positions), window["VOL_SMA20"], color=self.MUTED,
                      linewidth=1.0)
        axis.set_ylabel("Volume", fontsize=9)
        axis.tick_params(labelsize=8)

    def _rsi_panel(self, axis, window, positions):
        if "RSI" not in window or not window["RSI"].notna().any():
            axis.set_visible(False)
            return
        axis.plot(list(positions), window["RSI"], color="#5e35b1", linewidth=1.2)
        axis.axhline(70, color=self.DOWN, linewidth=0.8, linestyle="--", alpha=0.7)
        axis.axhline(30, color=self.UP, linewidth=0.8, linestyle="--", alpha=0.7)
        axis.fill_between(list(positions), 30, 70, color="#5e35b1", alpha=0.04)
        axis.set_ylim(0, 100)
        axis.set_yticks([0, 30, 50, 70, 100])
        axis.set_ylabel("RSI", fontsize=9)
        axis.tick_params(labelsize=8)

    def _macd_panel(self, axis, window, positions):
        if "MACD" not in window or not window["MACD"].notna().any():
            axis.set_visible(False)
            return
        histogram = window["MACD_HIST"]
        colours = [self.UP if value >= 0 else self.DOWN
                   for value in histogram.fillna(0.0)]
        axis.bar(list(positions), histogram, color=colours, width=0.62, alpha=0.5)
        axis.plot(list(positions), window["MACD"], color="#1e88e5", linewidth=1.1,
                  label="MACD")
        axis.plot(list(positions), window["MACD_SIGNAL"], color="#fb8c00",
                  linewidth=1.1, label="Signal")
        axis.axhline(0, color=self.MUTED, linewidth=0.7)
        axis.set_ylabel("MACD", fontsize=9)
        axis.legend(loc="upper left", fontsize=8, framealpha=0.85, ncol=2)
        axis.tick_params(labelsize=8)

    def _forecast(self, axis, window):
        """Median forecast and its band, starting from the last real close."""
        if self.forecast is None or not self.forecast.steps:
            return
        last = len(window) - 1
        close = float(window["Close"].iloc[-1])
        x = [last] + [last + 1 + i for i in range(self.forecast.steps)]
        low = [close] + list(self.forecast.low)
        high = [close] + list(self.forecast.high)
        median = [close] + list(self.forecast.median)
        lo_q, _, hi_q = self.forecast.quantiles
        axis.fill_between(x, low, high, color=self.FORECAST, alpha=0.12,
                          linewidth=0, zorder=1,
                          label="Forecast %.0f-%.0f%%" % (100 * lo_q, 100 * hi_q))
        if self.forecast.has_inner():
            in_lo, in_hi = self.forecast.inner_quantiles
            axis.fill_between(
                x, [close] + list(self.forecast.inner_low),
                [close] + list(self.forecast.inner_high),
                color=self.FORECAST, alpha=0.28, linewidth=0, zorder=2,
                label="Forecast %.0f-%.0f%% (median ±%.0f pp)" % (
                    100 * in_lo, 100 * in_hi, 50 * (in_hi - in_lo)))
        axis.plot(x, median, color=self.FORECAST, linewidth=1.6, zorder=5,
                  label="Forecast median (%s)" % self.forecast.model.split("/")[-1])
        axis.legend(loc="upper left", fontsize=8, framealpha=0.85, ncol=3)

    def _note(self, axis):
        if not self.note or self.forecast is not None:
            return
        axis.text(0.99, 0.03, self.note, transform=axis.transAxes, ha="right",
                  va="bottom", fontsize=8, color=self.DOWN, wrap=True,
                  bbox={"facecolor": "white", "edgecolor": self.DOWN,
                        "alpha": 0.9, "boxstyle": "round,pad=0.3"}, zorder=7)

    def _today_line(self, axes, window):
        """Dashed vertical line between the last real candle and the forecast."""
        if self.forecast is None or not self.forecast.steps:
            return
        boundary = len(window) - 0.5
        for axis in axes:
            if axis.get_visible():
                axis.axvline(boundary, color=self.INK, linestyle="--",
                             linewidth=1.0, alpha=0.7, zorder=6)
        top = axes[0]
        top.text(boundary - 0.6, 0.02, "history", transform=top.get_xaxis_transform(),
                 ha="right", va="bottom", fontsize=8, color=self.MUTED)
        top.text(boundary + 0.6, 0.02, "forecast", transform=top.get_xaxis_transform(),
                 ha="left", va="bottom", fontsize=8, color=self.FORECAST)

    # -- axis furniture ----------------------------------------------------

    def _time_axis(self, axis, window):
        """Label roughly ten evenly spaced candles with their real timestamps.

        Forecast candles continue the axis with their expected timestamps.
        """
        stamps = list(window.index)
        if self.forecast is not None:
            stamps += list(self.forecast.timestamps)
        count = len(stamps)
        step = max(1, count // 10)
        ticks = list(range(0, count, step))
        fmt = "%Y-%m-%d %H:%M" if self.settings.is_intraday() else "%Y-%m-%d"
        labels = []
        for position in ticks:
            stamp = stamps[position]
            try:
                labels.append(stamp.strftime(fmt))
            except AttributeError:
                labels.append(str(stamp)[:16])
        axis.set_xticks(ticks)
        axis.set_xticklabels(labels, rotation=45, ha="right", fontsize=8)
        axis.set_xlim(-1, count)

    def _title(self):
        title = "%s  --  %s candles  |  %s  |  score %+.1f" % (
            self.market.ticker,
            self.settings.horizon_label(),
            self.market.name()[:48],
            self.verdict.score,
        )
        if self.forecast is not None:
            title += "  |  forecast %d candles: %+.1f%%" % (
                self.forecast.steps, self.forecast.change_pct())
        return title

    def _destination(self):
        directory = self.settings.ensure_output_dir()
        safe = "".join(c if c.isalnum() or c in "-_." else "_"
                       for c in self.market.ticker)
        filename = "%s_%s.png" % (safe, self.settings.horizon)
        return os.path.join(directory, filename) if directory else filename
