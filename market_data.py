"""Utilities for fetching K-line (candlestick) data for equities.

This module focuses on common stock tickers in Chinese A-shares and
U.S. markets while avoiding derivative instruments such as indices,
ETFs, or options.
"""
from __future__ import annotations

from datetime import date
from typing import Iterable, Literal, Optional

import akshare as ak
import pandas as pd
import yfinance as yf


KLINE_SCHEMA = ["date", "open", "close", "high", "low", "volume"]


def _normalize_date(value: date | str) -> str:
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return value


def _records_from_dataframe(df: pd.DataFrame, column_map: dict[str, str]) -> list[dict[str, float | str]]:
    if df is None or df.empty:
        return []

    missing = [col for col in column_map if col not in df.columns]
    if missing:
        raise ValueError(
            "Upstream data is missing expected columns: "
            f"{missing}. Available columns: {list(df.columns)}"
        )

    renamed = df.rename(columns=column_map)
    renamed = renamed[list(column_map.values())]
    renamed[KLINE_SCHEMA[0]] = renamed[KLINE_SCHEMA[0]].astype(str)
    return renamed.to_dict(orient="records")


def _reject_non_equity(symbol: str) -> None:
    # Simple filter to avoid common derivative tickers.
    disallowed_markers: Iterable[str] = {"=", "^", ".P", ".W", "-P", "-W"}
    if any(marker in symbol for marker in disallowed_markers):
        raise ValueError(f"Symbol '{symbol}' looks like a derivative instrument; provide a common stock ticker instead.")


def _to_dataframe(records: list[dict[str, float | str]]) -> pd.DataFrame:
    return pd.DataFrame.from_records(records)


def _ensure_sorted_by_date(df: pd.DataFrame) -> pd.DataFrame:
    if "date" not in df.columns:
        return df
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date")


def get_cn_equity_kline(
    symbol: str,
    start: date | str,
    end: date | str,
    adjust: Literal["qfq", "hfq", ""] = "qfq",
    period: Literal["daily", "weekly", "monthly"] = "daily",
) -> list[dict[str, float | str]]:
    """Fetch A-share K-line data using `akshare`.

    Args:
        symbol: Six-digit stock code (e.g., "600519" for 贵州茅台).
        start: Start date as ``YYYY-MM-DD`` or :class:`datetime.date`.
        end: End date as ``YYYY-MM-DD`` or :class:`datetime.date`.
        adjust: Price adjustment method; empty string keeps raw prices.
        period: K-line granularity supported by ``akshare``.

    Returns:
        A list of dictionaries with standardized K-line keys.
    """
    _reject_non_equity(symbol)
    start_str, end_str = _normalize_date(start), _normalize_date(end)

    raw = ak.stock_zh_a_hist(
        symbol=symbol,
        period=period,
        start_date=start_str.replace("-", ""),
        end_date=end_str.replace("-", ""),
        adjust=adjust,
    )

    column_map = {
        "日期": "date",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
    }

    return _records_from_dataframe(raw, column_map)


