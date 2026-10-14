"""What the chart is doing: trend, momentum, volatility and participation.

Reads the enriched candle frame produced by Indicators and turns it into a
weighted Score.Block. Every window is counted in *candles*, so the same code
means "50 days" on a 1d horizon and "50 hours" on a 1h horizon -- the horizon
is what decides the timeframe being judged.
"""

from Indicators import Indicators
from Score import Score


class TechnicalAnalysis:
    """Scores the price action of one ticker at one horizon."""

    NAME = "technical"

    # Signal key -> how much it counts within this block.
    WEIGHTS = {
        "trend": 2.5,
        "ma_slope": 1.5,
        "macd": 1.5,
        "rsi": 1.5,
        "momentum": 1.5,
        "bollinger": 1.0,
        "volume": 1.0,
        "adx": 1.0,
        "stochastic": 0.75,
        "drawdown": 1.0,
        "volatility": 0.75,
    }

    def __init__(self, market, settings, frame=None):
        self.market = market
        self.settings = settings
        self.frame = Indicators.enrich(market.history) if frame is None else frame
        self.block = Score.Block(self.NAME, sum(self.WEIGHTS.values()))
        self._analyse()

    # -- helpers -----------------------------------------------------------

    def _latest(self, column, offset=0):
        """The most recent usable value in a column, or None."""
        if column not in self.frame:
            return None
        series = self.frame[column].dropna()
        if len(series) <= offset:
            return None
        return Score.num(series.iloc[-(offset + 1)])

    def _add(self, key, label, score, detail="", value=None):
        self.block.add(key, label, score, self.WEIGHTS[key], detail, value)

    def score(self):
        return self.block.score()

    # -- the signals -------------------------------------------------------

    def _analyse(self):
        if len(self.frame) < 20:
            self.block.note("only %d candles -- too little to read" % len(self.frame))
            return

        close = Score.num(self._latest("Close"))
        if close is None:
            self.block.note("no usable closing price")
            return

        self._trend(close)
        self._ma_slope()
        self._macd()
        self._rsi()
        self._momentum()
        self._bollinger()
        self._volume()
        self._adx()
        self._stochastic()
        self._drawdown()
        self._volatility()

    def _trend(self, close):
        """Price against its 50 and 200 candle averages -- the backbone signal."""
        sma50 = self._latest("SMA50")
        sma200 = self._latest("SMA200")

        if sma50 is None and sma200 is None:
            self.block.note("not enough candles for the 50/200 averages")
            return

        parts, reasons = [], []
        if sma50 is not None:
            gap = 100.0 * (close - sma50) / sma50
            parts.append(Score.ramp(gap, -8.0, 8.0))
            reasons.append("%+.1f%% vs SMA50" % gap)
        if sma200 is not None:
            gap = 100.0 * (close - sma200) / sma200
            parts.append(Score.ramp(gap, -15.0, 15.0))
            reasons.append("%+.1f%% vs SMA200" % gap)

        # The classic cross: 50 over 200 is the golden one, under is the death one.
        if sma50 is not None and sma200 is not None:
            crossed_up = sma50 > sma200
            parts.append(60.0 if crossed_up else -60.0)
            reasons.append("golden cross" if crossed_up else "death cross")

        self._add(
            "trend",
            "Trend vs moving averages",
            sum(parts) / len(parts),
            ", ".join(reasons),
            close,
        )

    def _ma_slope(self):
        """Is the medium-term average itself rising or rolling over?"""
        column = "SMA50" if self.frame["SMA50"].notna().any() else "SMA20"
        slope = Indicators.slope(self.frame[column], 20)
        if slope is None:
            return
        self._add(
            "ma_slope",
            "Moving-average slope",
            Score.ramp(slope, -0.25, 0.25),
            "%s rising %+.3f%% per candle" % (column, slope),
            slope,
        )

    def _macd(self):
        """Histogram sign for direction, plus a bonus for a fresh crossover."""
        histogram = self._latest("MACD_HIST")
        if histogram is None:
            return
        close = self._latest("Close") or 1.0
        # Normalise by price so the number means the same across tickers.
        relative = 100.0 * histogram / abs(close)
        result = Score.ramp(relative, -1.0, 1.0)

        previous = self._latest("MACD_HIST", offset=1)
        detail = "histogram %+.3f (%.2f%% of price)" % (histogram, relative)
        if previous is not None and (previous < 0 <= histogram):
            result = Score.clamp(result + 35.0)
            detail += ", just crossed up"
        elif previous is not None and (previous > 0 >= histogram):
            result = Score.clamp(result - 35.0)
            detail += ", just crossed down"

        self._add("macd", "MACD", result, detail, histogram)

    def _rsi(self):
        """Mean reversion: oversold is an opportunity, overbought is a risk."""
        rsi = self._latest("RSI")
        if rsi is None:
            return
        # 30 -> +100 (oversold, attractive), 70 -> -100 (overbought, stretched).
        result = Score.ramp(rsi, 30.0, 70.0) * -1.0
        if rsi < 30:
            mood = "oversold"
        elif rsi > 70:
            mood = "overbought"
        else:
            mood = "neutral"
        self._add("rsi", "RSI (14)", result, "%.1f -- %s" % (rsi, mood), rsi)

    def _momentum(self):
        """Return over roughly the last quarter, scaled by the ticker's own noise."""
        window = min(self.settings.bars_for_days(90), len(self.frame) - 1)
        if window < 5:
            return
        closes = self.frame["Close"].dropna()
        if len(closes) <= window:
            return
        past = float(closes.iloc[-(window + 1)])
        if past <= 0:
            return
        change = 100.0 * (float(closes.iloc[-1]) - past) / past
        self._add(
            "momentum",
            "Momentum (~90 days)",
            Score.ramp(change, -20.0, 20.0),
            "%+.1f%% over the last %d candles" % (change, window),
            change,
        )

    def _bollinger(self):
        """Position inside the volatility envelope, read as mean reversion."""
        percent_b = self._latest("BB_PCT")
        if percent_b is None:
            return
        # 0 sits on the lower band (cheap), 1 on the upper band (stretched).
        result = Score.ramp(percent_b, 1.0, 0.0)
        self._add(
            "bollinger",
            "Bollinger position",
            result,
            "%%B %.2f (0 = lower band, 1 = upper)" % percent_b,
            percent_b,
        )

    def _volume(self):
        """Is money flowing in behind the move, or is it drifting on no trade?"""
        obv_slope = Indicators.slope(self.frame["OBV"], min(30, len(self.frame)))
        if obv_slope is None:
            return
        result = Score.ramp(obv_slope, -1.5, 1.5)

        latest = self._latest("Volume")
        average = self._latest("VOL_SMA20")
        detail = "OBV trending %+.2f%% per candle" % obv_slope
        if latest and average and average > 0:
            ratio = latest / average
            detail += ", latest volume %.2fx the 20-candle average" % ratio
            # Heavy volume confirms whichever way the tape is already leaning.
            if ratio > 1.5:
                result = Score.clamp(result * 1.25)

        self._add("volume", "Volume flow", result, detail, obv_slope)

    def _adx(self):
        """ADX gives trend *strength*; DI+ vs DI- gives its direction."""
        adx = self._latest("ADX")
        plus_di = self._latest("DI_PLUS")
        minus_di = self._latest("DI_MINUS")
        if adx is None or plus_di is None or minus_di is None:
            return

        direction = 1.0 if plus_di >= minus_di else -1.0
        strength = Score.clamp(Score.ramp(adx, 10.0, 40.0), 0.0, 100.0)
        if adx < 20:
            detail = "ADX %.1f -- no real trend, range-bound" % adx
        else:
            detail = "ADX %.1f -- %s trend" % (
                adx, "up" if direction > 0 else "down",
            )
        self._add("adx", "Trend strength", direction * strength, detail, adx)

    def _stochastic(self):
        percent_k = self._latest("STOCH_K")
        if percent_k is None:
            return
        self._add(
            "stochastic",
            "Stochastic %K",
            Score.ramp(percent_k, 80.0, 20.0),
            "%.1f (below 20 oversold, above 80 overbought)" % percent_k,
            percent_k,
        )

    def _drawdown(self):
        """How far below its own peak the stock is trading."""
        drawdown = self._latest("DRAWDOWN")
        if drawdown is None:
            return
        # A modest dip is a discount; a collapse says something is broken.
        result = Score.band(drawdown, -15.0, -3.0, inside=45.0, outside=-70.0,
                            falloff=2.5)
        self._add(
            "drawdown",
            "Drawdown from peak",
            result,
            "%.1f%% below the highest close on the chart" % drawdown,
            drawdown,
        )

    def _volatility(self):
        """Rising volatility against a ticker's own norm is a mild warning."""
        atr = self._latest("ATR")
        close = self._latest("Close")
        if atr is None or not close:
            return
        relative = 100.0 * atr / close
        typical = self.frame["ATR"].dropna()
        if len(typical) < 30:
            return
        baseline = float((typical / self.frame["Close"]).dropna().mean()) * 100.0
        if baseline <= 0:
            return
        ratio = relative / baseline
        self._add(
            "volatility",
            "Volatility vs its own norm",
            Score.ramp(ratio, 1.8, 0.7),
            "ATR %.2f%% of price, %.2fx this ticker's usual" % (relative, ratio),
            relative,
        )
