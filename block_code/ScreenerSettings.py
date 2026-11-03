"""Configuration of the sector screener: which themes, which candidates, how
the 1-6 month outlook is scored.

Each theme is a curated list of US-listed tickers plus, optionally, Yahoo
industries whose largest companies are added to it at run time. Edit THEMES
and FACTOR_WEIGHTS right here on the canvas.
"""

import copy
import os


class ScreenerSettings:
    """One screener run's configuration, built on top of the analyser's Settings."""

    # -- edit me -----------------------------------------------------------
    # theme -> curated tickers (US exchanges, ADRs allowed) and Yahoo
    # industry keywords whose biggest members are added by SectorUniverse.
    THEMES = {
        "AI": {
            "tickers": ["NVDA", "MSFT", "GOOGL", "META", "AMZN", "AVGO", "AMD",
                        "PLTR", "ORCL", "TSM", "MU", "ARM", "ANET", "VRT",
                        "SMCI", "DELL", "MRVL", "NOW", "CRM", "SNOW", "DDOG",
                        "MDB", "CRWV", "AI", "PATH", "SOUN", "IBM"],
            "industries": [],
        },
        "Hi-tech / oprogramowanie": {
            "tickers": ["MSFT", "ORCL", "CRM", "ADBE", "NOW", "INTU", "SAP",
                        "WDAY", "ADSK", "CDNS", "SNPS", "TEAM", "HUBS", "APP",
                        "SHOP", "UBER", "DDOG", "PLTR", "MSTR", "TTD"],
            "industries": ["Software"],
        },
        "Półprzewodniki": {
            "tickers": ["NVDA", "AVGO", "AMD", "TSM", "MU", "QCOM", "TXN",
                        "ADI", "INTC", "MRVL", "NXPI", "MCHP", "ON", "ARM",
                        "ASML", "AMAT", "LRCX", "KLAC", "TER", "ENTG", "MPWR"],
            "industries": ["Semiconductors", "Semiconductor Equipment"],
        },
        "Sprzęt i elektronika": {
            "tickers": ["AAPL", "DELL", "HPQ", "HPE", "CSCO", "ANET", "APH",
                        "GLW", "TEL", "STX", "WDC", "NTAP", "PSTG", "SMCI",
                        "KEYS", "ZBRA", "JBL", "FLEX", "CLS"],
            "industries": ["Computer Hardware", "Communication Equipment",
                           "Electronic Components"],
        },
        "Cyberbezpieczeństwo": {
            "tickers": ["PANW", "CRWD", "FTNT", "ZS", "NET", "OKTA", "S",
                        "CHKP", "CYBR", "QLYS", "TENB", "RPD", "VRNS", "GEN",
                        "AKAM", "FFIV"],
            "industries": [],
        },
        "Internet, media i gry": {
            "tickers": ["GOOGL", "META", "NFLX", "DIS", "SPOT", "RDDT", "PINS",
                        "SNAP", "ROKU", "EA", "TTWO", "RBLX", "WBD", "DASH",
                        "BIDU", "SE"],
            "industries": ["Internet Content", "Entertainment",
                           "Electronic Gaming"],
        },
        "Telekomunikacja": {
            "tickers": ["TMUS", "VZ", "T", "CMCSA", "CHTR", "AMX", "VOD",
                        "LUMN", "FYBR", "IRDM", "ASTS"],
            "industries": ["Telecom"],
        },
        "Farmacja": {
            "tickers": ["LLY", "NVO", "JNJ", "MRK", "ABBV", "PFE", "BMY", "AZN",
                        "GSK", "NVS", "SNY", "AMGN", "GILD", "ZTS", "VTRS",
                        "TEVA", "TAK", "HLN"],
            "industries": ["Drug Manufacturers"],
        },
        "Biotechnologia": {
            "tickers": ["VRTX", "REGN", "AMGN", "GILD", "BIIB", "MRNA", "ALNY",
                        "ARGX", "BMRN", "INCY", "NBIX", "EXEL", "UTHR", "SRPT",
                        "INSM", "IONS", "BNTX", "MDGL"],
            "industries": ["Biotechnology"],
        },
        "Medtech i ochrona zdrowia": {
            "tickers": ["ISRG", "ABT", "TMO", "DHR", "SYK", "BSX", "MDT", "EW",
                        "BDX", "DXCM", "IDXX", "UNH", "ELV", "CI", "HCA",
                        "GEHC", "PODD", "RMD"],
            "industries": ["Medical Devices", "Medical Instruments",
                           "Diagnostics", "Healthcare Plans"],
        },
        "Energia: ropa i gaz": {
            "tickers": ["XOM", "CVX", "COP", "EOG", "OXY", "SLB", "HAL", "BKR",
                        "PSX", "MPC", "VLO", "KMI", "WMB", "OKE", "DVN",
                        "FANG", "EQT", "SHEL", "BP", "TTE"],
            "industries": ["Oil & Gas"],
        },
        "Energia odnawialna": {
            "tickers": ["FSLR", "ENPH", "SEDG", "NEE", "BEP", "AES", "RUN",
                        "ARRY", "NXT", "PLUG", "BE", "CWEN", "ORA", "SHLS",
                        "FLNC", "EOSE", "BEPC"],
            "industries": ["Solar", "Utilities-Renewable"],
        },
        "Energia jądrowa i uran": {
            "tickers": ["CEG", "VST", "CCJ", "OKLO", "SMR", "LEU", "BWXT",
                        "UEC", "NXE", "UUUU", "DNN", "TLN", "GEV", "NNE"],
            "industries": ["Uranium"],
        },
        "Energetyka (utilities)": {
            "tickers": ["NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL",
                        "PCG", "ED", "PEG", "ETR", "WEC", "NRG", "AWK"],
            "industries": ["Utilities-Regulated Electric",
                           "Utilities-Diversified",
                           "Utilities-Independent Power"],
        },
        "Finanse i fintech": {
            "tickers": ["JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW",
                        "AXP", "V", "MA", "PYPL", "COF", "SPGI", "ICE", "CME",
                        "BRK-B", "HOOD", "COIN", "SOFI", "KKR", "BX"],
            "industries": ["Banks", "Capital Markets", "Credit Services",
                           "Financial Data"],
        },
        "Przemysł, lotnictwo i obronność": {
            "tickers": ["GE", "RTX", "LMT", "NOC", "GD", "BA", "HON", "CAT",
                        "DE", "ETN", "UNP", "LHX", "TDG", "HWM", "PH", "EMR",
                        "RKLB", "AXON", "PWR"],
            "industries": ["Aerospace & Defense",
                           "Specialty Industrial Machinery",
                           "Electrical Equipment"],
        },
        "Konsumpcja cykliczna": {
            "tickers": ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW",
                        "BKNG", "TJX", "CMG", "ABNB", "MAR", "LULU", "ORLY",
                        "GM", "F", "RCL", "DECK"],
            "industries": ["Internet Retail", "Restaurants", "Auto Manufacturers",
                           "Specialty Retail"],
        },
        "Konsumpcja podstawowa": {
            "tickers": ["PG", "KO", "PEP", "COST", "WMT", "PM", "MO", "MDLZ",
                        "CL", "KMB", "GIS", "KHC", "KR", "TGT", "EL", "STZ",
                        "KDP", "MNST"],
            "industries": ["Beverages", "Household", "Packaged Foods",
                           "Discount Stores"],
        },
        "Surowce i materiały": {
            "tickers": ["LIN", "APD", "SHW", "ECL", "FCX", "NEM", "NUE", "DOW",
                        "DD", "ALB", "MP", "SCCO", "VMC", "MLM", "CF", "MOS",
                        "AEM", "STLD"],
            "industries": ["Gold", "Copper", "Chemicals", "Steel",
                           "Other Industrial Metals"],
        },
        "Nieruchomości (REIT)": {
            "tickers": ["PLD", "AMT", "EQIX", "CCI", "PSA", "O", "SPG", "WELL",
                        "DLR", "AVB", "EQR", "VICI", "IRM", "EXR", "INVH"],
            "industries": ["REIT"],
        },
    }

    TOP_N = 10                       # picks shown per theme
    MAX_CANDIDATES_PER_THEME = 30    # curated first, then Yahoo's biggest
    SCREEN_SIZE_PER_INDUSTRY = 12    # how many Yahoo adds per industry keyword
    USE_YAHOO_SCREENER = True        # False = curated lists only

    # Filters a candidate must pass to be ranked at all.
    MIN_MARKET_CAP = 2e9             # USD
    MIN_DOLLAR_VOLUME = 20e6         # average daily turnover, USD
    MIN_PRICE = 5.0                  # USD, keeps penny stocks out
    MIN_BARS = 130                   # daily candles, ~6 months
    MIN_COVERAGE = 0.60              # share of factor weight with data
    MIN_ANALYSTS = 3                 # analyst factors need this many opinions

    FETCH_WORKERS = 8                # parallel Yahoo downloads (I/O bound)

    # Chronos-2 forecast over ~6 months of trading days; 0 switches it off.
    FORECAST_STEPS = 126

    # Factor -> weight in the final score. Each factor is turned into a
    # percentile rank inside its theme; weights need not sum to 1.
    FACTOR_WEIGHTS = {
        "momentum_12_1": 0.14,     # return 12 months ago -> 1 month ago
        "momentum_6_1": 0.08,      # return 6 months ago -> 1 month ago
        "high_proximity": 0.08,    # close / 52-week high
        "trend": 0.06,             # close / SMA200 - 1
        "analyst_upside": 0.10,    # mean price target / price - 1
        "analyst_rating": 0.06,    # Yahoo recommendationMean, 1 = strong buy
        "forward_eps_growth": 0.08,  # forward EPS / trailing EPS - 1
        "earnings_growth": 0.06,   # latest quarterly earnings growth y/y
        "revenue_growth": 0.06,    # revenue growth y/y
        "return_on_equity": 0.04,
        "profit_margin": 0.04,
        "fcf_yield": 0.05,         # free cash flow / market cap
        "peg": 0.04,               # P/E to growth, lower is better
        "low_volatility": 0.03,    # 6-month annualised volatility, lower better
        "reversal_1m": 0.03,       # last month's return, lower is better
        "analysis_score": 0.05,    # StockAnalyser composite (Recommendation)
        "forecast": 0.03,          # Chronos-2 median change over FORECAST_STEPS
    }

    FACTOR_LABELS = {
        "momentum_12_1": "momentum 12-1 mies.",
        "momentum_6_1": "momentum 6-1 mies.",
        "high_proximity": "blisko szczytu 52 tyg.",
        "trend": "trend nad SMA200",
        "analyst_upside": "potencjał do ceny docelowej",
        "analyst_rating": "rekomendacje analityków",
        "forward_eps_growth": "oczekiwany wzrost EPS",
        "earnings_growth": "wzrost zysków",
        "revenue_growth": "wzrost przychodów",
        "return_on_equity": "ROE",
        "profit_margin": "marża netto",
        "fcf_yield": "FCF yield",
        "peg": "PEG (wycena do wzrostu)",
        "low_volatility": "niska zmienność",
        "reversal_1m": "brak przegrzania (1 mies.)",
        "analysis_score": "ocena StockAnalyser",
        "forecast": "prognoza Chronos-2",
    }

    # Recommendation weights for a 1-6 month view (Settings' "1mo" blend).
    ANALYSIS_WEIGHTS = {"technical": 0.45, "valuation": 0.35, "supply": 0.20}

    OUTPUT_SUBDIR = "screener"
    DRAW_CHART = True
    # ----------------------------------------------------------------------

    def __init__(self, settings, top_n=TOP_N, use_yahoo_screener=USE_YAHOO_SCREENER,
                 forecast_steps=FORECAST_STEPS, fetch_workers=FETCH_WORKERS,
                 themes=None):
        self.settings = settings
        self.themes = dict(themes or self.THEMES)
        self.top_n = int(top_n)
        self.use_yahoo_screener = bool(use_yahoo_screener)
        self.forecast_steps = int(forecast_steps)
        self.fetch_workers = int(fetch_workers)
        self.max_candidates_per_theme = self.MAX_CANDIDATES_PER_THEME
        self.screen_size_per_industry = self.SCREEN_SIZE_PER_INDUSTRY
        self.min_market_cap = self.MIN_MARKET_CAP
        self.min_dollar_volume = self.MIN_DOLLAR_VOLUME
        self.min_price = self.MIN_PRICE
        self.min_bars = self.MIN_BARS
        self.min_coverage = self.MIN_COVERAGE
        self.min_analysts = self.MIN_ANALYSTS
        self.factor_weights = dict(self.FACTOR_WEIGHTS)
        if self.forecast_steps <= 0:
            self.factor_weights.pop("forecast", None)
        self.draw_chart = self.DRAW_CHART
        self._analysis = None
        self._validate()

    def screener_settings(self):
        return self

    # -- derived -----------------------------------------------------------

    def analysis_settings(self):
        """A copy of the analyser's Settings fit for a 1-6 month screen.

        Daily candles over two years (enough for 12-1 month momentum and
        SMA200), the 1-month block blend, no per-ticker charts or backtests,
        and the forecast horizon set to FORECAST_STEPS.
        """
        if self._analysis is None:
            analysis = copy.copy(self.settings)
            analysis.horizon = "1d"
            analysis.lookback = "2y"
            analysis.weights = dict(self.ANALYSIS_WEIGHTS)
            analysis.future_horizon = max(0, self.forecast_steps)
            analysis.draw_chart = False
            analysis.backtest = False
            analysis.output_dir = self.output_dir()
            self._analysis = analysis
        return self._analysis

    def output_dir(self):
        base = getattr(self.settings, "output_dir", "") or ""
        return os.path.join(base, self.OUTPUT_SUBDIR) if base else self.OUTPUT_SUBDIR

    def ensure_output_dir(self):
        directory = self.output_dir()
        os.makedirs(directory, exist_ok=True)
        return directory

    def label(self, factor):
        return self.FACTOR_LABELS.get(factor, factor)

    def describe(self):
        return ("%d themes | top %d each | Yahoo screener %s | forecast %s | "
                "filters: cap >= %.0fB USD, turnover >= %.0fM USD/day, price >= %.0f"
                % (len(self.themes), self.top_n,
                   "on" if self.use_yahoo_screener else "off",
                   "%d candles" % self.forecast_steps if self.forecast_steps > 0
                   else "off",
                   self.min_market_cap / 1e9, self.min_dollar_volume / 1e6,
                   self.min_price))

    def _validate(self):
        if not self.themes:
            raise ValueError("no themes to screen -- set ScreenerSettings.THEMES")
        if self.top_n < 1:
            raise ValueError("top_n must be at least 1, got %r" % self.top_n)
        if not 0 <= self.forecast_steps <= 512:
            raise ValueError("forecast_steps must be 0..512, got %r"
                             % self.forecast_steps)
        if self.fetch_workers < 1:
            raise ValueError("fetch_workers must be at least 1")
        if sum(w for w in self.factor_weights.values() if w > 0) <= 0:
            raise ValueError("factor weights must add up to something positive")
