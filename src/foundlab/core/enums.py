from enum import Enum


class AssetType(str, Enum):
    ETF = "etf"
    STOCK = "stock"
    PUBLIC_FUND = "public_fund"


class ProviderName(str, Enum):
    AKSHARE = "akshare"
    TUSHARE = "tushare"


class AdjustmentMode(str, Enum):
    NONE = ""
    QFQ = "qfq"
    HFQ = "hfq"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class NonTradingDayPolicy(str, Enum):
    FAIL = "fail"
    SKIP = "skip"
    NEXT = "next"


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    SUCCEEDED_WITH_WARNINGS = "succeeded_with_warnings"
    FAILED = "failed"
