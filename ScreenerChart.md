Rysuje top spółek jednego tematu jako poziomy wykres słupkowy wyniku 0–100 (najlepsza na górze, pierwsze trzy na zielono) z dopiskiem: wynik, momentum 6-1, potencjał do ceny docelowej i prognoza AI. Zapisuje PNG `top_<temat>.png` w `output/screener/`; w CatNip wykres trafia też do zakładki Output. Osobny blok — warstwa prezentacji, niezależna od rankingu. Wejście `screener_settings`, wyjście `screener_chart` do ScreenerReport.

## screener_settings
ScreenerSettings: `draw_chart` (False → nic nie jest rysowane) i `ensure_output_dir()`.

## BAR / BAR_TOP / INK / MUTED / GRID_COLOUR
Kolory: słupek zwykły (niebieski), słupek miejsc 1–3 (zielony), tytuł, dopiski, siatka pionowa co 10 punktów.

## screener_chart
Wyjście bloku: zwraca samą instancję, bo ScreenerReport woła `draw` raz na temat.

## draw(theme, picks)
Rysuje i zapisuje wykres, zwraca ścieżkę PNG albo `None` (brak spółek lub `draw_chart = False`). Nazwa pliku to nazwa tematu bez polskich znaków (np. `top_Polprzewodniki.png`); kolejny przebieg nadpisuje plik.
