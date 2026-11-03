Buduje listę kandydatów każdego tematu: najpierw tickery wpisane ręcznie w `ScreenerSettings.THEMES`, potem największe (wg kapitalizacji) spółki z branż Yahoo pasujących do słów kluczowych tematu, notowane na giełdach USA (Nasdaq, NYSE, NYSE American). Osobny blok, bo dobór „uniwersum” to inna odpowiedzialność niż pobieranie danych czy ocena; wejście `screener_settings` z ScreenerSettings, wyjście `universe` do ScreenerReport.

## screener_settings
ScreenerSettings (wejście): `themes`, `use_yahoo_screener`, `screen_size_per_industry`, `max_candidates_per_theme`, `min_market_cap`.

## US_EXCHANGES
Kody giełd Yahoo brane pod uwagę: `NMS`, `NGM`, `NCM` (Nasdaq), `NYQ` (NYSE), `ASE` (NYSE American). Usunięcie kodu zawęża dodatki z Yahoo; listy ręczne nie są filtrowane.

## notes
Lista ostrzeżeń (słowo kluczowe bez pasującej branży, błąd wyszukiwarki Yahoo) — wypisywana na początku raportu. Błąd Yahoo nie zatrzymuje skanu: temat zostaje z listą ręczną.

## universe
Wyjście bloku: zwraca samą instancję, bo ScreenerReport wywołuje na niej dwie metody (`themes`, `all_tickers`) i czyta `notes`.

## themes
Zwraca `{temat: [ticker, ...]}` — lista ręczna, potem dodatki Yahoo bez powtórzeń, przycięta do `max_candidates_per_theme`. Liczone raz (wynik zapamiętany).

## all_tickers
Wszystkie różne tickery ze wszystkich tematów, w kolejności pierwszego wystąpienia — to je pobiera UniverseFetcher (każdy tylko raz).
