# StockAnalyser

Dajesz listę tickerów, dostajesz dla każdego werdykt **STRONG BUY / BUY / HOLD / SELL / STRONG SELL**, wynik liczbowy (*score*), czteropanelowy wykres świecowy z prognozą modelu AI **Chronos-2** oraz uzasadnienie: które sygnały ciągną w górę, które w dół, i jak techniczny score sprawdzał się historycznie.

> **To nie jest porada inwestycyjna.** Program mechanicznie punktuje publiczne dane z Yahoo Finance. Nie czyta wiadomości, raportów kwartalnych ani komunikatów spółek. Zawsze weryfikuj wyniki i konsultuj decyzje ze specjalistą.

Projekt jest grafem CatNip (`StockAnalyser.catnip`): każda klasa to osobny blok, a połączenia na płótnie odpowiadają zależnościom między nimi.

## Trzy osobne rzeczy: wskaźniki, prognoza, rekomendacja

Program rozdziela trzy rzeczy, które łatwo pomylić na wykresie:

| Co | Skąd się bierze | Czy wpływa na HOLD/BUY/SELL? |
| --- | --- | --- |
| **Wskaźniki historyczne** (SMA, Bollinger, RSI, MACD, wolumen, ADX, stochastic…) | `Indicators` → `TechnicalAnalysis` | **Tak** — to blok *technical* |
| **Wycena i podaż akcji** (P/E, PEG, FCF yield, liczba akcji, short interest…) | `MarketData` → `ValuationAnalysis`, `SupplyAnalysis` | **Tak** — bloki *valuation* i *supply*, z wagą zależną od interwału |
| **Prognoza ceny Chronos-2** (fioletowy wachlarz) | `PriceForecaster` → `PriceForecast` | **Nie.** Prognoza jest tylko informacją na wykresie i w raporcie; nie wchodzi do score ani do rekomendacji |

## Jak powstaje score i rekomendacja

1. **Sygnał** (`Score.Signal`) to jedna obserwacja przeliczona na skalę **−100 (maksymalnie niedźwiedzia) … 0 (neutralna) … +100 (maksymalnie bycza)**, zwykle funkcją liniową `Score.ramp` z obcięciem na końcach skali. Każdy sygnał ma wagę w swoim bloku.
2. **Blok** (`Score.Block`) to średnia ważona swoich sygnałów, również −100…+100. Sygnał, którego nie da się policzyć (brak danych), jest pomijany, a wagi reszty są renormalizowane.
3. **Score końcowy** to średnia ważona trzech bloków. Wagi zależą od interwału świecy (`Settings.HORIZON_WEIGHTS`):

   | Interwał | technical | valuation | supply |
   | --- | ---: | ---: | ---: |
   | intraday, `1d` (domyślny) | 90% | 10% | 0% |
   | `5d`, `1wk` | 65% | 25% | 10% |
   | `1mo` | 45% | 35% | 20% |
   | `3mo` | 30% | 45% | 25% |

   Fundamenty niewiele mówią o jutrzejszej cenie, dlatego na świecach dziennych decyduje prawie wyłącznie wykres.
4. **Rekomendacja** to przedział, w który wpada score (`Settings.RATING_BANDS`):

   | Score | Rekomendacja |
   | --- | --- |
   | ≥ +45 | STRONG BUY |
   | +15 … +45 | BUY |
   | −15 … +15 | **HOLD** |
   | −45 … −15 | SELL |
   | < −45 | STRONG SELL |
   | brak świec z Yahoo | NO DATA (pusta analiza, score n/a) |

   HOLD oznacza „sygnały się znoszą, brak wyraźnej przewagi”. Nie oznacza, że akcja jest tania, bezpieczna ani że kurs będzie stabilny.
5. **DATA / confidence** to **pokrycie danych**: jaka część zamierzonych sygnałów faktycznie miała dane (100% = nic nie brakowało). To **nie jest** prawdopodobieństwo trafności rekomendacji.

### Sygnały techniczne i ich kierunek

Uwaga: część sygnałów jest **kontrariańska** (czyta skrajne odczyty jako szansę na powrót do średniej), więc niski RSI *podnosi* score, a nie go obniża.

