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
        # Statement currency -> quote currency, 1.0 when they are the same.
        self.fx = 1.0
        # Yahoo figures that were wrong but could be recomputed ...
        self.data_fixes = []
        # ... and the ones that could not, and were left out of the scoring.
        self.data_warnings = []

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

        # Foreign filers (ASML reports in EUR, TSMC in TWD) are quoted in USD;
        # the statement figures need converting before they meet the price.
        if snapshot.needs_fx():
            snapshot.fx = cls._fetch_fx(snapshot.statement_currency(),
                                        snapshot.currency())

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
    def _fetch_fx(source, target):
        """Units of `target` per one unit of `source`, or None if unavailable."""
        try:
            quotes = yf.Ticker("%s%s=X" % (source, target)).history(period="5d")
            rate = float(quotes["Close"].dropna().iloc[-1])
        except Exception:                            # noqa: BLE001
            return None
        return rate if rate > 0 else None

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
        """Shares actually available to trade, or None when Yahoo's is impossible.

        A float larger than the share count cannot be true (ASML: 21.28B
        floating out of 385M) and there is no second source to repair it from.
        """
        published = self.field("floatShares")
        shares = self.shares_outstanding()
        if published and shares and published > shares * self.FLOAT_TOLERANCE:
            self._warn(
                "Free float: Yahoo podaje %s akcji w wolnym obrocie przy %s akcji "
                "wyemitowanych (%.0f%%) -- to niemożliwe, a innego źródła nie ma; "
                "pominięty w ocenie (free float, obrót)"
                % (self._count(published), self._count(shares),
                   100.0 * published / shares))
            return None
        return published

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

    # -- fundamentals, checked ---------------------------------------------
    #
    # Yahoo divides a USD market cap by EUR or TWD statement figures without
    # converting them, and builds enterprise value from a broken float count.
    # Each ratio below is recomputed from its parts in the quote currency;
    # what cannot be recomputed, or is still beyond any plausible value, is
    # left out of the scoring and reported in data_warnings.

    FLOAT_TOLERANCE = 1.05                 # float may exceed shares by rounding
    SANE_LIMITS = {"P/B": 200.0, "P/S": 200.0, "EV/EBITDA": 500.0}
    SANE_FCF_YIELD = 50.0                  # percent, either sign
    MINOR_UNITS = {"GBP": "GBP", "ZAC": "ZAR", "ILA": "ILS"}   # GBp, ZAc, ILA

    def statement_currency(self):
        """Currency of the financial statements (EUR for ASML), or ''."""
        return self.text("financialCurrency", default="")

    @classmethod
    def _major(cls, code):
        code = str(code).upper()
        return cls.MINOR_UNITS.get(code, code)

    def needs_fx(self):
        """True when the statements are in another currency than the quote."""
        source = self.statement_currency()
        return bool(source) and self._major(source) != self._major(self.currency())

    def fx_label(self):
        return "%s->%s %.4f" % (self.statement_currency(), self.currency(),
                                self.fx or 0.0)

    def statement_value(self, *names):
        """A statement figure converted to the quote currency, or None."""
        value = self.field(*names)
        if value is None or self.fx is None:
            return None
        return value * self.fx

    def price_to_sales(self):
        cap = self.market_cap()
        revenue = self.statement_value("totalRevenue")
        computed = cap / revenue if cap and revenue and revenue > 0 else None
        return self._checked(
            "P/S", computed,
            self.field("priceToSalesTrailing12Months", "priceToSales"),
            "kapitalizacja / przychody" + self._fx_note("przychody"))

    def enterprise_to_ebitda(self):
        cap = self.market_cap()
        ebitda = self.statement_value("ebitda")
        computed = None
        if cap and ebitda:
            debt = self.statement_value("totalDebt") or 0.0
            cash = self.statement_value("totalCash") or 0.0
            computed = (cap + debt - cash) / ebitda
        return self._checked(
            "EV/EBITDA", computed, self.field("enterpriseToEbitda"),
            "EV = kapitalizacja + dług - gotówka (Yahoo liczy EV z błędnej "
            "liczby akcji w wolnym obrocie)" + self._fx_note("dług, gotówka, EBITDA"))

    def price_to_book(self):
        """Yahoo's P/B, or for a foreign filer one rebuilt from debt / (D/E).

        Yahoo's bookValue per share is unusable for ADRs (ASML: 1.16), but
        totalDebt and debtToEquity are consistent, and their ratio is equity.
        """
        computed = None
        if self.needs_fx():
            cap = self.market_cap()
            debt = self.statement_value("totalDebt")
            ratio = self.field("debtToEquity")
            if cap and debt and ratio and ratio > 0:
                computed = cap / (debt / (ratio / 100.0))
        return self._checked(
            "P/B", computed, self.field("priceToBook"),
            "kapitał własny = dług / (dług/kapitał)" + self._fx_note("dług"))

    def free_cash_flow_yield(self):
        """Free cash flow over market cap, percent, or None."""
        cap = self.market_cap()
        cash_flow = self.statement_value("freeCashflow")
        if self.field("freeCashflow") is None or not cap or cap <= 0:
            return None
        if cash_flow is None:
            self._no_fx("FCF yield")
            return None
        value = 100.0 * cash_flow / cap
        if abs(value) > self.SANE_FCF_YIELD:
            self._warn("FCF yield %.1f%% poza wiarygodnym zakresem (±%.0f%%) -- "
                       "pominięty w ocenie" % (value, self.SANE_FCF_YIELD))
            return None
        if self.needs_fx():
            self._fix("FCF yield: wolne przepływy w %s przeliczone na %s "
                      "(kurs %s): %.2f%%" % (self.statement_currency(),
                                             self.currency(), self.fx_label(), value))
        return value

    def _checked(self, label, computed, published, how):
        """Prefer the recomputed ratio; fall back to Yahoo's only when the
        currencies agree; drop anything beyond SANE_LIMITS."""
        if computed is None and self.needs_fx():
            if published is not None:
                self._no_fx(label)
            return None
        value = published if computed is None else computed
        if computed is not None and published is not None and computed > 0 \
                and abs(published / computed - 1.0) > 0.10:
            self._fix("%s: Yahoo podaje %.2f, przeliczono %.2f (%s)"
                      % (label, published, computed, how))
        if value is not None and value > self.SANE_LIMITS[label]:
            self._warn("%s %.1f poza wiarygodnym zakresem (> %.0f) -- pominięty "
                       "w ocenie" % (label, value, self.SANE_LIMITS[label]))
            return None
        return value

    def _fx_note(self, what):
        if not self.needs_fx():
            return ""
        return "; %s w %s przeliczone kursem %s" % (
            what, self.statement_currency(), self.fx_label())

    def _no_fx(self, label):
        self._warn("%s pominięty: sprawozdania są w %s, notowania w %s, a kursu "
                   "lub składników do przeliczenia brak -- wartość Yahoo miesza "
                   "waluty" % (label, self.statement_currency(), self.currency()))

    def _fix(self, text):
        if text not in self.data_fixes:
            self.data_fixes.append(text)

    def _warn(self, text):
        if text not in self.data_warnings:
            self.data_warnings.append(text)

    @staticmethod
    def _count(value):
        """Compact share count for messages: 21.28B, 385.42M."""
        for cutoff, unit in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
            if abs(value) >= cutoff:
                return "%.2f%s" % (value / cutoff, unit)
        return "%.0f" % value

    def has_suspect_data(self):
        """True when some Yahoo figure was impossible and had to be dropped."""
        return bool(self.data_warnings)

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
            "statement_currency": self.statement_currency(),
            "fx": self.fx,
            "data_fixes": list(self.data_fixes),
            "data_warnings": list(self.data_warnings),
        }
