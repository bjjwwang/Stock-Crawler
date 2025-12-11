"""Quick smoke test for the ``market_data`` helpers.

Run inside an activated backend virtualenv after installing ``requirements.txt``:

    python backend/examples/market_data_demo.py
"""

from datetime import date

import market_data


def demo_cn():
    print("CN A-share (贵州茅台 600519) — daily, qfq adjusted")
    rows = market_data.get_cn_equity_kline(
        symbol="600519",
        start=date(2023, 1, 3),
        end=date(2023, 1, 10),
        adjust="qfq",
        period="daily",
    )
    print(f"Rows fetched: {len(rows)}")
    print(f"First row: {rows[0] if rows else 'N/A'}")
    print()


def demo_us():
    print("US equity (AAPL) — daily, regular hours")
    rows = market_data.get_us_equity_kline(
        symbol="AAPL",
        start=date(2023, 1, 3),
        end=date(2023, 1, 10),
        interval="1d",
        prepost=False,
    )
    print(f"Rows fetched: {len(rows)}")
    print(f"First row: {rows[0] if rows else 'N/A'}")
    print()


def main():
    demo_cn()
    demo_us()


if __name__ == "__main__":
    main()