| Sygnał | Waga | Jak liczony | Kierunek |
| --- | ---: | --- | --- |
| Trend vs średnie | 2.5 | odległość od SMA50 (±8%) i SMA200 (±15%) + golden/death cross (±60) | trendowy |
| Nachylenie SMA50 | 1.5 | nachylenie z 20 świec, ±0,25% na świecę | trendowy |
| MACD (12, 26, 9) | 1.5 | histogram jako % ceny, ±1%; ±35 pkt za świeże przecięcie | trendowy |
| RSI (14, Wilder) | 1.5 | RSI 30 → +100, RSI 70 → −100 | **kontrariański** |
| Momentum (~90 dni) | 1.5 | zmiana ceny z ~62 sesji, ±20% | trendowy |
| Pozycja w Bollinger (20, 2) | 1.0 | %B 0 (dolne pasmo) → +100, 1 (górne) → −100 | **kontrariański** |
| Wolumen (OBV) | 1.0 | nachylenie OBV z 30 świec; ×1,25 przy wolumenie > 1,5× średniej | trendowy |
| Siła trendu (ADX 14) | 1.0 | siła z ADX 10–40, kierunek z DI+ vs DI− | trendowy |
| Stochastic %K (14, 3) | 0.75 | 20 → +100, 80 → −100 | **kontrariański** |
| Obsunięcie od szczytu | 1.0 | −3…−15% = okazja (+45), głębiej = sygnał problemu (do −70) | mieszany |
| Zmienność (ATR 14) | 0.75 | ATR względem własnej normy spółki: 0,7× → +100, 1,8× → −100 | ryzyko |

Pełne listy sygnałów wyceny (13) i podaży (8) z wagami są na stronach dokumentacji bloków `ValuationAnalysis` i `SupplyAnalysis`.

## Przykład: ASML, świece dzienne, uruchomienie 20.10.2026

Wykres `output/ASML_1d.png` z tytułem `ASML -- 1 day candles | ASML Holding N.V. | score +9.6 | forecast 90 candles: -1.0%` i etykietą **HOLD** był analizowany w zewnętrznej rozmowie z ChatGPT, która opierała się wyłącznie na obrazku. Poniżej odpowiedzi na wątpliwości z tamtej rozmowy, na podstawie kodu i pliku `output/analysis.json` z tego samego uruchomienia.

### Dokładne wartości (zamiast odczytu z obrazka)

| Wielkość | Wartość |
| --- | --- |
| Ostatnie zamknięcie | 1 647,12 USD (500 świec dziennych, lookback 2 lata) |
| Względem SMA50 / SMA200 | −5,2% / +4,2%, golden cross (SMA50 > SMA200), SMA50 rośnie 0,087% na świecę |
| RSI (14) | 38,6 |
| Histogram MACD | −20,44 (−1,24% ceny) |
| Bollinger %B | 0,09 (tuż nad dolnym pasmem) |
| Stochastic %K | 19,0 |
| ADX | 18,0 — brak wyraźnego trendu |
| Momentum | −8,6% w 62 sesjach |
| Obsunięcie od szczytu | −17,2% |
| ATR | 3,25% ceny, 1,00× normy ASML |
| Wolumen ostatniej sesji | 0,85× średniej 20-sesyjnej |

### „Co oznacza score +9.6 i jaka jest skala?”

Skala to **−100…+100**, próg BUY to +15, próg SELL to −15. Wynik +9,6 jest lekko dodatni, ale mieści się w strefie neutralnej (5,4 pkt poniżej BUY). Rachunek:

| Blok | Score bloku | Waga przy `1d` | Wkład w score |
| --- | ---: | ---: | ---: |
| technical | +11,5 | 90% | +10,3 |
| valuation | −7,3 | 10% | −0,7 |
| supply | +47,6 | 0% | 0,0 |
| **razem** | | | **+9,6 → HOLD** |

Pokrycie danych: 100% we wszystkich trzech blokach.

Technical +11,5 to wypadkowa przeciwnych sygnałów:

- **na plus:** stochastic 19 (+100), Bollinger %B 0,09 (+81), RSI 38,6 (+57, kontrariańsko), zmienność w normie (+45), umiarkowane obsunięcie (+37), rosnąca SMA50 (+35), trend vs średnie (+8);
- **na minus:** MACD (−100), momentum −8,6% (−43), wolumen/OBV (−8);
- **zero:** ADX 18 (brak trendu).

