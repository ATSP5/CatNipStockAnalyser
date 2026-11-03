"""Downloads every candidate of the screen from Yahoo, several at a time."""

from concurrent.futures import ThreadPoolExecutor, as_completed


class UniverseFetcher:
    """Fetches MarketData snapshots in parallel; each ticker is fetched once
    even when it belongs to several themes."""

    def __init__(self, screener_settings, MarketData):
        self.screener_settings = screener_settings
        self.market_data = MarketData          # the MarketData class (block 5)
        self.failures = {}

    def universe_fetcher(self):
        return self

    def fetch_all(self, tickers, progress=None) -> dict:
        """{ticker: MarketData}. A failed download still yields an empty
        snapshot carrying its error, so nothing silently disappears."""
        settings = self.screener_settings.analysis_settings()
        workers = max(1, min(self.screener_settings.fetch_workers, len(tickers) or 1))
        snapshots = {}
        with ThreadPoolExecutor(max_workers=workers) as pool:
            jobs = dict((pool.submit(self._fetch, ticker, settings), ticker)
                        for ticker in tickers)
            for done, job in enumerate(as_completed(jobs), start=1):
                ticker = jobs[job]
                snapshots[ticker] = job.result()
                if progress:
                    progress(done, len(tickers), ticker)
        return snapshots

    def _fetch(self, ticker, settings):
        try:
            return self.market_data.fetch(ticker, settings)
        except Exception as problem:                # noqa: BLE001
            snapshot = self.market_data(ticker, settings)
            snapshot.errors.append("fetch failed: %s" % problem)
            self.failures[ticker] = str(problem)
            return snapshot
