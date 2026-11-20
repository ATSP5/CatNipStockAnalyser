Draws the candlestick chart at whatever horizon the run asked for, and saves it as a PNG in the output directory.

Four stacked panels share one x axis: candles with the 20, 50 and 200 moving averages and the Bollinger envelope, then volume, then RSI, then MACD. The rating appears in the top right and the composite score in the title, so a chart read on its own still carries the verdict.

Candles are plotted against their position in the series rather than against real time. That is deliberate — plotting against real timestamps opens blank stretches across every weekend and, on an intraday horizon, across every overnight gap, which squeezes the actual trading into a fraction of the width.

The matplotlib Agg backend is selected on import, so this never tries to open a window and is safe to run headless.

Inside CatNip the run engine replaces `plt.show()` with its own capture, which puts the figure straight into the **Output** tab. The block calls `show()` only when it has been replaced that way — calling the real Agg version outside CatNip would do nothing but warn that it cannot display anything.

## draw

`draw(verdict, settings, forecast=None, note=None, patterns=None)` — z `forecast` (PriceForecast) rysuje też prognozę AI; `note` to powód jej braku, pokazywany na wykresie; z `patterns` (PatternReading) rysuje formacje świecowe.

Renders a verdict and saves it and returns the file path. The class method is the intended entry point. A verdict with fewer than 2 candles (NO DATA) gets an empty chart from `_render_empty`, so its analysis is still visible.

## render

Does the work behind `draw` on an already-constructed instance.

## UP / DOWN

The candle colours — teal for a close at or above the open, red below.

## RATING_COLOUR

Maps each verdict to the colour it is printed in, green through amber to red.

## path

Where the PNG was written, set once `render` has run. The filename is `<TICKER>_<horizon>.png`, so charts for different horizons sit side by side rather than overwriting each other.

## Panel layout

The price panel takes a little over three times the height of the others, since it carries the candles, three moving averages and the Bollinger envelope at once. A candle with no body — where open and close match exactly — is drawn as a hairline so that a doji stays visible rather than disappearing.

The number of candles drawn comes from `Settings.CHART_CANDLES`, defaulting to the most recent 180. The indicators are calculated over the full history and only then trimmed for drawing, so a 200-candle average is still correct on the left-hand edge of the chart.

## Nagłówek: legenda i ramka nad wykresem

Legenda panelu ceny (`_price_legend`) i ramka formacji (`_pattern_box`) stoją w pasie między tytułem a panelem ceny, nie na nim — nie zasłaniają świec, średnich ani prognozy. `_layout` mierzy obie i dobiera wysokość pasa; panele mają zawsze tę samą wysokość (`PLOT_HEIGHT`), a rośnie cały obraz. Gdy legenda i ramka nie mieszczą się obok siebie na szerokości panelu, ramka idzie nad legendę. Legenda MACD zostaje w panelu MACD.

## FIGURE_WIDTH
Szerokość PNG w calach, `13.0` (przy `dpi=110` ≈ 1430 px). Większa = więcej miejsca na nagłówek i świece.

## PLOT_HEIGHT
Łączna wysokość czterech paneli w calach, `8.4`. Nie zależy od nagłówka. Większa = wyższe panele i wyższy PNG.

## BOTTOM_BAND
Pas pod panelami na daty osi X, `0.8` cala. Mniej niż ok. 0,7 może uciąć obrócone etykiety dat.

## TITLE_BAND
Pas na tytuł, rekomendację i `SUSPECT_TEXT`, `0.85` cala. Mniejszy może nałożyć ostrzeżenie o danych na nagłówek.

## HEADER_GAP
Odstęp (cale) między elementami nagłówka a panelem i między ramką a legendą, gdy stoją jedna nad drugą, `0.06`.

## BOX_PAD
Zapas (cale) doliczany do zmierzonego tekstu ramki na jej obramowanie i przesunięcie, `0.12`. Za mały = ramka może dotknąć tytułu.

## LEFT / RIGHT
Lewa i prawa krawędź paneli jako ułamek szerokości obrazu, `0.07` / `0.94`. Prawa krawędź ramki formacji i napis rekomendacji są do niej wyrównane.

## LEGEND_COLUMNS
Liczba kolumn legendy panelu ceny, `3`. Więcej = niższa, ale szersza legenda (wtedy częściej ramka idzie nad nią).

## _price_legend(axis)
Tworzy legendę panelu ceny zakotwiczoną lewym dolnym rogiem w lewym górnym rogu panelu (nad nim). Zbiera wpisy wszystkiego, co narysowano z etykietą: Bollinger, SMA, prognoza, ZigZag, formacja cenowa. Zwraca legendę albo `None`.

## _layout(figure, axis, legend)
Mierzy legendę i ramkę (`_measure`), ustawia rozmiar obrazu (`FIGURE_WIDTH` × suma pasów) i marginesy paneli. Zwraca wysokość obrazu w calach — według niej `render` ustawia tytuł, rekomendację i ostrzeżenie o danych.

