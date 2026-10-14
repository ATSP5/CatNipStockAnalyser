"""Technical indicator maths, written directly on pandas -- no TA-Lib needed.

Every function takes and returns pandas objects and is safe on short history:
when there are not enough candles to fill a window the result is NaN rather
than an exception, and the analysis blocks skip the signal.
"""

import numpy as np
import pandas as pd


class Indicators:
    """Stateless indicator maths plus one convenience method, `enrich`."""

    # -- moving averages ---------------------------------------------------

    @staticmethod
    def sma(series, window):
        return series.rolling(window=window, min_periods=window).mean()

    @staticmethod
    def ema(series, span):
        return series.ewm(span=span, adjust=False, min_periods=span).mean()

    # -- oscillators -------------------------------------------------------

    @staticmethod
    def rsi(series, window=14):
        """Wilder's Relative Strength Index, 0..100."""
        delta = series.diff()
        gain = delta.clip(lower=0.0)
        loss = (-delta).clip(lower=0.0)
        avg_gain = gain.ewm(alpha=1.0 / window, adjust=False, min_periods=window).mean()
        avg_loss = loss.ewm(alpha=1.0 / window, adjust=False, min_periods=window).mean()
        rs = avg_gain / avg_loss.replace(0.0, np.nan)
        result = 100.0 - (100.0 / (1.0 + rs))
        # A stretch with no losses at all is a legitimate 100, not a gap.
        return result.where(avg_loss != 0.0, 100.0).where(avg_gain.notna())

    @staticmethod
    def macd(series, fast=12, slow=26, signal=9):
        """Returns (macd line, signal line, histogram)."""
        macd_line = Indicators.ema(series, fast) - Indicators.ema(series, slow)
        signal_line = macd_line.ewm(
            span=signal, adjust=False, min_periods=signal
        ).mean()
        return macd_line, signal_line, macd_line - signal_line

    @staticmethod
    def stochastic(high, low, close, window=14, smooth=3):
        """Returns (%K, %D) -- where price sits in its recent high/low range."""
        lowest = low.rolling(window=window, min_periods=window).min()
        highest = high.rolling(window=window, min_periods=window).max()
        span = (highest - lowest).replace(0.0, np.nan)
        percent_k = 100.0 * (close - lowest) / span
        return percent_k, percent_k.rolling(window=smooth, min_periods=smooth).mean()

    # -- volatility and range ---------------------------------------------

    @staticmethod
    def bollinger(series, window=20, deviations=2.0):
        """Returns (middle, upper, lower, %B) where %B is 0 at the lower band."""
        middle = Indicators.sma(series, window)
        spread = series.rolling(window=window, min_periods=window).std(ddof=0)
        upper = middle + deviations * spread
        lower = middle - deviations * spread
        width = (upper - lower).replace(0.0, np.nan)
        return middle, upper, lower, (series - lower) / width

    @staticmethod
    def true_range(high, low, close):
        previous_close = close.shift(1)
        candidates = pd.concat(
            [
                high - low,
                (high - previous_close).abs(),
                (low - previous_close).abs(),
            ],
            axis=1,
        )
        return candidates.max(axis=1)

    @staticmethod
    def atr(high, low, close, window=14):
        """Average True Range -- typical candle size, in price units."""
        true_range = Indicators.true_range(high, low, close)
        return true_range.ewm(
            alpha=1.0 / window, adjust=False, min_periods=window
        ).mean()

    @staticmethod
    def adx(high, low, close, window=14):
        """Average Directional Index, 0..100 -- how *trending* the tape is."""
        up_move = high.diff()
        down_move = -low.diff()
        plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
        minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)

        smoothing = dict(alpha=1.0 / window, adjust=False, min_periods=window)
        atr = Indicators.true_range(high, low, close).ewm(**smoothing).mean()
        safe_atr = atr.replace(0.0, np.nan)
        plus_di = 100.0 * plus_dm.ewm(**smoothing).mean() / safe_atr
        minus_di = 100.0 * minus_dm.ewm(**smoothing).mean() / safe_atr

        total = (plus_di + minus_di).replace(0.0, np.nan)
        directional_index = 100.0 * (plus_di - minus_di).abs() / total
        return directional_index.ewm(**smoothing).mean(), plus_di, minus_di

    # -- volume ------------------------------------------------------------

    @staticmethod
    def obv(close, volume):
        """On-Balance Volume -- volume signed by the day's direction."""
        direction = np.sign(close.diff().fillna(0.0))
        return (direction * volume.fillna(0.0)).cumsum()

    # -- shape -------------------------------------------------------------

    @staticmethod
    def slope(series, window):
        """Least-squares slope over the last `window` points, per point.

        Expressed as a percent of the mean level so it can be compared across
        tickers of wildly different price.
        """
        trimmed = series.dropna()
        if len(trimmed) < window or window < 2:
            return None
        recent = trimmed.iloc[-window:]
        x = np.arange(len(recent), dtype=float)
        y = recent.to_numpy(dtype=float)
        level = float(np.mean(y))
        if not np.isfinite(level) or level == 0:
            return None
        gradient = float(np.polyfit(x, y, 1)[0])
        return 100.0 * gradient / abs(level)

    @staticmethod
    def zscore(series, window):
        """How many standard deviations the latest point sits from its mean."""
        trimmed = series.dropna()
        if len(trimmed) < window:
            return None
        recent = trimmed.iloc[-window:].to_numpy(dtype=float)
        spread = float(np.std(recent, ddof=0))
        if not np.isfinite(spread) or spread == 0:
            return None
        return (float(recent[-1]) - float(np.mean(recent))) / spread

    @staticmethod
    def drawdown(series):
        """Percent below the running peak, as a negative number."""
        peak = series.cummax()
        return 100.0 * (series - peak) / peak

    @staticmethod
    def range_position(value, low, high):
        """Where `value` sits between low and high, as 0..100."""
        span = float(high) - float(low)
        if not np.isfinite(span) or span <= 0:
            return None
        return 100.0 * (float(value) - float(low)) / span

    # -- one call to rule them all ----------------------------------------

    @staticmethod
    def enrich(frame):
        """Return a copy of an OHLCV frame with every indicator column added.

        Both the technical block and the chart read from this, so what is
        scored and what is drawn can never drift apart.
        """
        data = frame.copy()
        close, high, low = data["Close"], data["High"], data["Low"]
        volume = data["Volume"] if "Volume" in data else pd.Series(
            0.0, index=data.index
        )

        data["SMA20"] = Indicators.sma(close, 20)
        data["SMA50"] = Indicators.sma(close, 50)
        data["SMA200"] = Indicators.sma(close, 200)
        data["EMA12"] = Indicators.ema(close, 12)
        data["RSI"] = Indicators.rsi(close, 14)

        macd_line, signal_line, histogram = Indicators.macd(close)
        data["MACD"] = macd_line
        data["MACD_SIGNAL"] = signal_line
        data["MACD_HIST"] = histogram

        middle, upper, lower, percent_b = Indicators.bollinger(close, 20)
        data["BB_MID"] = middle
        data["BB_UPPER"] = upper
        data["BB_LOWER"] = lower
        data["BB_PCT"] = percent_b

        data["ATR"] = Indicators.atr(high, low, close, 14)
        adx, plus_di, minus_di = Indicators.adx(high, low, close, 14)
        data["ADX"] = adx
        data["DI_PLUS"] = plus_di
        data["DI_MINUS"] = minus_di

        percent_k, percent_d = Indicators.stochastic(high, low, close)
        data["STOCH_K"] = percent_k
        data["STOCH_D"] = percent_d

        data["OBV"] = Indicators.obv(close, volume)
        data["VOL_SMA20"] = Indicators.sma(volume, 20)
        data["DRAWDOWN"] = Indicators.drawdown(close)
        return data
