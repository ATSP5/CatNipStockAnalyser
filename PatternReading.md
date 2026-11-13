Rekord danych (`@dataclass(frozen=True)`) z wynikiem analizy formacji świecowych jednego tickera: jakie okno przeszukano i dlaczego, jakie formacje w nim znaleziono oraz łączny werdykt **BULL / BEAR / NEUTRAL / NONE**. Zwraca go `PatternDetector.detect()`; `Report` przechowuje go w `patterns`, drukuje w karcie, zapisuje do JSON/CSV i przekazuje do `CandleChart.draw(patterns=…)`. Jako rekord danych nie ma połączeń na płótnie — importują go `PatternDetector`, a pośrednio korzystają z niego `Report` i `CandleChart`.

## window
Liczba świec wstecz od dzisiejszej, w których szukano formacji (`int`, zwykle `PatternDetector.min_window … max_window`, domyślnie 15–120; nie więcej niż rysowany wycinek wykresu ani dostępna historia). Dobierana automatycznie z ostatnich swingów ceny — patrz `PatternDetector.choose_window`. Na wykresie to jasnożółte tło i kropkowana linia „okno formacji: N świec”.

## window_reason
Tekst wyjaśniający długość okna, np. `"ostatnie swingi: 2 (ZigZag 2.0×ATR)"`, z dopiskiem `", podniesione do minimum 15"` albo `", przycięte do 120"` gdy zadziałało ograniczenie, lub `"brak wyraźnych swingów -- okno maksymalne"`.

## patterns
Lista `CandlePattern` znalezionych w oknie, po usunięciu nakładających się formacji tego samego kierunku, posortowana od najnowszej (`bars_ago` rosnąco). Pusta, gdy w oknie nie ma żadnej formacji.

## bull_score
Suma `strength × 0,5^(bars_ago / półokres)` formacji BULL, gdzie półokres = max(3, `window`/4) świec. `float ≥ 0`. Świeża, potwierdzona formacja waży najwięcej.

## bear_score
To samo dla formacji BEAR.

## bias
Werdykt: `"BULL"` gdy `net() > bias_threshold` (domyślnie 0,2), `"BEAR"` gdy `net() < −bias_threshold`, `"NEUTRAL"` gdy siły się równoważą, `"NONE"` gdy w oknie nie ma formacji. Pokazywany w tytule wykresu, w ramce, w kolumnie `CANDLES` tabeli podsumowania i w CSV (`pattern_bias`). **Nie wpływa** na score ani na rekomendację BUY/SELL — jest osobną informacją.

## net()
Przewaga strony: `(bull_score − bear_score) / (bull_score + bear_score)`, od −1 (tylko formacje niedźwiedzie) do +1 (tylko bycze); 0 gdy brak formacji.

## count(direction)
Liczba formacji danego kierunku (`"BULL"` lub `"BEAR"`) w `patterns`.

## summary()
Jedna linia do karty tickera: werdykt, `net`, liczba formacji byczych i niedźwiedzich, długość okna i jej uzasadnienie.

## to_dict()
Słownik zapisywany w `analysis.json` jako `candle_patterns`: `bias`, `net`, `window`, `window_reason`, `bull_score`, `bear_score` i lista `patterns` (każda przez `CandlePattern.to_dict()`).