### „Czy HOLD wynika z reguł, czy z interpretacji?”

Z reguł: score +9,6 wpada w przedział −15…+15, więc `Settings.rating_for` zwraca HOLD. Ocena ChatGPT („rozsądna interpretacja przy niejednoznacznych sygnałach”) zgadza się z mechanizmem. Jedna różnica: ChatGPT czytał RSI ≈ 40 jako słabość. W tym systemie RSI jest sygnałem kontrariańskim, więc RSI 38,6 **podnosi** score (blisko wyprzedania = potencjalne odbicie). Słabość momentum wnoszą natomiast MACD i 90-dniowe momentum.

### „Czy prognoza wpływa na rekomendację?”

Nie. HOLD powstaje wyłącznie z bloków technical, valuation i supply. Prognoza Chronos-2 jest liczona osobno (`PriceForecaster`) i tylko rysowana na wykresie oraz wypisywana w raporcie.

### „Czy −1,0% jest policzone poprawnie i od czego?”

`PriceForecast.change_pct()` = mediana prognozy na ostatniej przyszłej świecy ÷ ostatnie rzeczywiste zamknięcie − 1:
1 630,87 / 1 647,12 − 1 = **−0,99%**, zaokrąglone do −1,0%. To zmiana *mediany* po 90 świecach, a nie oczekiwany zwrot ani prawdopodobieństwo spadku.

### „90 świec to 90 dni?”

90 **sesji** przy świecach `1d`, czyli ok. 4 miesięcy. Daty przyszłych świec są wyznaczane jako dni robocze (`freq="B"`), bez świąt giełdowych, więc data końca (22.02.2027) jest przybliżona: rzeczywista 90. sesja wypada kilka dni później.

### „Co to są pasma 10–90% i 24–76% (median ±26 pp)?”

To kwantyle rozkładu prognozowanego przez Chronos-2 dla każdej przyszłej świecy:

- **Forecast median** — kwantyl 0,5;
- **Forecast 10–90%** — kwantyle 0,1 i 0,9, środkowe 80% rozkładu (na końcu horyzontu: 988–2 339 USD);
- **Forecast 24–76% (median ±26 pp)** — kwantyle 0,24 i 0,76, środkowe 52% rozkładu (1 264–2 001 USD). „±26 pp” oznacza ±26 **punktów procentowych prawdopodobieństwa** wokół kwantyla 50%, a **nie** ±26% ceny.

Poziomy ustawia `PriceForecaster.QUANTILES` i `INNER_QUANTILES`. Przedziały opisują rozkład według modelu i bez walidacji (patrz niżej) nie są gwarancją pokrycia.

### „Czy tak szeroki wachlarz to błąd?”

Nie. Model dostaje wyłącznie ostatnie ceny zamknięcia (tu 500 świec; limit `MAX_CONTEXT` = 2 048), bez wolumenu, wiadomości i fundamentów. Niepewność narasta z każdą świecą, a ASML ma wysoką zmienność (ATR ≈ 3,25% dziennie). Szeroki wachlarz wiernie oddaje to, że cena za 4 miesiące jest w dużej mierze nieprzewidywalna.

### „Jak powstaje prognoza — Chronos-2 dostrojony czy bez treningu?”

Bez treningu. Używany jest wytrenowany model `amazon/chronos-2` w trybie **zero-shot**: nie jest dostrajany na danych ASML ani żadnej innej spółki. Wagi (~0,5 GB) są pobierane z Hugging Face do folderu `models/`.

### „Czy model i score były testowane historycznie?”

