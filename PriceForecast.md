Rekord danych: prognoza AI cen zamknięcia jednego tickera na `future_horizon` świec naprzód — mediana i dwa pasma kwantylowe (10–90% i węższe 24–76%) dla każdej przyszłej świecy. Tworzy go PriceForecaster, czytają go Report (wydruk, JSON, CSV) i CandleChart (pasmo na wykresie).

**Dlaczego tu jest:** oddziela wynik modelu od samego modelu — wykres i raport nie muszą nic wiedzieć o Chronos-2 ani o torch; dostają gotowe tablice liczb. Jako czysty rekord danych nie jest podłączony na kanwie.

## ticker
Symbol, np. `AAPL`.

## model
Identyfikator modelu z Hugging Face, np. `amazon/chronos-2`; pokazywany w legendzie wykresu i w raporcie.

## last_close
Ostatnie prawdziwe zamknięcie (waluta tickera) — punkt startu linii prognozy i baza dla `change_pct()`.

## timestamps
Lista dat przyszłych świec (długość = `steps`) z `PriceForecaster.future_timestamps`; służą do etykiet osi czasu i pola `end`.

## low, median, high
Tablice numpy długości `steps`: kwantyle prognozy (domyślnie 10%, 50%, 90%) w walucie tickera. Przy dobrze skalibrowanym modelu ok. 80% przyszłych cen powinno mieścić się między `low` a `high`.

## quantiles
Krotka poziomów kwantyli `(niski, mediana, wysoki)`, domyślnie `(0.1, 0.5, 0.9)`; wartości w przedziale (0, 1).

## steps
Liczba prognozowanych świec (= `Settings.future_horizon`).

## change_pct()
Zmiana mediany na końcu horyzontu względem `last_close`, w %. Dodatnia = model oczekuje (w medianie) wzrostu.

## to_dict()
Słownik do `analysis.json` i CSV: `model`, `steps`, `quantiles`, `end`, `median_end`, `low_end`, `high_end`, `change_pct`, a przy węższym paśmie także `inner_quantiles`, `inner_low_end`, `inner_high_end`.

## inner_low, inner_high
Tablice numpy długości `steps` (albo `None`): węższe pasmo wokół mediany — domyślnie kwantyle 24% i 76%, czyli mediana ±26 punktów procentowych. Przy dobrze skalibrowanym modelu ok. 52% przyszłych cen powinno mieścić się w tym paśmie. `None`, gdy `PriceForecaster.INNER_QUANTILES = None`.

## inner_quantiles
Krotka poziomów węższego pasma, domyślnie `(0.24, 0.76)`, albo `None`.

## has_inner()
`True`, gdy węższe pasmo jest policzone.
