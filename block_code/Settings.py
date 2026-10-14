"""Run configuration: which tickers, how wide a candle, how much each factor counts.

Edit TICKERS and HORIZON right here on the canvas. When the generated source is
run from a terminal the same values can be overridden with arguments, e.g.

    python run.py AAPL MSFT NVDA --horizon 1wk --lookback 5y --future 20
"""

import os
import re
import sys


class Settings:
    """One run's configuration, with canvas defaults and command-line overrides."""

    # -- edit me -----------------------------------------------------------
    TICKERS = ["AAPL", "MSFT", "NVDA", "KO", "PFE"]

    # Width of a single candle. "1d" means one candle per trading day.
    HORIZON = "1d"

    # How far back the chart reaches. "" lets the horizon pick for itself.
    LOOKBACK = ""

    # How much each analysis block counts toward the final call. None lets the
    # horizon decide (see HORIZON_WEIGHTS); a dict here overrides it.
    WEIGHTS = None

    OUTPUT_DIR = "output"
    DRAW_CHART = True
    CHART_CANDLES = 180          # how many candles to draw, newest last
    RISK_FREE_RATE = 0.04        # hurdle for the yield-style valuation factors

    BACKTEST = True              # walk-forward check of the technical score

    # FutureHorizon: how many candles of HORIZON the AI model (Chronos-2)
    # forecasts past the last real candle. 0 switches the forecast off.
    FUTURE_HORIZON = 30
    MAX_FUTURE_HORIZON = 512
    COST_BPS = 10.0              # one-way trading cost, basis points
    # ----------------------------------------------------------------------

    # Fundamentals and ownership say next to nothing about tomorrow's price, so
    # short candles are judged almost entirely on the tape. They only earn real
    # weight once the horizon reaches weeks.
    SHORT_TERM_WEIGHTS = {"technical": 0.90, "valuation": 0.10, "supply": 0.00}
    HORIZON_WEIGHTS = {
        "1d":  SHORT_TERM_WEIGHTS,
        "5d":  {"technical": 0.65, "valuation": 0.25, "supply": 0.10},
        "1wk": {"technical": 0.65, "valuation": 0.25, "supply": 0.10},
        "1mo": {"technical": 0.45, "valuation": 0.35, "supply": 0.20},
        "3mo": {"technical": 0.30, "valuation": 0.45, "supply": 0.25},
    }

    # interval -> (default lookback, cap Yahoo allows, bars per year, label)
    HORIZONS = {
        "1m":  ("5d",  "7d",   98280.0, "1 minute"),
        "2m":  ("10d", "60d",  49140.0, "2 minutes"),
        "5m":  ("1mo", "60d",  19656.0, "5 minutes"),
        "15m": ("1mo", "60d",   6552.0, "15 minutes"),
        "30m": ("2mo", "60d",   3276.0, "30 minutes"),
        "60m": ("6mo", "730d",  1638.0, "1 hour"),
        "1h":  ("6mo", "730d",  1638.0, "1 hour"),
        "90m": ("2mo", "60d",   1092.0, "90 minutes"),
        "1d":  ("2y",  "max",    252.0, "1 day"),
        "5d":  ("5y",  "max",     50.0, "5 days"),
        "1wk": ("5y",  "max",     52.0, "1 week"),
        "1mo": ("10y", "max",     12.0, "1 month"),
        "3mo": ("max", "max",      4.0, "1 quarter"),
    }

    INTRADAY = ("1m", "2m", "5m", "15m", "30m", "60m", "1h", "90m")

    # Composite score -> recommendation. Checked top down.
    RATING_BANDS = [
        (45.0, "STRONG BUY"),
        (15.0, "BUY"),
        (-15.0, "HOLD"),
        (-45.0, "SELL"),
    ]
    RATING_ORDER = ["STRONG SELL", "SELL", "HOLD", "BUY", "STRONG BUY"]

    _TICKER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\-=^]{0,14}$")

    def __init__(self, tickers=["AAPL", "MSFT", "NVDA", "KO", "PFE", "HOG", "ORCL", "IBM", "INTC", "AMD","FB2A","AMZN","BA","TSM","MU","SMSN","ASML","GOOGL","MU"], horizon='1d', lookback=None, argv=None, future_horizon=90):
        self.tickers = self._clean(tickers) if tickers else list(self.TICKERS)
        self.horizon = (horizon or self.HORIZON).lower()
        self.lookback = self.LOOKBACK if lookback is None else lookback
        # Resolved against the horizon once the arguments are in, unless
        # WEIGHTS or --weights pins them.
        self.weights = dict(self.WEIGHTS) if self.WEIGHTS else None
        self.output_dir = self.OUTPUT_DIR
        self.draw_chart = self.DRAW_CHART
        self.chart_candles = self.CHART_CANDLES
        self.risk_free_rate = self.RISK_FREE_RATE
        self.backtest = self.BACKTEST
        self.cost_bps = self.COST_BPS
        self.future_horizon = (self.FUTURE_HORIZON if future_horizon is None
                               else int(future_horizon))
        # Arguments that looked like neither a flag nor a ticker, so the run can
        # say so rather than dropping a typo on the floor.
        self.ignored = []

        env_tickers = os.environ.get("STOCKANALYSER_TICKERS", "")
        if env_tickers:
            self.tickers = self._clean(env_tickers.replace(",", " ").split())

        self._apply_argv(sys.argv[1:] if argv is None else argv)
        if self.weights is None:
            self.weights = dict(self.horizon_weights(self.horizon))
        self._validate()

    # -- construction helpers ---------------------------------------------

    @staticmethod
    def _clean(raw):
        """Normalise a ticker list: strip, upper-case, drop blanks and repeats."""
        seen = []
        for item in raw:
            symbol = str(item).strip().upper()
            if symbol and symbol not in seen:
                seen.append(symbol)
        return seen

    def _apply_argv(self, argv):
        """Fold command-line arguments in over the canvas defaults.

        Anything unrecognised is ignored rather than fatal, because CatNip may
        hand the block arguments of its own.
        """
        positional = []
        index = 0
        while index < len(argv):
            token = str(argv[index])
            following = str(argv[index + 1]) if index + 1 < len(argv) else ""

            if token in ("--horizon", "--interval") and following:
                self.horizon = following.lower()
                index += 2
            elif token in ("--lookback", "--period") and following:
                self.lookback = following
                index += 2
            elif token in ("--output", "-o") and following:
                self.output_dir = following
                index += 2
            elif token == "--future" and following.isdigit():
                self.future_horizon = int(following)
                index += 2
            elif token == "--candles" and following.isdigit():
                self.chart_candles = int(following)
                index += 2
            elif token == "--weights" and following:
                self._apply_weights(following)
                index += 2
            elif token == "--no-chart":
                self.draw_chart = False
                index += 1
            elif token == "--no-backtest":
                self.backtest = False
                index += 1
            elif token.startswith("-"):
                index += 1                      # unknown flag: skip it
            else:
                positional.append(token)
                index += 1

        wanted = self._clean([t for t in positional if self._TICKER_RE.match(t)])
        self.ignored = [t for t in positional if not self._TICKER_RE.match(t)]
        if wanted:
            self.tickers = wanted

    def _apply_weights(self, spec):
        """Accept --weights 0.5,0.3,0.2 as technical,valuation,supply."""
        parts = [p for p in str(spec).replace(" ", "").split(",") if p]
        keys = ["technical", "valuation", "supply"]
        if len(parts) != len(keys):
            return
        try:
            values = [float(p) for p in parts]
        except ValueError:
            return
        if sum(values) > 0:
            self.weights = dict(zip(keys, values))

    def _validate(self):
        if not self.tickers:
            raise ValueError("no tickers to analyse -- set Settings.TICKERS")
        if self.horizon not in self.HORIZONS:
            raise ValueError(
                "unknown horizon %r; choose one of: %s"
                % (self.horizon, ", ".join(sorted(self.HORIZONS)))
            )
        if not 0 <= self.future_horizon <= self.MAX_FUTURE_HORIZON:
            raise ValueError("future_horizon must be 0..%d candles, got %r"
                             % (self.MAX_FUTURE_HORIZON, self.future_horizon))
        if sum(self.weights.values()) <= 0:
            raise ValueError("block weights must add up to something positive")

    # -- horizon ----------------------------------------------------------

    @classmethod
    def horizon_weights(cls, horizon):
        """Default block weights for a horizon; intraday reads like 1d."""
        return cls.HORIZON_WEIGHTS.get(horizon, cls.SHORT_TERM_WEIGHTS)

    def spec(self):
        """The (default lookback, cap, bars per year, label) tuple in force."""
        return self.HORIZONS[self.horizon]

    def resolved_lookback(self):
        """The history window to request: explicit if given, else the default."""
        return self.lookback or self.spec()[0]

    def max_lookback(self):
        return self.spec()[1]

    def bars_per_year(self):
        return self.spec()[2]

    def horizon_label(self):
        return self.spec()[3]

    def is_intraday(self):
        return self.horizon in self.INTRADAY

    def bars_for_days(self, days):
        """How many candles of this horizon roughly span `days` calendar days."""
        return max(2, int(round(self.bars_per_year() * days / 365.0)))

    # -- output -----------------------------------------------------------

    def normalised_weights(self):
        total = float(sum(self.weights.values()))
        return dict((k, v / total) for k, v in self.weights.items())

    def ensure_output_dir(self):
        if self.output_dir and not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
        return self.output_dir

    @classmethod
    def rating_for(cls, score):
        """Map a composite score onto STRONG BUY .. STRONG SELL."""
        for threshold, label in cls.RATING_BANDS:
            if score >= threshold:
                return label
        return "STRONG SELL"

    def describe(self):
        weights = self.normalised_weights()
        return (
            "%d ticker(s) | %s candles | lookback %s | "
            "technical %.0f%% / valuation %.0f%% / supply %.0f%% | "
            "forecast %s"
            % (
                len(self.tickers),
                self.horizon_label(),
                self.resolved_lookback(),
                100 * weights["technical"],
                100 * weights["valuation"],
                100 * weights["supply"],
                "%d candles" % self.future_horizon if self.future_horizon
                else "off",
            )
        )

    def settings(self):
        return self
