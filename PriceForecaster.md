Prognozuje przyszłe ceny zamknięcia gotowym, wytrenowanym modelem AI **Chronos-2** (Amazon, `amazon/chronos-2`) na `Settings.future_horizon` świec naprzód i zwraca PriceForecast z medianą, pasmem 10–90% i węższym pasmem 24–76% (mediana ±26 pp).

**Dlaczego tu jest:** izoluje model AI (torch, transformers, pobieranie wag) od reszty potoku — Report i CandleChart dostają tylko liczby. Chronos-2 to model bazowy dla szeregów czasowych: prognozuje serię, której nigdy nie widział, bez doszkalania (zero-shot), i w 2026 r. był w czołówce rankingu GIFT-Eval. Zwraca kwantyle, a nie jedną linię, bo cena akcji jest w dużej mierze nieprzewidywalna — model widzi tylko historię cen (bez wiadomości i fundamentów), więc pasmo to statystyczne przedłużenie, a nie pewna prognoza. Wejście `settings` ← Settings; wyjście `forecaster` → wejście `Forecaster` bloku Report, który przekazuje prognozę do CandleChart.

Wymaga pakietu pip `chronos-forecasting` (ciągnie torch i transformers). Przy pierwszym użyciu wagi (~0,5 GB) są pobierane z Hugging Face do folderu `models` w projekcie. Brak pakietu lub błąd ładowania nie przerywa raportu: powód (`forecast off: …`) trafia do konsoli, do podsumowania raportu, do `analysis.json` (`forecast_status`) i jako czerwona ramka na każdy wykres. Uwaga: automatyczna instalacja pakietów w CatNip zamienia `import chronos` na niewłaściwy pakiet PyPI `chronos` — w ustawieniach maina trzeba wybrać instalację **Manual** i wpisać `chronos-forecasting`.

## settings
Settings: `future_horizon` (ile świec) i `horizon` (interwał świecy — wyznacza daty przyszłych świec).

## model_id
Model z Hugging Face, domyślnie `MODEL_ID = "amazon/chronos-2"`. Można podać inny model Chronos-2 (np. własny, dostrojony); modele innych rodzin wymagają zmiany kodu ładowania.

## cache_dir
Folder na wagi modelu, domyślnie `MODEL_CACHE = "models"` (względem folderu uruchomienia). W Dockerze trzyma wagi w folderze projektu, więc nie są pobierane przy każdym uruchomieniu. `None` albo `""` = domyślny cache Hugging Face.

## QUANTILES
Poziomy kwantyli `(0.1, 0.5, 0.9)` — pasmo 10–90% i mediana. Szersze (np. 0.05/0.95) dają szersze pasmo; poziomy spoza zakresu treningu modelu są przycinane z ostrzeżeniem.

## MAX_CONTEXT
Ile ostatnich świec czyta model (2048 — kontekst Chronos-2). Dłuższa historia z `lookback` jest przycinana do najnowszych świec.

## MIN_CONTEXT
Minimalna liczba świec (32); przy krótszej historii prognoza nie powstaje (`None`).

## FREQUENCIES
Interwał → częstotliwość pandas przyszłych świec: `1d` → dni sesyjne (`B`), `5d`/`1wk` → co 7 dni, `1mo` → początek miesiąca, `3mo` → początek kwartału, śróddzienne → równe minuty/godziny (bez godzin sesji, więc daty przybliżone). Nieznany interwał → `B`.

## forecaster()
Wyjście bloku: zwraca tę instancję.

## enabled()
`True`, gdy `future_horizon > 0` i model nie zgłosił wcześniej problemu.

## forecast(verdict)
PriceForecast dla `verdict.frame["Close"]` albo `None` (prognoza wyłączona, za mało danych, brak modelu). Model jest ładowany leniwie przy pierwszym wywołaniu (GPU, jeśli torch widzi CUDA, inaczej CPU) i używany dla wszystkich tickerów.

## future_timestamps(last, steps)
Daty `steps` świec po `last`, według `FREQUENCIES`.

## problem
Przyczyna wyłączenia prognoz (brak pakietu, błąd pobierania modelu) albo `None`.

## status()
Jedna linia dla raportu: `forecast: amazon/chronos-2, N candles ahead, 10-90% band`, albo powód braku prognozy — `future_horizon` = 0, brak pakietu (`No module named 'torch'`/`'chronos'`), zainstalowany niewłaściwy pakiet `chronos` (bez `Chronos2Pipeline`, np. niezwiązany pakiet z PyPI albo chronos-forecasting < 2.0), błąd pobierania wag. Przed pierwszą prognozą: `forecast not run yet`.

## INNER_QUANTILES
Węższe pasmo wokół mediany, domyślnie `(0.24, 0.76)` = mediana ±26 punktów procentowych. Model jest pytany o wszystkie poziomy naraz (`QUANTILES` ∪ `INNER_QUANTILES`), więc nie wydłuża to obliczeń. Wartości w (0, 1), dolna < 0,5 < górna; poziomy między trenowanymi kwantylami Chronos-2 są interpolowane. `None` wyłącza węższe pasmo. Zmiana na np. `(0.25, 0.75)` daje pasmo 25–75% (mediana ±25 pp); węższe pasmo = mniej przyszłych cen w środku.