## _measure(figure, artist)
Szerokość i wysokość elementu wykresu w calach (przez renderer Agg); `(0, 0)` dla `None`.

## FORMATION
Kolor ZigZaga i linii formacji cenowej, `#111111` (prawie czarny).

## _zigzag(axis, swings, count, close)
Czarna łamana przez potwierdzone punkty swingów (`PatternReading.swings`) z kropkami na zwrotach (wpis legendy „ZigZag (swingi)”), a od ostatniego potwierdzonego swingu — linia kropkowana przez niepotwierdzony skrajny punkt do dzisiejszego zamknięcia. Punkty spoza rysowanego wycinka są pomijane.

## _formation(axis, formation, count)
Dwie czarne linie formacji cenowej (`PatternReading.formation`): górna przez szczyty, dolna przez dołki, od pierwszego swingu formacji do dzisiejszej świecy, z bardzo lekkim szarym wypełnieniem między nimi; wpis legendy „Formacja cenowa (KOD)”. Bez formacji (`None`) nic nie rysuje.

## _stamp(stamp)
Znacznik czasu świecy jako tekst: `RRRR-MM-DD`, na interwałach śróddziennych z godziną `RRRR-MM-DD GG:MM`. Używany przez oś X i napis przy linii history/forecast.

## Time axis

Roughly ten evenly spaced candles are labelled with their real timestamps, formatted with the time included on intraday horizons and as a plain date otherwise. Z prognozą ostatnia prawdziwa świeca zawsze dostaje własną, pogrubioną etykietę pod linią history/forecast, a zwykłe etykiety bliżej niż pół odstępu od niej są pomijane, żeby się nie nakładały.

## forecast

PriceForecast z bloku PriceForecaster albo `None`. Gdy jest, panel ceny ciągnie się za ostatnią świecę o `forecast.steps` pozycji: fioletowa linia to mediana prognozy (start od ostatniego zamknięcia), jasne pasmo to przedział 10–90%. Tytuł dostaje dopisek `forecast N candles: ±x%` (zmiana mediany na końcu horyzontu względem ostatniego zamknięcia). `None` → wykres jak dawniej.

## _today_line

Pionowa kreskowana linia między ostatnią prawdziwą świecą a pierwszą prognozowaną, na wszystkich widocznych panelach (cena, wolumen, RSI, MACD), z podpisami „history” / „forecast” i pionowym napisem `ostatnia świeca: <data>` przy górze linii — znacznik czasu ostatniej świecy z danych (`window.index[-1]`), od którego liczona jest prognoza. Ta sama data jest pogrubioną etykietą osi X dokładnie pod linią (`_time_axis`). Rysowana tylko wtedy, gdy jest prognoza.

## Oś czasu z prognozą

Etykiety osi obejmują też przyszłe świece — ich daty pochodzą z `forecast.timestamps` (dni sesyjne dla `1d`, co 7 dni dla `1wk`/`5d`, pierwsze dni miesięcy dla `1mo`; dla interwałów śróddziennych odstępy są równe i pomijają godziny sesji, więc daty są przybliżone).

## SUSPECT_TEXT

Napis `! Możliwe błędne dane`, rysowany na czerwono pod rekomendacją w prawym górnym rogu (`_suspect_mark`), gdy `MarketData.has_suspect_data()`, czyli gdy jakąś wartość Yahoo trzeba było pominąć jako niemożliwą (np. free float ASML 5520%). Szczegóły są w karcie tickera w terminalu. Wartości, które udało się poprawić (np. P/B po przeliczeniu waluty), nie dają tego napisu.

## _render_empty

Wykres dla tickera bez danych: tytuł `<TICKER> -- <interwał> candles | score n/a`, etykieta NO DATA i na środku „Brak danych” z powodem (`Recommendation.missing_reason()`). Zapisywany pod tą samą nazwą `<TICKER>_<interwał>.png` i pokazywany w zakładce Output jak każdy inny.

## FORECAST

Kolor prognozy (`#7b1fa2`).

## note

Tekst (albo `None`) pokazywany w czerwonej ramce w prawym dolnym rogu panelu ceny, gdy prognoza była zamówiona (`future_horizon > 0`), ale jej nie ma — np. `forecast off: No module named 'torch' -- install the pip package chronos-forecasting`. Przy narysowanej prognozie jest ignorowany. Dostarcza go Report (`_forecast_note`).

## Pasmo 24–76%

Gdy `forecast.has_inner()`, wewnątrz jasnego pasma 10–90% rysowane jest ciemniejsze pasmo `inner_low`–`inner_high` (domyślnie 24–76%, w legendzie „median ±26 pp”), też startujące od ostatniego zamknięcia.

## GRID_COLOUR

