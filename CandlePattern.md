Rekord danych (`@dataclass(frozen=True)`) opisujący jedno wystąpienie formacji świecowej na wykresie tickera: nazwę, kierunek BULL/BEAR, położenie względem dzisiejszej świecy, zakres cen i siłę. Tworzy go `PatternDetector`, zbiera `PatternReading`, a czytają `CandleChart` (rysowanie) i `Report` (karta tickera, JSON, CSV). Jako czysty rekord danych nie ma połączeń na płótnie — bloki, które go używają, importują go (`from CandlePattern import CandlePattern`).

## name
Pełna angielska nazwa formacji, np. `"Bullish Engulfing"`, `"Evening Star"`. `str`, jedna z 22 nazw z `PatternDetector.catalogue`. Pokazywana w ramce na wykresie i w karcie tickera.

## code
Krótki symbol rysowany na wykresie nad/pod świecą, np. `ENG`, `MS`, `3WS`. `str`, 1–3 znaki. Ta sama formacja w wersji byczej i niedźwiedziej ma ten sam kod — kierunek widać po kolorze i strzałce (▲ zielona = BULL, ▼ czerwona = BEAR).

## direction
`"BULL"` (formacja sugeruje wzrost) albo `"BEAR"` (spadek). Inne wartości nie występują. Decyduje o kolorze na wykresie i o tym, do której strony (`bull_score` / `bear_score`) formacja dolicza się w `PatternReading`.

## length
Liczba świec, z których składa się formacja: `1` (np. Hammer), `2` (np. Engulfing) lub `3` (np. Morning Star). Na wykresie ramka obejmuje dokładnie tyle świec.

## bars_ago
Położenie najnowszej świecy formacji liczone wstecz od dziś: `0` = ostatnia świeca, `5` = pięć świec temu. `int ≥ 0`, zawsze mniejsze od okna `PatternReading.window`. Liczenie od końca pozwala `CandleChart` umieścić formację na dowolnym wycinku ramki. Im mniejsze, tym większa waga formacji w werdykcie (zanik wykładniczy).

## timestamp
Znacznik czasu najnowszej świecy formacji (z indeksu ramki: `pd.Timestamp`). Do wydruku i JSON (jako tekst).

## low
Najniższe minimum (`Low`) ze świec formacji, w walucie notowań. Dolna krawędź ramki na wykresie; pod nią rysowany jest znacznik formacji byczej.

## high
Najwyższe maksimum (`High`) ze świec formacji. Górna krawędź ramki; nad nią rysowany jest znacznik formacji niedźwiedziej.

## strength
Siła formacji `0…1`: bazowa wiarygodność z katalogu (0,40–0,75) × 1,25 gdy następna świeca potwierdziła formację, × 0,5 gdy zanegowała, × 1,15 gdy wolumen świecy był powyżej średniej 20-sesyjnej; obcinana do 1,0. Wyższa siła = większy wpływ na werdykt BULL/BEAR i pierwszeństwo przy usuwaniu nakładających się formacji.

## confirmed
`True` — następna świeca zamknęła się w kierunku formacji (wyżej dla BULL, niżej dla BEAR); `False` — w przeciwnym; `None` — formacja na dzisiejszej świecy, jeszcze nie ma czym jej potwierdzić. Formacje zanegowane są na wykresie rysowane półprzezroczyście.

## bullish
Właściwość: `True`, gdy `direction == "BULL"`.

## status()
Zwraca stan potwierdzenia po polsku: `"potwierdzona"`, `"zanegowana"` albo `"niepotwierdzona"` (dla `confirmed = None`).

## to_dict()
Słownik do `analysis.json`: wszystkie pola, `timestamp` jako tekst, `strength` zaokrąglona do 3 miejsc.
