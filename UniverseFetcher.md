Pobiera z Yahoo dane wszystkich kandydatów skanu — równolegle, w puli wątków — używając tego samego `MarketData.fetch` co pierwszy main, więc poprawki danych (waluty, EV, free float) działają tak samo. Osobny blok, bo to warstwa I/O: tylko ona rozmawia z siecią i decyduje o równoległości. Wejścia: `screener_settings` (ScreenerSettings) i `MarketData` (klasa z bloku MarketData); wyjście `universe_fetcher` do ScreenerReport.

## screener_settings
ScreenerSettings: `analysis_settings()` (świece 1d, historia 2y) i `fetch_workers`.

## MarketData
Klasa MarketData (wejście z bloku MarketData), przechowywana jako `market_data`; wywoływane jest `MarketData.fetch(ticker, settings)`.

## failures
`ticker -> komunikat` dla pobrań, które rzuciły wyjątek.

## universe_fetcher
Wyjście bloku: zwraca samą instancję, bo ScreenerReport wywołuje `fetch_all` z listą tickerów i funkcją postępu, których ten blok nie zna.

## fetch_all(tickers, progress=None)
Zwraca `{ticker: MarketData}` dla każdego tickera, także nieudanego (pusty snapshot z błędem — nic nie znika po cichu). `progress(done, total, ticker)` jest wołane po każdym pobraniu. Liczba wątków = `min(fetch_workers, len(tickers))`; więcej wątków = szybciej, ale powyżej ~10 Yahoo zaczyna odrzucać zapytania.