- **Score techniczny — tak.** Blok `Backtest` robi test walk-forward: dla każdej świecy po rozgrzewce (200 świec) przelicza blok technical tylko na danych do tej świecy włącznie (wszystkie wskaźniki są przyczynowe, bez look-ahead) i porównuje score ze zwrotem następnej świecy. Dla ASML (299 świec): **rank IC −0,013 (t = −0,23)**, czyli brak wartości predykcyjnej. Strategia „long, gdy score ≥ +15”, z kosztem 10 bp za każdą zmianę pozycji, dała **+66,5% wobec +128,4% buy & hold** (16 transakcji, 81% czasu w pozycji, 56% trafień). IC łączne dla wszystkich 16 tickerów z tego uruchomienia: **−0,0095 na 4 784 świecach**. Wniosek: w tej próbie score techniczny nie daje przewagi, a HOLD należy czytać jako „brak sygnału”, nie jako przemyślaną rekomendację.
- **Bloki valuation i supply — nie.** Opierają się na bieżącym snapshocie fundamentów z Yahoo, którego nie da się odtworzyć wstecz bez look-ahead.
- **Prognoza Chronos-2 — nie (jeszcze).** Proponowany plan walidacji, zgodny z sugestią z rozmowy:
  1. dla wielu dat w przeszłości generować prognozę 90 sesji naprzód wyłącznie z danych dostępnych w danym dniu;
  2. mierzyć błąd mediany (MAE/RMSE prognozowanego **zwrotu**);
  3. porównać z benchmarkami: zerowa zmiana (random walk) i prosty trend;
  4. sprawdzić kalibrację: w paśmie 10–90% powinno wypadać ok. 80% rzeczywistych cen, a w 24–76% ok. 52%;
  5. uwzględnić, że okna 90-sesyjne się nakładają (obserwacje zależne), i nie stroić modelu na okresie, na którym raportuje się wynik.

### „Szara linia wolumenu, okresy RSI i MACD?”

Szara linia to 20-sesyjna średnia wolumenu (`VOL_SMA20`). RSI ma okres 14 (wygładzanie Wildera). MACD ma parametry 12/26/9 (EMA). Bollinger to 20 sesji ± 2 odchylenia standardowe (populacyjne). Kolory SMA: 20 niebieska, 50 pomarańczowa, 200 fioletowa.

### „Czy uwzględniono fundamenty, np. wyniki za Q3 2026?”

Tylko jako snapshot wskaźników z Yahoo (P/E, PEG, marże, rekomendacje analityków…), z wagą 10% przy świecach dziennych. Program nie czyta raportów, wiadomości ani komunikatów spółki (np. o mocach produkcyjnych czy popycie), więc ani score, ani prognoza ich nie widzą.

### Błędne dane Yahoo w tym przykładzie i co z nimi zrobiono

W uruchomieniu z 20.10.2026 Yahoo podał dla ASML wartości niemożliwe: **P/B 1 415×**, **EV/EBITDA 2 166×**, **free float 5 520%**. Trafiły one wtedy do oceny (−100 / −60) i zaniżały blok valuation (−7,3). Przyczyny:

- ASML jest notowany w **USD**, a sprawozdania ma w **EUR**. Yahoo dzieli kapitalizację w USD przez przychody, FCF i EBITDA w EUR bez przeliczenia. Ten sam błąd dotyczy np. TSMC (TWD): Yahoo podaje P/S 0,44 zamiast ok. 14.
- EV Yahoo liczy jako `floatShares × cena`, a `floatShares` jest błędne (21,28 mld akcji przy 385 mln wyemitowanych). Stąd EV 35 bln USD.
- `bookValue` na akcję (1,16) jest dla ADR bezużyteczne, więc P/B wychodzi absurdalne.

Od tej wersji `MarketData` **naprawia** to, co się da: przelicza dane ze sprawozdań na walutę notowań kursem z Yahoo (`EURUSD=X`), liczy EV jako kapitalizacja + dług − gotówka, a kapitał własny odtwarza z długu i wskaźnika dług/kapitał. Dla ASML wychodzi wtedy (przy kursie ≈ 1,16) **P/S ≈ 13,9, EV/EBITDA ≈ 33, P/B ≈ 25, FCF yield ≈ 1,9%**. Liczby z tabel powyżej pochodzą z uruchomienia sprzed poprawki; po niej blok valuation ASML będzie wyższy.

Tego, czego naprawić się nie da (free float ASML: brak drugiego źródła), program **nie ocenia**. Ticker dostaje wtedy:

- znak `!` w tabeli podsumowania i notatkę pod nią,
- czerwony napis **„! Możliwe błędne dane”** na wykresie, pod rekomendacją,
- w karcie tickera sekcję „! Możliwe błędne dane -- pominięte w ocenie” z wyjaśnieniem (co Yahoo podał i dlaczego to niemożliwe) oraz sekcję „Dane poprawione” z każdą przeliczoną wartością (Yahoo vs po przeliczeniu),
- kolumny `data_warnings` / `data_fixes` w CSV i pola `market.data_warnings` / `market.data_fixes` w JSON.

