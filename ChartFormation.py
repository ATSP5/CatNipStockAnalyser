"""A price formation (channel, triangle, wedge, ...) drawn with two lines."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ChartFormation:
    """Two trend lines fitted through the last swing highs and swing lows.

    The upper line runs through the swing highs, the lower one through the
    swing lows. Both are stored as their prices at the formation's first swing
    (start_bars_ago) and at today's candle, so the chart only draws two
    segments. bars_ago = 0 is the newest candle.

    bias is the signal the formation gives today, like PatternReading.bias for
    candles: a breakout decides it (up = BULL, down = BEAR); inside the lines,
    or past a triangle's apex, it is the formation's own direction.
    """

    INSIDE = "cena w formacji"
    BREAKOUT_UP = "wybicie górą"
    BREAKOUT_DOWN = "wybicie dołem"
    PAST_APEX = "linie przecięte (za wierzchołkiem)"

    name: str                    # Polish name, e.g. "Kanał wzrostowy"
    code: str                    # short label, e.g. "KAN↑"
    direction: str               # "BULL", "BEAR" or "NEUTRAL"
    start_bars_ago: int          # first swing the lines were fitted on
    upper_start: float           # upper line at the start candle
    upper_end: float             # upper line at today's candle
    lower_start: float           # lower line at the start candle
    lower_end: float             # lower line at today's candle
    swings: int                  # swing points the lines were fitted on
    position: str                # where today's close is relative to the lines

    @property
    def bias(self) -> str:
        """Today's signal: "BULL", "BEAR" or "NEUTRAL"."""
        if self.position == self.BREAKOUT_UP:
            return "BULL"
        if self.position == self.BREAKOUT_DOWN:
            return "BEAR"
        return self.direction

    def upper_at(self, bars_ago: int) -> float:
        return self._at(self.upper_start, self.upper_end, bars_ago)

    def lower_at(self, bars_ago: int) -> float:
        return self._at(self.lower_start, self.lower_end, bars_ago)

    def _at(self, start: float, end: float, bars_ago: int) -> float:
        if self.start_bars_ago <= 0:
            return end
        share = (self.start_bars_ago - bars_ago) / self.start_bars_ago
        return start + (end - start) * share

    def summary(self) -> str:
        """One line: signal, name, direction, swings used and today's position."""
        return "%s -- %s (%s, %d swingów, %d świec), %s" % (
            self.bias, self.name, self.direction, self.swings,
            self.start_bars_ago + 1, self.position)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "code": self.code,
            "direction": self.direction,
            "bias": self.bias,
            "start_bars_ago": self.start_bars_ago,
            "upper": [round(self.upper_start, 4), round(self.upper_end, 4)],
            "lower": [round(self.lower_start, 4), round(self.lower_end, 4)],
            "swings": self.swings,
            "position": self.position,
        }
