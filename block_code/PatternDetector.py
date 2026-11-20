"""Finds candlestick patterns over an automatically sized window back from today.

The window is not a fixed number of candles. A ZigZag with a threshold of
`swing_atr` x ATR splits the price history into swings; the window reaches back
to the start of the last `swings` completed swings (plus a few candles of
lead-in), because a pattern older than that has already played out -- the
swing it pointed to has come and gone. A calm, slowly trending ticker gets a
long window, a choppy one a short window. The result is clamped to
[min_window, max_window] and to the candles the chart shows.

Reversal patterns (hammer, engulfing, stars, ...) count only after a matching
trend (`trend_candles` candles moving at least `trend_atr` ATR). Each pattern
is BULL or BEAR; its strength is a base reliability, raised when the next
candle confirmed it or volume was above average, cut when the next candle went
the other way. The reading weights every pattern by recency and says BULL,
BEAR or NEUTRAL.

The same ZigZag also describes the price structure: its swing points (drawn
on the chart as a black zigzag) and a price formation -- two trend lines fitted
through the last `formation_swings` swing highs and lows, named channel,
rectangle, triangle, wedge or broadening formation from their slopes.
"""

from types import SimpleNamespace

import numpy as np
import pandas as pd

from CandlePattern import CandlePattern
from ChartFormation import ChartFormation
from PatternReading import PatternReading
from SwingPoint import SwingPoint