def get_cn_equity_intraday_kline(
    symbol: str,
    start: Optional[date | str] = None,
    end: Optional[date | str] = None,
    adjust: Literal["qfq", "hfq", "bfq"] = "qfq",
    period: Literal["1", "5", "15", "30", "60"] = "60",
) -> list[dict[str, float | str]]:
    """Fetch intraday A-share K-line data (e.g., 60-minute bars) using `akshare`.

    Args:
        symbol: Six-digit stock code (e.g., "600519" for 贵州茅台).
        start: Optional start datetime (inclusive) in ``YYYY-MM-DD`` or :class:`datetime.date`.
        end: Optional end datetime (inclusive) in ``YYYY-MM-DD`` or :class:`datetime.date`.
        adjust: Price adjustment method; ``bfq`` leaves prices unadjusted.
        period: Minute granularity supported by ``akshare`` ("1", "5", "15", "30", "60").

    Returns:
        A list of dictionaries with standardized K-line keys.
    """

    _reject_non_equity(symbol)
    raw = ak.stock_zh_a_minute(symbol=symbol, period=period, adjust=adjust)

    column_map = {
        "day": "date",
        "open": "open",
        "close": "close",
        "high": "high",
        "low": "low",
        "volume": "volume",
    }

    records = _records_from_dataframe(raw, column_map)
    if not records:
        return []

    df = _ensure_sorted_by_date(_to_dataframe(records))

    if start:
        start_ts = pd.to_datetime(_normalize_date(start))
        df = df[df["date"] >= start_ts]
    if end:
        end_ts = pd.to_datetime(_normalize_date(end))
        df = df[df["date"] <= end_ts]

    df["date"] = df["date"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df.to_dict(orient="records")


def compute_keltner_channels(
    kline_records: list[dict[str, float | str]],
    window: int = 20,
    atr_multiplier: float = 2.0,
) -> list[dict[str, float | str]]:
    """Compute Keltner Channel ("薛斯通道") values from OHLCV records.

    The function returns a time series with the original OHLCV fields plus:
    - ``middle``: EMA of the typical price over ``window`` periods.
    - ``atr``: Average True Range over ``window`` periods.
    - ``upper`` and ``lower``: Channel bands using ``atr_multiplier``.
    """

    if not kline_records:
        return []

    df = _ensure_sorted_by_date(_to_dataframe(kline_records))
    if "open" not in df or "high" not in df or "low" not in df or "close" not in df:
        raise ValueError("K-line records must include open, high, low, and close prices.")

    typical_price = (df["high"] + df["low"] + df["close"]) / 3.0
    df["middle"] = typical_price.ewm(span=window, adjust=False).mean()

    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr"] = true_range.rolling(window=window, min_periods=1).mean()

    df["upper"] = df["middle"] + atr_multiplier * df["atr"]
    df["lower"] = df["middle"] - atr_multiplier * df["atr"]

    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    return df.to_dict(orient="records")


def get_us_equity_kline(
    symbol: str,
    start: date | str,
    end: date | str,
    interval: Literal["1d", "1wk", "1mo"] = "1d",
    prepost: Optional[bool] = False,
) -> list[dict[str, float | str]]:
    """Fetch U.S. equity K-line data using `yfinance`.

    Args:
        symbol: Yahoo Finance ticker (e.g., "AAPL" or "MSFT").
        start: Start date as ``YYYY-MM-DD`` or :class:`datetime.date`.
        end: End date as ``YYYY-MM-DD`` or :class:`datetime.date`.
        interval: K-line granularity supported by Yahoo Finance.
        prepost: Include pre/post market data when ``True``.

    Returns:
        A list of dictionaries with standardized K-line keys.
    """
    _reject_non_equity(symbol)
    start_str, end_str = _normalize_date(start), _normalize_date(end)

    history = yf.Ticker(symbol).history(start=start_str, end=end_str, interval=interval, prepost=prepost)
    history = history.rename_axis("date").reset_index()

    column_map = {
        "date": "date",
        "Open": "open",
        "Close": "close",
        "High": "high",
        "Low": "low",
        "Volume": "volume",
    }

    return _records_from_dataframe(history, column_map)


def get_us_equity_intraday_kline(
    symbol: str,
    start: date | str,
    end: date | str,
    interval: Literal[
        "1m",
        "2m",
        "5m",
        "15m",
        "30m",
        "60m",
        "90m",
    ] = "60m",
    prepost: Optional[bool] = False,
) -> list[dict[str, float | str]]:
    """Fetch intraday U.S. equity K-line data (e.g., 60-minute bars) using `yfinance`.

    Args:
        symbol: Yahoo Finance ticker (e.g., "AAPL" or "MSFT").
        start: Start date as ``YYYY-MM-DD`` or :class:`datetime.date`.
        end: End date as ``YYYY-MM-DD`` or :class:`datetime.date`.
        interval: Minute granularity supported by Yahoo Finance (default "60m").
        prepost: Include pre/post market data when ``True``.

    Returns:
        A list of dictionaries with standardized K-line keys.
    """
    _reject_non_equity(symbol)
    start_str, end_str = _normalize_date(start), _normalize_date(end)

    history = yf.Ticker(symbol).history(
        start=start_str,
        end=end_str,
        interval=interval,
        prepost=prepost,
    )
    history = history.rename_axis("date").reset_index()

    column_map = {
        "date": "date",
        "Open": "open",
        "Close": "close",
        "High": "high",
        "Low": "low",
        "Volume": "volume",
    }

    records = _records_from_dataframe(history, column_map)
    df = _ensure_sorted_by_date(_to_dataframe(records))
    df["date"] = df["date"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df.to_dict(orient="records")


__all__ = [
    "get_cn_equity_kline",
    "get_us_equity_kline",
    "get_cn_equity_intraday_kline",
    "get_us_equity_intraday_kline",
    "compute_keltner_channels",
    "KLINE_SCHEMA",
]