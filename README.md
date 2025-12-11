# Stock-Crawler

Utilities for fetching K-line (candlestick) data for Chinese A-shares and U.S. equities. The project wraps
[akshare](https://github.com/akfamily/akshare) and [yfinance](https://github.com/ranaroussi/yfinance) to provide
standardized records for downstream processing.

## Features
- Fetch Chinese A-share K-line data with configurable price adjustment (qfq/hfq) and period granularity.
- Fetch U.S. equity OHLCV data with daily/weekly/monthly-like intervals and optional pre/post market inclusion.
- Return normalized records using a consistent schema: `date`, `open`, `close`, `high`, `low`, `volume`.

## Project Structure
- `market_data.py`: Core helpers for fetching and normalizing data from Akshare (CN) and Yahoo Finance (US).
- `market_data_demo.py`: Simple script showing how to call the helpers for both markets.
- `requirements.txt`: Runtime dependencies.

## Installation
1. Create and activate a virtual environment (optional but recommended).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
The quickest way to see the helpers in action is to run the demo script:
```bash
python market_data_demo.py
```
It will fetch a small sample for both 贵州茅台 (`600519`) and Apple (`AAPL`) and print the number of rows and the
first record for each query.

You can also call the helpers directly in your own code:

```python
from datetime import date
from market_data import get_cn_equity_kline, get_us_equity_kline

cn_rows = get_cn_equity_kline(
    symbol="600519",  # 贵州茅台
    start=date(2023, 1, 3),
    end=date(2023, 1, 10),
    adjust="qfq",
    period="daily",
)

us_rows = get_us_equity_kline(
    symbol="AAPL",
    start=date(2023, 1, 3),
    end=date(2023, 1, 10),
    interval="1d",
    prepost=False,
)
```

Both functions return a list of dictionaries using the shared `KLINE_SCHEMA`. Columns are normalized to English
keys and dates are stringified for consistency.

## Notes
- The helpers intentionally reject common derivative markers (e.g., indices or warrants). Provide common stock
  tickers only.
- Network connectivity is required to retrieve data from the upstream APIs.
