Wykrywa formacje świecowe (22 rodzaje, 1-, 2- i 3-świecowe) w automatycznie dobranym oknie wstecz od dzisiejszej świecy, oznacza każdą jako **BULL** albo **BEAR** i składa je w werdykt `PatternReading`. Jest osobnym blokiem, bo rozpoznawanie formacji to odrębna odpowiedzialność od liczenia wskaźników (`Indicators`), punktowania (`TechnicalAnalysis`) i rysowania (`CandleChart`). Wejście `settings` ← `Settings` (potrzebne `chart_candles`), wyjście `pattern_detector` → wejście `PatternDetector` bloku `Report`. Wyjście zwraca cały obiekt, bo `Report` wywołuje `detect(verdict)` raz na ticker we własnej pętli, z werdyktem, który ma tylko on — wyniku nie da się policzyć z góry jedną metodą. Wynik idzie do `CandleChart.draw(patterns=…)`, karty tickera, JSON i CSV; **nie zmienia score ani rekomendacji**.

**Jak dobierane jest okno.** Formacja świecowa to sygnał krótkoterminowy — ma znaczenie, dopóki nie rozegrał się ruch, który zapowiadała. Dlatego okno nie ma stałej długości: ZigZag z progiem `swing_atr × ATR(14)` dzieli historię na swingi (ruchy od dołka do szczytu i z powrotem), a okno sięga do początku `swings` ostatnich zakończonych swingów (plus 3 świece rozbiegu), czyli obejmuje ostatni pełny zwrot i bieżący ruch. Spokojny, długo trendujący walor dostaje długie okno, rozedrgany — krótkie. Wynik jest ograniczany do `[min_window, max_window]`, do liczby rysowanych świec (`Settings.chart_candles`) i do dostępnej historii.

**Kontekst trendu.** Formacje odwrócenia liczą się tylko po pasującym trendzie: bycze po spadku, niedźwiedzie po wzroście. Trend = zmiana zamknięcia z `trend_candles` świec przed formacją, mierzona w ATR; co najmniej `trend_atr` ATR w górę/dół. Marubozu oraz Three White Soldiers / Three Black Crows nie wymagają trendu.

**Katalog** (nazwa, kod, kierunek, świece, siła bazowa):

| Formacja | Kod | Kierunek | Świece | Siła | Trend przed |
| --- | --- | --- | ---: | ---: | --- |
| Morning Star / Evening Star | MS / ES | BULL / BEAR | 3 | 0,75 | spadek / wzrost |
| Bullish / Bearish Engulfing | ENG | BULL / BEAR | 2 | 0,70 | spadek / wzrost |
| Three White Soldiers / Three Black Crows | 3WS / 3BC | BULL / BEAR | 3 | 0,70 | — |
| Three Inside Up / Down | 3IU / 3ID | BULL / BEAR | 3 | 0,65 | spadek / wzrost |
| Piercing Line / Dark Cloud Cover | PL / DCC | BULL / BEAR | 2 | 0,60 | spadek / wzrost |
| Hammer / Shooting Star | H / SS | BULL / BEAR | 1 | 0,60 | spadek / wzrost |
| Inverted Hammer / Hanging Man | IH / HM | BULL / BEAR | 1 | 0,50 | spadek / wzrost |
| Bullish / Bearish Harami | HR | BULL / BEAR | 2 | 0,45 | spadek / wzrost |
| Tweezer Bottom / Top | TB / TT | BULL / BEAR | 2 | 0,45 | spadek / wzrost |
| Dragonfly / Gravestone Doji | DD / GD | BULL / BEAR | 1 | 0,40 | spadek / wzrost |
| Bullish / Bearish Marubozu | MB | BULL / BEAR | 1 | 0,40 | — |

Siła bazowa to przybliżona, literaturowa wiarygodność formacji, a nie wartość zmierzona na danych tego projektu.

## settings
Obiekt `Settings` (wejście ← blok `Settings`). Używane jest tylko `chart_candles` (domyślnie 180): okno nigdy nie jest dłuższe niż rysowany wycinek (min. 20), żeby każda znaleziona formacja była widoczna na wykresie.

## min_window
Najkrótsze okno w świecach, domyślnie `15`. Zakres: `≥ 5`, inaczej `ValueError` przy konstrukcji. Większa wartość = więcej starszych formacji przy bardzo krótkich swingach.

