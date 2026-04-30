from enum import StrEnum


class AssetType(StrEnum):
    ETF = "etf"
    STOCK = "stock"
    PUBLIC_FUND = "public_fund"


class ProviderName(StrEnum):
    AKSHARE = "akshare"
    TUSHARE = "tushare"


class AdjustmentMode(StrEnum):
    NONE = ""
    QFQ = "qfq"
    HFQ = "hfq"


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class NonTradingDayPolicy(StrEnum):
    FAIL = "fail"
    SKIP = "skip"
    NEXT = "next"


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    SUCCEEDED_WITH_WARNINGS = "succeeded_with_warnings"
    FAILED = "failed"