Wartość uznaje się za niemożliwą, gdy free float przekracza liczbę akcji, P/B lub P/S > 200, EV/EBITDA > 500, |FCF yield| > 50%, albo gdy waluty się różnią, a kursu lub składników do przeliczenia brak.

## Wymagania

- **Python 3.10+.** Domyślne „Local Shell (system Python)” w CatNip na tej maszynie to Python 3.5, który nie uruchomi bloków. Wybierz `.venv` / Python 3.10+.
- Pakiety (`requirements.txt`): `yfinance>=0.2.40`, `pandas>=2.0`, `numpy>=1.24`, `matplotlib>=3.7`, `chronos-forecasting>=2.0` (pociąga torch i transformers).
- Dostęp do internetu: Yahoo Finance oraz jednorazowe pobranie wag Chronos-2 z Hugging Face.
- GPU (CUDA) opcjonalne. Bez niego Chronos-2 działa na CPU, wolniej.

## Instalacja

```
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

W CatNip: w ustawieniach głównego bloku wybierz instalację pakietów **Manual** i wpisz `chronos-forecasting`. Automatyczna instalacja zamienia `import chronos` na niewłaściwy pakiet PyPI `chronos`.

## Uruchomienie

**W CatNip:** otwórz `StockAnalyser.catnip` i uruchom graf (blok główny: `Report`). Tickery i argumenty można podać w polu argumentów Run Engine (trafiają do `sys.argv`). Wykresy i tabela pojawiają się w zakładce Output.

**Z terminala:**

```
.venv/Scripts/python.exe main_1.py                       # tickery z bloku Settings
.venv/Scripts/python.exe main_1.py ASML NVDA --future 90 # wybrane tickery, prognoza 90 świec
.venv/Scripts/python.exe tools/run.py TSLA --horizon 1wk # odtwarza moduły z .catnip i uruchamia
```

`main_1.py` i pliki `<Blok>.py` w katalogu projektu są generowane z `.catnip`. Edytuj bloki w CatNip, a nie te pliki.

## Konfiguracja

| Argument / ustawienie | Znaczenie | Zakres / domyślnie |
| --- | --- | --- |
| tickery (argumenty pozycyjne) | symbole Yahoo, np. `ASML`, `SAP.DE`, `0700.HK`, `^GSPC`, `BTC-USD` | domyślnie lista w `Settings.__init__`; zmienna `STOCKANALYSER_TICKERS="A,B"` też działa; argument o niedozwolonej składni jest zgłaszany jako zignorowany; symbol poprawny składniowo, ale nieznany Yahoo, dostaje pustą analizę NO DATA |
| `--horizon` / `--interval` | szerokość świecy | `1m 2m 5m 15m 30m 60m 1h 90m 1d 5d 1wk 1mo 3mo`; domyślnie `1d`; inna wartość = błąd |
| `--lookback` / `--period` | ile historii pobrać | np. `6mo`, `2y`, `max`; domyślnie zależnie od interwału (`1d`: 2y); Yahoo ogranicza historię intraday |
| `--future` | ile świec naprzód prognozuje Chronos-2 | `0…512`; `0` wyłącza prognozę; domyślnie **90** (parametr `future_horizon` konstruktora `Settings` nadpisuje stałą `FUTURE_HORIZON = 30`) |
| `--weights` | wagi `technical,valuation,supply`, np. `0.6,0.3,0.1` | suma > 0, normalizowane; domyślnie zależne od interwału |
| `--candles` | ile świec rysować | domyślnie 180 |
| `--output` / `-o` | katalog wyników | domyślnie `output/` |
| `--no-chart` | bez wykresów | |
| `--no-backtest` | bez testu walk-forward | |
| `RISK_FREE_RATE` | próg dla wskaźników typu yield (FCF, dywidenda) | 0,04 |
| `COST_BPS` | koszt transakcji w backteście, w jedną stronę | 10 bp |
| `STOCKANALYSER_DEBUG=1` | pełne logi yfinance i tracebacki | |

## Wyniki

- tabela rankingowa w konsoli (najlepszy score na górze) i karta każdego tickera: score bloków, wagi i wkłady, backtest, prognoza (mediana, pasma, zmiana %), dane poprawione i możliwe błędne dane, po trzy najsilniejsze argumenty za i przeciw, uwagi o danych;
- **tickery bez danych nie są ukrywane.** Symbol, dla którego Yahoo nie zwraca świec (w domyślnej liście `FB2A` i `SMSN`), dostaje pustą analizę **NO DATA**: wiersz na końcu tabeli ze score `n/a` i DATA 0%, kartę z powodem i trzema blokami `brak danych`, pusty wykres z napisem „Brak danych” oraz wiersze w JSON/CSV. W terminalu pojawia się notatka z powodem i podpowiedzią, by sprawdzić symbol w Yahoo (np. sufiks giełdy `.DE`, `.KS`). Powtórzony ticker (w domyślnej liście dwa razy `MU`) jest analizowany raz;
- `output/<TICKER>_<interwał>.png` — wykres: świece + SMA 20/50/200 + Bollinger + prognoza, wolumen, RSI, MACD;
- `output/analysis.json` — wszystko, łącznie z każdym sygnałem; `output/analysis.csv` — jeden wiersz na ticker.

## Struktura projektu (bloki)

```
Score, Indicators ──> TechnicalAnalysis, ValuationAnalysis
Score             ──> SupplyAnalysis
Score, Indicators, TechnicalAnalysis, ValuationAnalysis, SupplyAnalysis ──> Recommendation
Score, TechnicalAnalysis ──> Backtest
Settings ──> PriceForecaster
Settings, MarketData, Recommendation, CandleChart, Backtest, PriceForecaster ──> Report (main)
PriceForecast — rekord danych (dataclass), bez połączeń
```

| Blok | Do czego służy |
| --- | --- |
| `Settings` | tickery, interwał, lookback, wagi bloków, progi rekomendacji, horyzont prognozy, argumenty wiersza poleceń |
| `Score` | wspólna skala −100…+100, klasy `Signal` i `Block`, pokrycie danych |
| `Indicators` | matematyka wskaźników w czystym pandas: SMA, EMA, RSI, MACD, Bollinger, ATR, ADX, OBV, stochastic, drawdown |
| `MarketData` | pobiera z Yahoo świece, fundamenty i historię liczby akcji; przelicza dane ze sprawozdań na walutę notowań i odrzuca wartości niemożliwe |
| `TechnicalAnalysis` | 11 sygnałów z wykresu → blok *technical* |
| `ValuationAnalysis` | 13 sygnałów wyceny i jakości → blok *valuation* |
| `SupplyAnalysis` | 8 sygnałów podaży akcji i akcjonariatu → blok *supply* |
| `Recommendation` | łączy trzy bloki w score, rekomendację i pokrycie danych; zbiera argumenty za i przeciw; dla tickera bez świec zwraca pusty werdykt NO DATA |
| `Backtest` | test walk-forward score technicznego: rank IC, strategia BUY-only vs buy & hold (do wejścia `Score` bloku `Report`) |
| `PriceForecaster` | ładuje Chronos-2 i liczy kwantyle przyszłych cen zamknięcia |
| `PriceForecast` | rekord danych z prognozą jednego tickera (mediana, pasma, `change_pct`) |
| `CandleChart` | rysuje czteropanelowy wykres PNG (z „! Możliwe błędne dane”, gdy trzeba; pusty wykres dla NO DATA) |
| `Report` | blok główny: uruchamia potok, drukuje raport, zapisuje JSON/CSV |

Każdy blok ma własną stronę dokumentacji (`<Blok>.md`), którą CatNip pokazuje w edytorze.

## Ograniczenia

- Wagi sygnałów i progi rekomendacji to rozsądne wartości domyślne, a nie parametry zoptymalizowane na danych.
- Backtest obejmuje tylko blok technical i zwrot **następnej świecy**. Nie mówi nic o horyzoncie 90 sesji z prognozy.
- Prognoza Chronos-2 nie jest jeszcze walidowana (patrz plan wyżej).
- Dane fundamentalne Yahoo bywają błędne, szczególnie dla ADR. Program przelicza waluty i odrzuca wartości niemożliwe (znak „!”), ale błąd mieszczący się w wiarygodnym zakresie przejdzie niezauważony.
- Prognozowane daty pomijają święta giełdowe, a dla intraday także godziny sesji.

## Licencja

Projekt nie ma licencji.
