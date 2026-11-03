Mierzy czynniki 1–6 mies. jednej pobranej spółki i zwraca StockCandidate. Każdy czynnik jest zorientowany „więcej = lepiej”; czynnik, którego nie da się zmierzyć, ma wartość `None` i później nie dostaje wagi. Osobny blok, bo to jedyne miejsce, gdzie surowe dane Yahoo zamieniają się w liczby rankingu — ThemeRanker porównuje już tylko gotowe wartości. Wejścia: `screener_settings`, `Recommendation` (klasa z bloku Recommendation — pełna analiza StockAnalysera) i `forecaster` (PriceForecaster, prognoza Chronos-2); wyjście `factor_model` do ScreenerReport.

## screener_settings
ScreenerSettings: `analysis_settings()`, `factor_weights` (liczone są tylko czynniki z wagą), `min_analysts`.

## Recommendation
Klasa Recommendation; `Recommendation(market, analysis_settings)` daje werdykt i wynik −100..+100 (czynnik `analysis_score`) oraz ramkę ze wskaźnikami dla prognozy.

## forecaster
PriceForecaster albo `None`. Gdy jest i działa (`enabled()`), liczy prognozę na `forecast_steps` świec; brak pakietu `chronos-forecasting` → czynnik `forecast` pusty.

## TRADING_DAYS / MONTH / HALF_YEAR
252, 21 i 126 świec dziennych — rok, miesiąc i pół roku sesji.

## CAPS
Obcięcia wartości Yahoo przed rankingiem (np. potencjał do ceny docelowej −90%…+300%), chroniące przed oczywistymi błędami danych. Na percentyle wpływają tylko dla skrajnych przypadków.

## factor_model
Wyjście bloku: zwraca samą instancję, bo ScreenerReport woła `measure` osobno dla każdej spółki.

## measure(market)
Zwraca StockCandidate; nigdy nie rzuca wyjątku (problemy trafiają do `problems`). Czynniki:
- `momentum_12_1` — zwrot od 12 do 1 mies. temu (pomija ostatni miesiąc, który ma tendencję do odwracania się);
- `momentum_6_1` — zwrot od 6 do 1 mies. temu;
- `reversal_1m` — minus zwrot z ostatniego miesiąca (kara za przegrzanie);
- `high_proximity` — cena / maksimum 52 tyg. (efekt bliskości szczytu);
- `trend` — cena / SMA200 − 1;
- `low_volatility` — minus roczna zmienność z 6 mies.;
- `analyst_upside` — średnia cena docelowa / cena − 1 (≥ `min_analysts` opinii);
- `analyst_rating` — minus średnia rekomendacja Yahoo (1 = strong buy, 5 = sell);
- `forward_eps_growth` — EPS prognozowany / EPS z 12 mies. − 1 (tylko dodatni EPS bieżący);
- `earnings_growth`, `revenue_growth` — wzrost zysku kwartalnego i przychodów r/r;
- `return_on_equity`, `profit_margin` — jakość biznesu;
- `fcf_yield` — wolne przepływy / kapitalizacja (przeliczone przez MarketData);
- `peg` — minus PEG (tylko dodatni);
- `analysis_score` — wynik StockAnalysera;
- `forecast` — zmiana mediany Chronos-2 (ułamek).
Spółka bez min. 20 świec dostaje pustego kandydata (zostanie odrzucona przez filtr `min_bars`).