## max_window
Najdłuższe okno, domyślnie `120`. Musi być `≥ min_window` (inaczej `ValueError`). Ogranicza okno przy długich, gładkich trendach; dodatkowo okno jest przycinane do `chart_candles` i do historii.

## swing_atr
Próg ZigZag w wielokrotnościach ATR(14), domyślnie `2.0`. Musi być `> 0` (inaczej `ValueError`); sensownie 1–4. Mniejszy próg = więcej drobnych swingów = **krótsze** okno; większy = tylko duże ruchy = **dłuższe** okno.

## swings
Ile ostatnich zakończonych swingów obejmuje okno, domyślnie `2`. Liczba całkowita `≥ 1` (inaczej `ValueError`). `1` = tylko bieżący ruch od ostatniego zwrotu; `3` = sięga dalej w przeszłość. Gdy swingów jest mniej, okno = maksimum.

## trend_candles
Liczba świec, z których mierzony jest trend przed formacją, domyślnie `6`. `≥ 2` (inaczej `ValueError`). Dłuższy = formacje odwrócenia wymagają dłuższego trendu.

## trend_atr
Minimalna zmiana zamknięcia (w ATR) w `trend_candles` świecach, żeby uznać trend, domyślnie `1.0`. `> 0` (inaczej `ValueError`). Większa wartość = mniej, ale pewniejszych formacji odwrócenia.

## bias_threshold
Próg `net()` dla werdyktu BULL/BEAR, domyślnie `0.2`. Zakres `[0, 1)` (inaczej `ValueError`). `0` = każda przewaga daje BULL/BEAR; większy = częściej NEUTRAL.

## catalogue
Lista definicji formacji: `(nazwa, kod, kierunek, liczba świec, siła bazowa, wymagany trend −1/0/+1, test kształtu)`. Kolejność nie ma znaczenia dla wyniku.

## PIVOT_LEAD
Świece rozbiegu przed najstarszym pivotem włączane do okna, `3` — formacja 3-świecowa na samym dołku/szczycie mieści się w oknie w całości.

## BODY_AVERAGE
Ile poprzednich świec tworzy średni korpus (`10`), względem którego korpus jest „długi” (≥ średnia) albo „mały” (≤ 0,5 średniej).

## CONFIRM_BOOST
Mnożnik siły, gdy następna świeca potwierdziła formację: `1.25`.

## REFUTE_CUT
Mnożnik siły, gdy następna świeca poszła przeciwnie: `0.5`.

## VOLUME_BOOST
Mnożnik siły, gdy wolumen świecy przekroczył średnią 20-sesyjną (`VOL_SMA20`): `1.15`. Bez kolumny `Volume` nie działa.

## pattern_detector()
Wyjście bloku: zwraca sam obiekt (patrz akapit wstępny — `Report` woła `detect` dla każdego tickera osobno).

## detect(verdict)
Zwraca `PatternReading` dla `verdict.frame` (ramka OHLCV z kolumnami `Indicators`, w tym `ATR`) albo `None`, gdy ramki brak lub ma mniej niż `trend_candles + 4` świec. Kolejno: przygotowanie tablic, `choose_window`, skan katalogu, usunięcie nakładek, werdykt. Brak kolumny `ATR` jest uzupełniany własnym ATR(14).

## choose_window(d)
Zwraca `(okno, uzasadnienie)` według reguły ze wstępu. Używana przez `detect`; publiczna, żeby można było sprawdzić okno bez szukania formacji.

## Usuwanie nakładek
Gdy dwie formacje tego samego kierunku dzielą świece (np. Bullish Harami w środku Three Inside Up, albo Tweezer Bottom i Bullish Engulfing na tych samych dwóch świecach), zostaje tylko silniejsza. Formacje przeciwnych kierunków na tych samych świecach zostają obie — ta sprzeczność jest informacją.

## Werdykt
Każda formacja waży `strength × 0,5^(bars_ago / półokres)`, półokres = max(3, okno/4) świec, więc formacja sprzed półokresu liczy się w połowie. Sumy dają `bull_score` i `bear_score`, a z nich `net` i `bias` (patrz `PatternReading`).