class PatternDetector:
    """Detects candlestick formations in a verdict's frame."""

    MIN_WINDOW = 15
    MAX_WINDOW = 120
    SWING_ATR = 2.0
    SWINGS = 2
    TREND_CANDLES = 6
    TREND_ATR = 1.0
    BIAS_THRESHOLD = 0.2
    FORMATION_SWINGS = 5
    FLAT_ATR = 1.0

    PIVOT_LEAD = 3            # candles kept before the oldest pivot (lead-in)
    BODY_AVERAGE = 10         # candles in the average body ("long" / "small")
    CONFIRM_BOOST = 1.25
    REFUTE_CUT = 0.5
    VOLUME_BOOST = 1.15

    def __init__(self, settings, min_window=MIN_WINDOW, max_window=MAX_WINDOW,
                 swing_atr=SWING_ATR, swings=SWINGS,
                 trend_candles=TREND_CANDLES, trend_atr=TREND_ATR,
                 bias_threshold=BIAS_THRESHOLD,
                 formation_swings=FORMATION_SWINGS, flat_atr=FLAT_ATR):
        if min_window < 5:
            raise ValueError("min_window must be at least 5 candles")
        if max_window < min_window:
            raise ValueError("max_window must not be smaller than min_window")
        if swing_atr <= 0 or trend_atr <= 0:
            raise ValueError("swing_atr and trend_atr must be positive")
        if swings < 1:
            raise ValueError("swings must be at least 1")
        if trend_candles < 2:
            raise ValueError("trend_candles must be at least 2")
        if not 0.0 <= bias_threshold < 1.0:
            raise ValueError("bias_threshold must be in [0, 1)")
        if formation_swings < 4:
            raise ValueError("formation_swings must be at least 4 (2 highs + 2 lows)")
        if flat_atr <= 0:
            raise ValueError("flat_atr must be positive")
        self.settings = settings
        self.min_window = int(min_window)
        self.max_window = int(max_window)
        self.swing_atr = float(swing_atr)
        self.swings = int(swings)
        self.trend_candles = int(trend_candles)
        self.trend_atr = float(trend_atr)
        self.bias_threshold = float(bias_threshold)
        self.formation_swings = int(formation_swings)
        self.flat_atr = float(flat_atr)

        # name, chart code, direction, candles, base strength, required trend
        # (-1 down, +1 up, 0 none), shape test(d, i) on the newest candle i.
        self.catalogue = [
            ("Morning Star", "MS", "BULL", 3, 0.75, -1, self._morning_star),
            ("Evening Star", "ES", "BEAR", 3, 0.75, +1, self._evening_star),
            ("Bullish Engulfing", "ENG", "BULL", 2, 0.70, -1, self._bull_engulfing),
            ("Bearish Engulfing", "ENG", "BEAR", 2, 0.70, +1, self._bear_engulfing),
            ("Three White Soldiers", "3WS", "BULL", 3, 0.70, 0, self._white_soldiers),
            ("Three Black Crows", "3BC", "BEAR", 3, 0.70, 0, self._black_crows),
            ("Three Inside Up", "3IU", "BULL", 3, 0.65, -1, self._inside_up),
            ("Three Inside Down", "3ID", "BEAR", 3, 0.65, +1, self._inside_down),
            ("Piercing Line", "PL", "BULL", 2, 0.60, -1, self._piercing),
            ("Dark Cloud Cover", "DCC", "BEAR", 2, 0.60, +1, self._dark_cloud),
            ("Hammer", "H", "BULL", 1, 0.60, -1, self._hammer_shape),
            ("Shooting Star", "SS", "BEAR", 1, 0.60, +1, self._inverted_shape),
            ("Inverted Hammer", "IH", "BULL", 1, 0.50, -1, self._inverted_shape),
            ("Hanging Man", "HM", "BEAR", 1, 0.50, +1, self._hammer_shape),
            ("Bullish Harami", "HR", "BULL", 2, 0.45, -1, self._bull_harami),
            ("Bearish Harami", "HR", "BEAR", 2, 0.45, +1, self._bear_harami),
            ("Tweezer Bottom", "TB", "BULL", 2, 0.45, -1, self._tweezer_bottom),
            ("Tweezer Top", "TT", "BEAR", 2, 0.45, +1, self._tweezer_top),
            ("Dragonfly Doji", "DD", "BULL", 1, 0.40, -1, self._dragonfly),
            ("Gravestone Doji", "GD", "BEAR", 1, 0.40, +1, self._gravestone),
            ("Bullish Marubozu", "MB", "BULL", 1, 0.40, 0, self._bull_marubozu),
            ("Bearish Marubozu", "MB", "BEAR", 1, 0.40, 0, self._bear_marubozu),
        ]

    def pattern_detector(self):
        # The whole instance goes downstream: Report calls detect() once per
        # ticker inside its own loop, with a verdict only Report has.
        return self

    # -- public ------------------------------------------------------------

    def detect(self, verdict) -> "PatternReading | None":
        """PatternReading for the verdict's candles, or None without enough data."""
        frame = getattr(verdict, "frame", None)
        if frame is None or len(frame) < self.trend_candles + 4:
            return None
        d = self._arrays(frame)
        pivots, pending = self._zigzag(d.high, d.low, d.atr)
        formation = self._formation(d, pivots)
        window, reason = self.choose_window(d, pivots, formation)
        found = self._scan(d, window)
        return self._read(self._deduplicate(found), window, reason,
                          self._swing_points(d, pivots, pending), formation)

    def choose_window(self, d, pivots, formation=None) -> "tuple[int, str]":
        """How many candles back from today to search, and why.

        With a price formation the window is at least as long as the formation,
        so every candle pattern inside it is read -- even above max_window,
        but never past the charted candles or the available history.
        """
        count = len(d.close)
        upper = min(self.max_window, self._chart_candles(),
                    count - self.trend_candles - 1)
        if len(pivots) >= self.swings:
            start = max(0, pivots[-self.swings][0] - self.PIVOT_LEAD)
            window = count - start
            reason = "ostatnie swingi: %d (ZigZag %.1f×ATR)" % (
                self.swings, self.swing_atr)
        else:
            window = upper
            reason = "brak wyraźnych swingów -- okno maksymalne"
        if window < self.min_window:
            window = self.min_window
            reason += ", podniesione do minimum %d" % self.min_window
        if window > upper:
            window = upper
            reason += ", przycięte do %d" % upper
        if formation is not None:
            span = min(formation.start_bars_ago + 1, self._chart_candles(),
                       count - self.trend_candles - 1)
            if span > window:
                window = span
                reason += ", wydłużone do formacji cenowej (%d)" % span
        return max(1, window), reason

    # -- data --------------------------------------------------------------

    def _arrays(self, frame):
        o = frame["Open"].to_numpy(dtype=float)
        h = frame["High"].to_numpy(dtype=float)
        l = frame["Low"].to_numpy(dtype=float)
        c = frame["Close"].to_numpy(dtype=float)
        if "ATR" in frame and frame["ATR"].notna().any():
            atr = frame["ATR"].astype(float)
        else:
            previous = pd.Series(c).shift(1)
            true_range = pd.concat([pd.Series(h - l),
                                    (pd.Series(h) - previous).abs(),
                                    (pd.Series(l) - previous).abs()], axis=1).max(axis=1)
            atr = true_range.rolling(14, min_periods=1).mean()
        atr = pd.Series(np.asarray(atr, dtype=float)).bfill().ffill()
        fallback = float(np.nanmean(h - l)) or 1e-9
        atr = atr.fillna(fallback).clip(lower=1e-9).to_numpy()

        body = np.abs(c - o)
        average = (pd.Series(body).rolling(self.BODY_AVERAGE, min_periods=1)
                   .mean().shift(1).bfill().to_numpy())
        volume = frame["Volume"].to_numpy(dtype=float) if "Volume" in frame else None
        if "VOL_SMA20" in frame:
            volume_average = frame["VOL_SMA20"].to_numpy(dtype=float)
        elif volume is not None:
            volume_average = pd.Series(volume).rolling(20, min_periods=1).mean().to_numpy()
        else:
            volume_average = None
        return SimpleNamespace(
            open=o, high=h, low=l, close=c, atr=atr, body=body,
            range=h - l, upper=h - np.maximum(o, c), lower=np.minimum(o, c) - l,
            average_body=np.maximum(average, 1e-9), volume=volume,
            volume_average=volume_average, index=list(frame.index),
        )

    def _chart_candles(self) -> int:
        """Candles the chart shows -- swings and formations older are not drawn."""
        return max(20, int(getattr(self.settings, "chart_candles", self.max_window)))

    def _zigzag(self, high, low, atr):
        """Confirmed swings as (position, "HIGH"/"LOW"), oldest first, plus the
        extreme the price is still moving into (or None)."""
        pivots, direction, top, bottom = [], 0, 0, 0
        for i in range(1, len(high)):
            threshold = self.swing_atr * atr[i]
            if direction == 0:
                if high[i] > high[top]:
                    top = i
                if low[i] < low[bottom]:
                    bottom = i
                if high[top] - low[bottom] >= threshold:
                    if top > bottom:
                        pivots.append((bottom, "LOW"))
                        direction = 1
                    else:
                        pivots.append((top, "HIGH"))
                        direction = -1
            elif direction == 1:
                if high[i] >= high[top]:
                    top = i
                elif high[top] - low[i] >= threshold:
                    pivots.append((top, "HIGH"))
                    direction, bottom = -1, i
            else:
                if low[i] <= low[bottom]:
                    bottom = i
                elif high[i] - low[bottom] >= threshold:
                    pivots.append((bottom, "LOW"))
                    direction, top = 1, i
        pending = {1: (top, "HIGH"), -1: (bottom, "LOW")}.get(direction)
        return pivots, pending

    # -- price structure ---------------------------------------------------

    def _swing_points(self, d, pivots, pending):
        """ZigZag points inside the charted candles; the open extreme last."""
        count = len(d.close)
        points = [self._swing(d, position, kind, True) for position, kind in pivots]
        if pending is not None and (not pivots or pending[0] > pivots[-1][0]):
            points.append(self._swing(d, pending[0], pending[1], False))
        visible = self._chart_candles()
        return [point for point in points if point.bars_ago < visible]

    @staticmethod
    def _swing(d, position, kind, confirmed):
        price = d.high[position] if kind == "HIGH" else d.low[position]
        return SwingPoint(bars_ago=len(d.close) - 1 - position, price=float(price),
                          kind=kind, confirmed=confirmed)

    def _formation(self, d, pivots):
        """Trend lines through the last swing highs and lows, or None."""
        count = len(d.close)
        visible = self._chart_candles()
        recent = [(p, k) for p, k in pivots if count - 1 - p < visible]
        recent = recent[-self.formation_swings:]
        highs = [p for p, k in recent if k == "HIGH"]
        lows = [p for p, k in recent if k == "LOW"]
        if len(highs) < 2 or len(lows) < 2:
            return None
        start, end = recent[0][0], count - 1
        upper = np.polyfit(highs, d.high[highs], 1)
        lower = np.polyfit(lows, d.low[lows], 1)
        length = max(1, end - start)
        atr = float(d.atr[end])
        name, code, direction = self._classify(upper[0] * length / atr,
                                               lower[0] * length / atr)
        upper_end = float(np.polyval(upper, end))
        lower_end = float(np.polyval(lower, end))
        return ChartFormation(
            name=name, code=code, direction=direction,
            start_bars_ago=end - start,
            upper_start=float(np.polyval(upper, start)), upper_end=upper_end,
            lower_start=float(np.polyval(lower, start)), lower_end=lower_end,
            swings=len(recent),
            position=self._position(float(d.close[end]), upper_end, lower_end),
        )

    def _classify(self, upper_move, lower_move):
        """Name, code and direction from both lines' moves (in ATR) over the formation."""
        flat = self.flat_atr

        def trend(move):
            return 0 if abs(move) < flat else (1 if move > 0 else -1)

        top, bottom = trend(upper_move), trend(lower_move)
        spread = upper_move - lower_move        # > 0 widening, < 0 narrowing
        if abs(spread) < flat:
            middle = trend((upper_move + lower_move) / 2.0)
            if middle == 0:
                return "Prostokąt (konsolidacja)", "PROST", "NEUTRAL"
            if middle > 0:
                return "Kanał wzrostowy", "KAN↑", "BULL"
            return "Kanał spadkowy", "KAN↓", "BEAR"
        if spread < 0:
            if top == 0 and bottom > 0:
                return "Trójkąt zwyżkujący", "TR↑", "BULL"
            if top < 0 and bottom == 0:
                return "Trójkąt zniżkujący", "TR↓", "BEAR"
            if top > 0 and bottom > 0:
                return "Klin zwyżkujący", "KL↑", "BEAR"
            if top < 0 and bottom < 0:
                return "Klin zniżkujący", "KL↓", "BULL"
            return "Trójkąt symetryczny", "TR=", "NEUTRAL"
        if top > 0 and bottom > 0:
            return "Kanał wzrostowy", "KAN↑", "BULL"
        if top < 0 and bottom < 0:
            return "Kanał spadkowy", "KAN↓", "BEAR"
        return "Formacja rozszerzająca się", "ROZSZ", "NEUTRAL"

    @staticmethod
    def _position(close, upper, lower):
        if upper < lower:
            return ChartFormation.PAST_APEX
        if close > upper:
            return ChartFormation.BREAKOUT_UP
        if close < lower:
            return ChartFormation.BREAKOUT_DOWN
        return ChartFormation.INSIDE

    # -- scanning ----------------------------------------------------------

    def _scan(self, d, window):
        count = len(d.close)
        first = count - window
        found = []
        for i in range(first, count):
            for name, code, direction, length, base, trend, test in self.catalogue:
                start = i - length + 1
                if start < first or start - 1 - self.trend_candles < 0:
                    continue
                if trend and self._trend(d, start - 1) != trend:
                    continue
                if test(d, i):
                    found.append(self._pattern(d, i, name, code, direction,
                                               length, base))
        return found

    def _trend(self, d, s):
        """-1, 0 or +1: how the close moved over trend_candles up to candle s."""
        move = (d.close[s] - d.close[s - self.trend_candles]) / d.atr[s]
        if move >= self.trend_atr:
            return 1
        if move <= -self.trend_atr:
            return -1
        return 0

    def _pattern(self, d, i, name, code, direction, length, base):
        count = len(d.close)
        strength = base
        confirmed = None
        if i + 1 < count:
            moved = d.close[i + 1] - d.close[i]
            confirmed = moved > 0 if direction == "BULL" else moved < 0
            strength *= self.CONFIRM_BOOST if confirmed else self.REFUTE_CUT
        if (d.volume is not None and d.volume_average is not None
                and np.isfinite(d.volume_average[i])
                and d.volume[i] > d.volume_average[i]):
            strength *= self.VOLUME_BOOST
        span = slice(i - length + 1, i + 1)
        return CandlePattern(
            name=name, code=code, direction=direction, length=length,
            bars_ago=count - 1 - i, timestamp=d.index[i],
            low=float(np.min(d.low[span])), high=float(np.max(d.high[span])),
            strength=float(min(1.0, strength)), confirmed=confirmed,
        )

    @staticmethod
    def _deduplicate(found):
        """Keep the strongest pattern where same-direction ones share candles."""
        kept = []
        for pattern in sorted(found, key=lambda p: p.strength, reverse=True):
            first, last = pattern.bars_ago, pattern.bars_ago + pattern.length - 1
            if any(other.direction == pattern.direction
                   and other.bars_ago <= last
                   and first <= other.bars_ago + other.length - 1
                   for other in kept):
                continue
            kept.append(pattern)
        return sorted(kept, key=lambda p: p.bars_ago)

    def _read(self, patterns, window, reason, swings, formation):
        half_life = max(3.0, window / 4.0)
        bull = sum(p.strength * 0.5 ** (p.bars_ago / half_life)
                   for p in patterns if p.bullish)
        bear = sum(p.strength * 0.5 ** (p.bars_ago / half_life)
                   for p in patterns if not p.bullish)
        if not patterns:
            bias = "NONE"
        else:
            net = (bull - bear) / (bull + bear)
            if net > self.bias_threshold:
                bias = "BULL"
            elif net < -self.bias_threshold:
                bias = "BEAR"
            else:
                bias = "NEUTRAL"
        return PatternReading(window=window, window_reason=reason,
                              patterns=patterns, bull_score=bull,
                              bear_score=bear, bias=bias, swings=swings,
                              formation=formation)

    # -- candle shapes -----------------------------------------------------

    @staticmethod
    def _bull(d, i):
        return d.close[i] > d.open[i]

    @staticmethod
    def _bear(d, i):
        return d.close[i] < d.open[i]

    @staticmethod
    def _long(d, i):
        return d.body[i] >= d.average_body[i]

    @staticmethod
    def _small(d, i):
        return d.body[i] <= 0.5 * d.average_body[i]

    @staticmethod
    def _visible(d, i):
        """Range big enough to be a formation rather than noise."""
        return d.range[i] >= 0.5 * d.atr[i]

    @staticmethod
    def _middle(d, i):
        return (d.open[i] + d.close[i]) / 2.0

    def _hammer_shape(self, d, i):
        return (self._visible(d, i) and d.body[i] > 0.1 * d.range[i]
                and d.lower[i] >= 2.0 * d.body[i] and d.upper[i] <= 0.15 * d.range[i])

    def _inverted_shape(self, d, i):
        return (self._visible(d, i) and d.body[i] > 0.1 * d.range[i]
                and d.upper[i] >= 2.0 * d.body[i] and d.lower[i] <= 0.15 * d.range[i])

    def _dragonfly(self, d, i):
        return (self._visible(d, i) and d.body[i] <= 0.1 * d.range[i]
                and d.lower[i] >= 0.7 * d.range[i])

    def _gravestone(self, d, i):
        return (self._visible(d, i) and d.body[i] <= 0.1 * d.range[i]
                and d.upper[i] >= 0.7 * d.range[i])

    def _marubozu(self, d, i):
        return (d.body[i] >= 0.9 * d.range[i]
                and d.body[i] >= 1.5 * d.average_body[i])

    def _bull_marubozu(self, d, i):
        return self._bull(d, i) and self._marubozu(d, i)

    def _bear_marubozu(self, d, i):
        return self._bear(d, i) and self._marubozu(d, i)

    def _bull_engulfing(self, d, i):
        p = i - 1
        return (self._bear(d, p) and self._bull(d, i)
                and d.body[p] >= 0.3 * d.average_body[p]
                and d.close[i] >= d.open[p] and d.open[i] <= d.close[p]
                and d.body[i] > d.body[p])

    def _bear_engulfing(self, d, i):
        p = i - 1
        return (self._bull(d, p) and self._bear(d, i)
                and d.body[p] >= 0.3 * d.average_body[p]
                and d.close[i] <= d.open[p] and d.open[i] >= d.close[p]
                and d.body[i] > d.body[p])

    def _piercing(self, d, i):
        p = i - 1
        return (self._bear(d, p) and self._long(d, p) and self._bull(d, i)
                and d.open[i] <= d.close[p]
                and self._middle(d, p) < d.close[i] < d.open[p])

    def _dark_cloud(self, d, i):
        p = i - 1
        return (self._bull(d, p) and self._long(d, p) and self._bear(d, i)
                and d.open[i] >= d.close[p]
                and d.open[p] < d.close[i] < self._middle(d, p))

    def _bull_harami(self, d, i):
        p = i - 1
        return (self._bear(d, p) and self._long(d, p) and d.close[i] >= d.open[i]
                and d.body[i] <= 0.5 * d.body[p]
                and max(d.open[i], d.close[i]) <= d.open[p]
                and min(d.open[i], d.close[i]) >= d.close[p])

    def _bear_harami(self, d, i):
        p = i - 1
        return (self._bull(d, p) and self._long(d, p) and d.close[i] <= d.open[i]
                and d.body[i] <= 0.5 * d.body[p]
                and max(d.open[i], d.close[i]) <= d.close[p]
                and min(d.open[i], d.close[i]) >= d.open[p])

    def _tweezer_bottom(self, d, i):
        p = i - 1
        return (self._bear(d, p) and self._bull(d, i)
                and abs(d.low[i] - d.low[p]) <= 0.1 * d.atr[i])

    def _tweezer_top(self, d, i):
        p = i - 1
        return (self._bull(d, p) and self._bear(d, i)
                and abs(d.high[i] - d.high[p]) <= 0.1 * d.atr[i])

    def _morning_star(self, d, i):
        a, b = i - 2, i - 1
        return (self._bear(d, a) and self._long(d, a) and self._small(d, b)
                and self._middle(d, b) <= d.close[a] and self._bull(d, i)
                and d.close[i] >= self._middle(d, a))

    def _evening_star(self, d, i):
        a, b = i - 2, i - 1
        return (self._bull(d, a) and self._long(d, a) and self._small(d, b)
                and self._middle(d, b) >= d.close[a] and self._bear(d, i)
                and d.close[i] <= self._middle(d, a))

    def _soldier(self, d, previous, i):
        return (self._bull(d, i) and d.close[i] > d.close[previous]
                and d.open[previous] <= d.open[i] <= d.close[previous]
                and d.body[i] >= 0.6 * d.average_body[i]
                and d.upper[i] <= 0.3 * d.body[i])

    def _crow(self, d, previous, i):
        return (self._bear(d, i) and d.close[i] < d.close[previous]
                and d.close[previous] <= d.open[i] <= d.open[previous]
                and d.body[i] >= 0.6 * d.average_body[i]
                and d.lower[i] <= 0.3 * d.body[i])

    def _white_soldiers(self, d, i):
        a, b = i - 2, i - 1
        return (self._bull(d, a) and d.body[a] >= 0.6 * d.average_body[a]
                and self._soldier(d, a, b) and self._soldier(d, b, i))

    def _black_crows(self, d, i):
        a, b = i - 2, i - 1
        return (self._bear(d, a) and d.body[a] >= 0.6 * d.average_body[a]
                and self._crow(d, a, b) and self._crow(d, b, i))

    def _inside_up(self, d, i):
        return (self._bull_harami(d, i - 1) and self._bull(d, i)
                and d.close[i] > d.open[i - 2])

    def _inside_down(self, d, i):
        return (self._bear_harami(d, i - 1) and self._bear(d, i)
                and d.close[i] < d.open[i - 2])
