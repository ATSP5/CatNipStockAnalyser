Everything known about one ticker, fetched from Yahoo through yfinance: candles at the chosen horizon, published fundamentals, and the share count history that the supply block reads.

Two price series are always fetched. `history` uses the requested horizon and drives the chart and the technicals. `daily` is always two years of 1-day candles, so that a 5-minute run still knows where the 52-week range sits and how far price has drifted from its 200-day average. Without that second series, an intraday horizon would have no long-range context to value against.

Network failure is recorded, never raised. A ticker that cannot be fetched is collected in `errors`; the report shows it as an empty NO DATA analysis with that reason, and the rest of the run continues.

## fetch

Pulls one ticker and returns a populated `MarketData`. Retries the history request before giving up, since Yahoo intermittently returns an empty frame for a perfectly valid symbol.

## fetch_many

Fetches every ticker in the settings, in order, optionally calling a `progress` callback with `(position, total, ticker)`.

## ok

True when at least 20 candles arrived — the minimum for any indicator to mean anything. A ticker that fails this gets an empty NO DATA verdict (see Recommendation) instead of being hidden.

## problem

A one-line explanation of why this ticker cannot be analysed, or `""` when it can.

## field

Returns the first present, numeric value among the names given. Yahoo renames fields without warning and omits them freely, so every call site lists the spellings it knows about: `field("pegRatio", "trailingPegRatio")`. Anything missing, `None`, boolean or non-numeric is skipped.

## text

The string equivalent of `field`.

## shares_outstanding

Shares in issue — the denominator behind every per-share figure, and the starting point of the supply analysis.

## free_float

Shares actually available to trade, with insider and strategic holdings excluded. Usually smaller than `shares_outstanding`, sometimes far smaller.

Zwraca `None`, gdy Yahoo podaje więcej akcji w wolnym obrocie niż akcji wyemitowanych (powyżej `FLOAT_TOLERANCE` = 1,05×), np. ASML: 21,28 mld przy 385 mln (5520%). Takiej liczby nie da się naprawić, bo nie ma drugiego źródła. Trafia więc do `data_warnings`, a SupplyAnalysis pomija sygnał free float, a obrót liczy względem `shares_outstanding`.

## Kontrola danych fundamentalnych — po co

Yahoo dzieli kapitalizację w walucie notowań (USD) przez dane ze sprawozdań w walucie spółki (ASML: EUR, TSMC: TWD) bez przeliczenia. Do tego liczy EV z błędnej liczby akcji w wolnym obrocie. Dla ASML dawało to P/B 1415×, EV/EBITDA 2166× i P/S 16,1. Te metody przeliczają wskaźniki z ich składników w walucie notowań. Czego nie da się przeliczyć albo co dalej jest nieprawdopodobne, nie jest oceniane i trafia do `data_warnings`. Taki ticker dostaje w raporcie i na wykresie znak „! Możliwe błędne dane”. Odpowiedzialność jest tutaj, bo MarketData i tak tłumaczy osobliwości Yahoo (`field`), a ValuationAnalysis dostaje gotowe, sprawdzone liczby.

## fx

Kurs: ile jednostek waluty notowań za 1 jednostkę waluty sprawozdań. Pobierany w `fetch` z pary Yahoo `<sprawozdania><notowania>=X` (np. `EURUSD=X`) tylko wtedy, gdy `needs_fx()`. Gdy waluty są te same, wynosi 1,0. Gdy kursu nie da się pobrać, jest `None`: wskaźniki ze sprawozdań są wtedy pomijane z ostrzeżeniem, zamiast używać wartości Yahoo mieszających waluty.

## data_fixes

Lista komunikatów (po polsku) o wartościach Yahoo, które były błędne, ale zostały przeliczone, np. `P/B: Yahoo podaje 1415.48, przeliczono 24.80 (…)`. Wpis powstaje, gdy wartość przeliczona różni się od Yahoo o ponad 10%. Report drukuje je w karcie tickera jako „Dane poprawione”. Trafiają też do JSON (`market.data_fixes`) i CSV (`data_fixes`). Nie wpływają na znak „!”.

## data_warnings

Lista komunikatów o wartościach, których nie dało się naprawić i które **pominięto w ocenie**. Niepusta lista daje znak „!” w tabeli, czerwony napis „! Możliwe błędne dane” na wykresie i sekcję „! Możliwe błędne dane” w karcie. Trafiają też do JSON i CSV.

## has_suspect_data

`True`, gdy `data_warnings` nie jest puste.

## statement_currency

Waluta sprawozdań (`financialCurrency` z Yahoo) albo `""`.

## needs_fx

`True`, gdy waluta sprawozdań różni się od waluty notowań. Jednostki drobne (`GBp`, `ZAc`, `ILA`) są porównywane jako ich waluta główna (`MINOR_UNITS`), więc spółki z Londynu nie są przeliczane, czyli zachowują się jak wcześniej.

## statement_value

Pole ze sprawozdań (np. `totalRevenue`) przeliczone przez `fx` na walutę notowań albo `None`.

## price_to_sales

P/S = kapitalizacja / (przychody × fx). Gdy brakuje składników: wartość Yahoo, ale tylko przy tej samej walucie. Limit wiarygodności: 200.

## enterprise_to_ebitda

EV/EBITDA, gdzie EV = kapitalizacja + (dług − gotówka) × fx, a EBITDA × fx. Wartość ujemna jest zwracana (ValuationAnalysis zapisuje ją jako notatkę). Limit: 500.

## price_to_book

Przy tej samej walucie: `priceToBook` z Yahoo. Przy innej: P/B = kapitalizacja / kapitał własny, gdzie kapitał = dług / (`debtToEquity` / 100) × fx, bo `bookValue` na akcję jest dla ADR bezużyteczne (ASML: 1,16). Bez długu albo D/E nie da się go odtworzyć i jest pomijany. Limit: 200.

## free_cash_flow_yield

FCF × fx / kapitalizacja, w procentach. Poza ±50% (`SANE_FCF_YIELD`) jest pomijany jako błąd danych.

## SANE_LIMITS

Górne granice, powyżej których wskaźnik uznaje się za błąd danych, a nie za drogą wycenę: P/B 200, P/S 200, EV/EBITDA 500. Mniejsze wartości przechodzą bez zmian. Obniżenie limitów oznaczałoby więcej tickerów z „!” i mniej sygnałów wyceny; podniesienie przepuszcza więcej błędów Yahoo do oceny.

## market_cap

The published market capitalisation, falling back to price times share count when Yahoo does not supply one.

## year_range

`(low, high)` over the trailing 52 weeks. Prefers Yahoo's own figures and falls back to measuring the daily series directly.

## share_count_change

Percent change in shares outstanding over the last year, or `None` when no history is published.

This is the single most informative number in the supply block. Negative means the company has been retiring its own stock, which lifts every per-share figure without the business doing anything more. Positive means shareholders are being diluted, which quietly erodes a holding even while the company grows.

## average_volume

Average daily volume, from Yahoo where available and measured over the last 60 daily candles otherwise.