Kolor linii siatki (`#9e9e9e`, neutralny szary), wspólny dla siatki głównej i pomocniczej na wszystkich czterech panelach. Dowolny kolor matplotlib; ciemniejszy kolor daje mocniejszą siatkę. Wpływa wyłącznie na wygląd PNG, nie na analizę.

## GRID_MAJOR

Styl siatki głównej — linie przy każdej opisanej podziałce (ceny, wolumen, RSI, MACD na osi Y; daty na osi X). Domyślnie `alpha 0.55`, `linewidth 0.8`, linia ciągła. `alpha` w zakresie 0–1 (0 = niewidoczna, 1 = pełny kolor); `linewidth` w punktach, sensownie 0.3–2. Poza zakresem `alpha` matplotlib zgłasza błąd i wykres nie powstaje (Report zapisze to w błędach tickera).

## GRID_MINOR

Styl siatki pomocniczej między liniami głównymi — domyślnie `alpha 0.30`, `linewidth 0.5`, linia kropkowana, żeby nie zagłuszała świec. Te same zakresy co `GRID_MAJOR`.

## GRID_MINOR_DIVISIONS

Na ile komórek siatka pomocnicza dzieli jedną komórkę siatki głównej (domyślnie `4`, na obu osiach). Liczba całkowita ≥ 1; `1` wyłącza praktycznie siatkę pomocniczą, wartości > 6 robią gęstą „kratkę”.

## _grid

Rysuje siatkę na jednym panelu: ustawia `AutoMinorLocator(GRID_MINOR_DIVISIONS)` na obu osiach, siatkę główną (`GRID_MAJOR`) i pomocniczą (`GRID_MINOR`) w kolorze `GRID_COLOUR`, krótkie podziałki pomocnicze i umieszcza siatkę pod danymi (`set_axisbelow`). Wywoływana przez `render` dla każdego z czterech paneli.

## patterns

`PatternReading` z bloku `PatternDetector` (przez `Report`) albo `None`. Argument konstruktora i `draw`, domyślnie `None` — wtedy wykres wygląda jak dawniej. Gdy jest, `_patterns` rysuje na panelu ceny okno formacji i każdą formację, a tytuł dostaje dopisek `| świece BULL/BEAR/NEUTRAL/NONE` (werdykt formacji świecowych) i — gdy jest formacja cenowa — `| formacja BULL/BEAR/NEUTRAL` (`ChartFormation.bias`). Formacje nie zmieniają oceny (`rating`, `score`) pokazywanej na wykresie.

## _patterns

Rysuje formacje świecowe:

- **okno formacji** — jasnożółte tło (`PATTERN_WINDOW`) od początku automatycznie dobranego okna do dzisiejszej świecy, pomarańczowa kropkowana linia przez wszystkie widoczne panele i podpis „okno formacji: N świec” u dołu panelu ceny;
- **każda formacja** — przerywana ramka obejmująca jej świece (od najniższego `low` do najwyższego `high`), zielona dla BULL, czerwona dla BEAR; znacznik ▲ pod ramką (BULL) albo ▼ nad nią (BEAR) i kod formacji (`ENG`, `MS`, `H`…). Formacja zanegowana przez następną świecę jest półprzezroczysta. Znaczniki bliskich formacji tego samego kierunku (< 4 świece) są rozsuwane na 3 poziomy, żeby się nie nakładały;
- **struktura ceny** — czarny ZigZag (`_zigzag`) i czarne linie formacji cenowej (`_formation`);
- formacja, której początek wypada przed rysowanym wycinkiem, jest pomijana (w praktyce nie występuje, bo okno jest przycinane do `chart_candles`).

## _pattern_box

Ramka **nad** panelem ceny, wyrównana do jego prawej krawędzi (w pasie nagłówka, więc nie zasłania świec ani prognozy): gdy jest formacja cenowa — pierwsza linia `Formacja cenowa: <BULL/BEAR/NEUTRAL> -- <nazwa>, <położenie ceny>`, potem werdykt formacji z `net`, długość okna z uzasadnieniem i `PATTERN_LIST` najnowszych formacji (▲/▼, kod, nazwa, ile świec temu, stan potwierdzenia); starsze są zliczone jako „... i N starszych”. Kolor obramowania z `BIAS_COLOUR`.

## BIAS_COLOUR

Kolor obramowania ramki według werdyktu: BULL = `UP` (turkus), BEAR = `DOWN` (czerwony), NEUTRAL = bursztyn, NONE = szary.

## PATTERN_WINDOW

Kolor tła okna formacji (`#fff8e1`, rysowany z `alpha 0.6` pod świecami). Wpływa tylko na wygląd.

## PATTERN_LIST

Ile najnowszych formacji wypisać w ramce, domyślnie `5`. Liczba całkowita ≥ 0; więcej = wyższa ramka i wyższy pas nagłówka (cały PNG robi się wyższy, panele zachowują wysokość). Pełna lista jest w karcie tickera i w `analysis.json`.
