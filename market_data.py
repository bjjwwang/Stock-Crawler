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
    renamed = df.rename(columns=column_map)
    renamed = renamed[list(column_map.values())]
    renamed[KLINE_SCHEMA[0]] = renamed[KLINE_SCHEMA[0]].astype(str)
    return renamed.to_dict(orient="records")


def _reject_non_equity(symbol: str) -> None:
    # Simple filter to avoid common derivative tickers.
    disallowed_markers: Iterable[str] = {"=", "^", ".P", ".W", "-P", "-W"}
    if any(marker in symbol for marker in disallowed_markers):
        raise ValueError(f"Symbol '{symbol}' looks like a derivative instrument; provide a common stock ticker instead.")


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


__all__ = [
    "get_cn_equity_kline",
    "get_us_equity_kline",
    "KLINE_SCHEMA",
]