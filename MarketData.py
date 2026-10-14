"""Everything known about one ticker: candles at the chosen horizon, a daily
series for long-range context, published fundamentals, and the share count
history that the supply block reads.

Two series are always fetched. `history` is drawn at the requested horizon and
drives the chart and the technicals. `daily` is always 1-day candles over two
years, so that a 5-minute run still knows where the 52-week range sits.
"""

import logging
import os
import time

import pandas as pd
import yfinance as yf

# yfinance narrates every 404 straight to the console, which would otherwise
# interleave with the report. Failures are collected per ticker and printed as
# proper "skipped" lines instead. Set STOCKANALYSER_DEBUG to hear it again.
if not os.environ.get("STOCKANALYSER_DEBUG"):
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)


class MarketData:
    """A fetched, validated snapshot of one ticker."""

    OHLCV = ("Open", "High", "Low", "Close", "Volume")

    def __init__(self, ticker, settings):
        self.ticker = str(ticker).strip().upper()
        self.settings = settings
        self.history = pd.DataFrame()
        self.daily = pd.DataFrame()
        self.info = {}
        self.shares_history = None
        self.errors = []

    # -- fetching ----------------------------------------------------------

    @classmethod
    def fetch(cls, ticker, settings, retries=2, pause=1.0):
        """Pull one ticker. Network trouble is recorded, never raised."""
        snapshot = cls(ticker, settings)
        handle = None

        for attempt in range(retries + 1):
            try:
                handle = yf.Ticker(snapshot.ticker)
                snapshot.history = cls._clean(
                    handle.history(
                        period=settings.resolved_lookback(),
                        interval=settings.horizon,
                        auto_adjust=False,
                    )
                )
                if not snapshot.history.empty:
                    break
            except Exception as problem:            # noqa: BLE001 - report, do not crash
                snapshot.errors.append("history: %s" % problem)
            if attempt < retries:
                time.sleep(pause)

        if snapshot.history.empty and not snapshot.errors:
            snapshot.errors.append(
                "no candles returned for %s at %s over %s"
                % (snapshot.ticker, settings.horizon, settings.resolved_lookback())
            )

        if handle is None:
            return snapshot

        # Daily context. Reuse `history` when it is already daily or coarser.
        if settings.horizon in ("1d", "5d", "1wk", "1mo", "3mo"):
            snapshot.daily = snapshot.history
        else:
            try:
                snapshot.daily = cls._clean(
                    handle.history(period="2y", interval="1d", auto_adjust=False)
                )
            except Exception as problem:            # noqa: BLE001
                snapshot.errors.append("daily context: %s" % problem)

        try:
            snapshot.info = handle.get_info() or {}
        except Exception as problem:                # noqa: BLE001
            snapshot.errors.append("fundamentals: %s" % problem)

        # The share count over time is what makes buybacks and dilution visible.
        try:
            shares = handle.get_shares_full(start=None, end=None)
            if shares is not None and len(shares) > 0:
                snapshot.shares_history = shares
        except Exception as problem:                # noqa: BLE001
            snapshot.errors.append("share count history: %s" % problem)

        return snapshot

    @classmethod
    def fetch_many(cls, settings, progress=None):
        """Fetch every ticker in `settings`, in order."""
        results = []
        for position, ticker in enumerate(settings.tickers, start=1):
            if progress:
                progress(position, len(settings.tickers), ticker)
            results.append(cls.fetch(ticker, settings))
        return results

    @staticmethod
    def _clean(frame):
        """Drop empty candles and flatten the column index yfinance may return."""
        if frame is None or len(frame) == 0:
            return pd.DataFrame()
        frame = frame.copy()
        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = frame.columns.get_level_values(0)
        keep = [c for c in MarketData.OHLCV if c in frame.columns]
        frame = frame[keep].dropna(subset=["Close"])
        return frame[~frame.index.duplicated(keep="last")].sort_index()

    # -- state -------------------------------------------------------------

    def ok(self):
        """True when there is enough history to say anything at all."""
        return len(self.history) >= 20

    def bars(self):
        return len(self.history)

    def problem(self):
        """A one-line reason this ticker cannot be analysed, or ''."""
        if self.ok():
            return ""
        if self.errors:
            return self.errors[0]
        return "only %d candle(s) available -- need at least 20" % self.bars()

    # -- convenient reads --------------------------------------------------

    def field(self, *names, **kwargs):
        """First present, numeric value among `names` in the fundamentals blob.

        Yahoo renames these fields without warning, so every call site lists
        the spellings it knows about.
        """
        default = kwargs.get("default")
        for name in names:
            value = self.info.get(name)
            if value is None or isinstance(value, bool):
                continue
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if number == number and abs(number) != float("inf"):
                return number
        return default

    def text(self, *names, **kwargs):
        """First present, non-empty string among `names`."""
        default = kwargs.get("default", "")
        for name in names:
            value = self.info.get(name)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return default

    def last_price(self):
        if self.history.empty:
            return self.field("currentPrice", "regularMarketPrice")
        return float(self.history["Close"].iloc[-1])

    def name(self):
        return self.text("longName", "shortName", default=self.ticker)

    def currency(self):
        return self.text("currency", default="USD")

    def sector(self):
        return self.text("sector", default="n/a")

    def exchange(self):
        return self.text("fullExchangeName", "exchange", default="n/a")

    def shares_outstanding(self):
        """Shares in issue -- the denominator behind every per-share number."""
        return self.field("sharesOutstanding", "impliedSharesOutstanding")

    def free_float(self):
        """Shares actually available to trade, insiders and blocks excluded."""
        return self.field("floatShares")

    def market_cap(self):
        """Published market cap, or price times share count when absent."""
        published = self.field("marketCap")
        if published:
            return published
        price, shares = self.last_price(), self.shares_outstanding()
        if price and shares:
            return price * shares
        return None

    def average_volume(self):
        published = self.field("averageVolume", "averageDailyVolume3Month")
        if published:
            return published
        if not self.daily.empty and "Volume" in self.daily:
            recent = self.daily["Volume"].tail(60).mean()
            return float(recent) if recent == recent else None
        return None

    def year_range(self):
        """(low, high) over the trailing 52 weeks, measured from daily candles."""
        low = self.field("fiftyTwoWeekLow")
        high = self.field("fiftyTwoWeekHigh")
        if low and high and high > low:
            return low, high
        source = self.daily if not self.daily.empty else self.history
        if source.empty:
            return None, None
        window = source.tail(252)
        return float(window["Low"].min()), float(window["High"].max())

    def share_count_change(self):
        """Percent change in shares outstanding over the last year, or None.

        Negative means the company has been buying its own stock back;
        positive means shareholders are being diluted.
        """
        series = self.shares_history
        if series is None or len(series) < 2:
            return None
        try:
            series = series.dropna().sort_index()
            latest_stamp = series.index[-1]
            cutoff = latest_stamp - pd.Timedelta(days=365)
            earlier = series[series.index <= cutoff]
            # Fall back to the oldest reading when history is under a year.
            baseline = float(earlier.iloc[-1]) if len(earlier) else float(series.iloc[0])
            latest = float(series.iloc[-1])
        except Exception:                            # noqa: BLE001
            return None
        if baseline <= 0:
            return None
        return 100.0 * (latest - baseline) / baseline

    def to_dict(self):
        low, high = self.year_range()
        return {
            "ticker": self.ticker,
            "name": self.name(),
            "sector": self.sector(),
            "exchange": self.exchange(),
            "currency": self.currency(),
            "price": self.last_price(),
            "market_cap": self.market_cap(),
            "shares_outstanding": self.shares_outstanding(),
            "free_float": self.free_float(),
            "year_low": low,
            "year_high": high,
            "bars": self.bars(),
            "errors": list(self.errors),
        }

    def marketdata(self):
        return
