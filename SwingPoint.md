Rekord danych (`@dataclass(frozen=True)`) z jednym punktem zwrotnym ZigZag — szczytem albo dołkiem swingu. Tworzy go `PatternDetector` (`_swing_points`), trafia do `PatternReading.swings`, a `CandleChart` rysuje z listy takich punktów czarną łamaną na panelu ceny. Jest osobnym blokiem, bo to czysty rekord używany przez kilka klas; jako rekord nie ma połączeń na płótnie — importują go `PatternDetector` i `PatternReading`.

## bars_ago
Świeca punktu liczona wstecz od najnowszej (`int ≥ 0`, `0` = dzisiejsza). Dzięki temu punkt da się umieścić na dowolnym wycinku ramki; `CandleChart` pomija punkty z `bars_ago` większym niż liczba rysowanych świec.

## price
Cena punktu (`float`, w walucie notowania): `High` świecy dla szczytu, `Low` dla dołka. Wyznacza położenie wierzchołka łamanej.

## kind
`"HIGH"` (szczyt swingu) albo `"LOW"` (dołek). Inne wartości nie są tworzone; `PatternDetector` używa ich do rozdzielenia punktów na linię górną i dolną formacji.

## confirmed
`True` dla zakończonego swingu (cena cofnęła się od niego o co najmniej `swing_atr × ATR`), `False` dla skrajnego punktu bieżącego ruchu, który może się jeszcze przesunąć. Niepotwierdzony punkt jest rysowany linią kropkowaną i nie służy do dopasowania formacji.

## is_high
`True`, gdy `kind == "HIGH"`.

## to_dict()
Słownik do `analysis.json`: `bars_ago`, `price` (zaokrąglona do 4 miejsc), `kind`, `confirmed`.
