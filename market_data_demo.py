"""Quick smoke test for the ``market_data`` helpers."""

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


def demo_cn_intraday_keltner():
    print("CN A-share (贵州茅台 600519) — 60m Keltner Channel")
    try:
        rows = market_data.get_cn_equity_intraday_kline(
            symbol="600519",
            start=date(2023, 1, 3),
            end=date(2023, 1, 10),
            adjust="qfq",
            period="60",
        )
    except ValueError as exc:
        print(f"Intraday fetch failed: {exc}")
        print()
        return

    if not rows:
        print("No intraday rows returned. The ticker may be suspended or data may be unavailable.")
        print()
        return

    keltner = market_data.compute_keltner_channels(rows, window=20, atr_multiplier=2.0)
    print(f"Rows fetched: {len(keltner)}")
    print(f"Most recent row: {keltner[-1] if keltner else 'N/A'}")
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
    demo_cn_intraday_keltner()


if __name__ == "__main__":
    main()