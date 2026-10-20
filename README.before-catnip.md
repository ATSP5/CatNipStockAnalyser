# StockAnalyser

Give it a list of tickers and it gives back **STRONG BUY / BUY / HOLD / SELL / STRONG SELL**, with a candlestick chart and the reasoning behind every call.

IMPORTANT! NEVER TREAT THIS AS ADVISE IN REAL INVESTMENTS! IT IS NOT MENT TO BE INVESTITION ADVICE, ALLWAYS VALIDATE RESULTS AND CONSULT EXPERTS!

The verdict comes from three independent views on each ticker:

| View | Weight | What it asks |
| --- | --- | --- |
| **Supply** | 20% | How many shares exist, and is that number growing or shrinking? |
| **Valuation** | 35% | Is the price high or low — against the business, and against its own history? |
| **Technical** | 45% | What is the chart doing right now? |

Each produces a score from `-100` to `+100`; the weighted composite lands in one of five bands.

## Running it

**From CatNip** — open `StockAnalyser.catnip` and press Run. Set the tickers either by editing `TICKERS` in the **Settings** block or by typing them into the Run Engine's script arguments, which arrive as `sys.argv` exactly like command-line arguments. Charts and the summary table appear in the **Output** tab.

**From a terminal** — `run.py` re-derives the block modules from the project file and runs the main block the same way CatNip does, so it can never drift out of step with the canvas:

```
python run.py                             # the tickers saved on the canvas
python run.py AAPL MSFT NVDA              # override them
python run.py TSLA --horizon 1wk          # weekly candles
python run.py KO --horizon 1h --no-chart  # hourly, skip the chart
```

| Argument | Meaning |
| --- | --- |
| *(positional)* | Tickers. Yahoo symbols, so `0700.HK`, `SAP.DE`, `^GSPC` and `BTC-USD` all work |
| `--horizon` | Candle width. **Default `1d`** |
| `--lookback` | How far back to fetch (`6mo`, `2y`, `max`). Defaults per horizon |
| `--weights` | `technical,valuation,supply`, e.g. `0.6,0.3,0.1`. Pins the weights; by default they follow the horizon (1d: 90/10/0) |
| `--candles` | How many candles to draw (default 180) |
| `--output` | Where charts and files go (default `output/`) |
| `--no-chart` | Skip chart rendering |
| `--no-backtest` | Skip the walk-forward backtest |

`STOCKANALYSER_TICKERS="AAPL,MSFT"` works too. `STOCKANALYSER_DEBUG=1` restores yfinance's own logging and prints full tracebacks.

## The candle horizon

The horizon is the width of a single candle, and **the default is `1d`** — one candle per trading day.

```
1m  2m  5m  15m  30m  60m  1h  90m      intraday
1d  5d  1wk  1mo  3mo                   daily and longer
```

Every indicator window is counted in *candles*, so the horizon is what decides the timeframe being judged: a 50-candle average means fifty days at `1d` and fifty hours at `1h`. Each horizon carries its own sensible lookback, and Yahoo's caps on intraday history are respected (a minute chart cannot reach back beyond seven days).

Intraday runs also fetch two years of daily candles in the background, so a 5-minute chart still knows where its 52-week range sits.

## Output

A ranked table, best call first:

```
    TICKER   CALL           SCORE   CONF     TECH VALUATION   SUPPLY
--------------------------------------------------------------------
+   NVDA     BUY            +23.5   100%    +27.8      -4.5    +62.7
=   KO       HOLD           +14.6   100%    +31.9     -33.6    +60.2
```

Then a card per ticker with each block's score, the three strongest arguments each way, and the reasoning:

```
  Supporting a buy:
      +96  Share count trend (supply)  -4.73% over the past year -- buying back stock
      +58  Trend vs moving averages    +2.4% vs SMA50, +12.7% vs SMA200, golden cross
  Arguing against:
     -100  PEG ratio (valuation)       2.47 (near 1.0 is priced fairly for its growth)
```

Plus `output/<TICKER>_<horizon>.png`, `output/analysis.json` (complete, every signal) and `output/analysis.csv` (one row per ticker).

## Reading the result

**Expect the blocks to disagree.** A stock at the top of its 52-week range on a strong uptrend scores well technically and badly on valuation. The HOLD that comes out is the honest answer, not a failure to decide — the interesting cases are where all three agree.

**Watch the data coverage figure.** It reports how much of the intended evidence actually arrived, not how likely the call is to be right. A fully covered HOLD and a HOLD that had nothing to work with are very different statements.

**Check the backtest before trusting a BUY.** Each card shows the technical score's rank IC against the next candle's return, plus a long-on-BUY strategy (after costs) against buy & hold. An IC near zero, or a strategy that trails buy & hold, means the call carries no edge.

**The reason list is ranked by weighted contribution**, not raw score, so a moderate reading on a heavy signal can outrank an extreme reading on a light one. That is why the printed numbers are not always in descending order.

## The graph

```
Settings ─────────────────────────────────────────────┐
Score ──────┬─────┬─────┬──────────────┐              │
Indicators ─┼─────┼─────┼──────────────┤              │
            │     │     │              │              │
   TechnicalAnalysis    │              │              │
   ValuationAnalysis ───┼──> Recommendation ──> Report (main)
   SupplyAnalysis ──────┘              │              │
                          MarketData ──┴──────────────┤
                          CandleChart ────────────────┘
```

| Block | Role |
| --- | --- |
| `Settings` | Tickers, horizon, weights, output paths |
| `Score` | The `-100..+100` scale, `Signal` and `Block` |
| `Indicators` | RSI, MACD, Bollinger, ATR, ADX, OBV, stochastic — pure pandas |
| `MarketData` | Fetches candles, fundamentals and share count history |
| `TechnicalAnalysis` | 11 signals on the chart |
| `ValuationAnalysis` | 13 signals on price and quality |
| `SupplyAnalysis` | 8 signals on share count and ownership |
| `Recommendation` | Weights the three into one call |
| `Backtest` | Walk-forward IC and long-on-BUY vs buy & hold for the technical score |
| `CandleChart` | The four-panel PNG |
| `Report` | Runs everything and prints it |

Each block has a documentation page (`Settings.md`, `Score.md`, …) that CatNip shows in the editor.

CatNip compiles a program from the main block plus everything upstream of it: each block is written out as `<Name>.py` beside the project, that folder goes on `sys.path`, and the main block runs as `__main__`. **Blocks reach each other by ordinary Python import**, so every block that uses another imports it at the top — `Recommendation` opens with `from Score import Score`, and so on. The wires on the canvas describe that same dependency structure.

The `.py` files in the project root are generated from the `.catnip` and are overwritten on every save and every `run.py`; edit the blocks, not those files.

## Setup

Dependencies are `yfinance`, `pandas`, `numpy` and `matplotlib` — a virtual environment is already set up in `.venv`:

```
.venv/Scripts/python.exe run.py AAPL
```

To recreate it:

```
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

> **Note:** the blocks need **Python 3.10+**. CatNip's default *Local Shell (system Python)* on this machine resolves to Python 3.5, which cannot run them — pick **Python 3.10** or **venv:3.10** as the environment before running the graph.

## Scope

This scores public data mechanically. It has no view on news, filings, guidance or anything else that is not in a price series or a Yahoo fundamentals field, and the weights and thresholds are reasonable defaults rather than tuned parameters. The built-in backtest covers only the technical block, because fundamentals are a current snapshot that cannot be replayed without look-ahead. Treat the output as a structured starting point for your own research, not as investment advice.
