"""
Data Models for Payroll Adjustment Automation
"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from datetime import datetime, timezone

@dataclass
class PayrollAdjustmentItem:
    case_id: str
    employee_name_or_id: str
    category: str
    amount: float
    rule_confirmed: bool
    remark: str
    source_memo: str
    raw_text: str
    currency: str = "JPY"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self):
        return asdict(self)

@dataclass
class ValidationResult:
    is_valid: bool
    status: str  # AUTO_APPROVED, FLAGGED_FOR_REVIEW, REJECTED
    flags: List[str] = field(default_factory=list)
    confidence: float = 1.0

    def to_dict(self):
        return asdict(self)

@dataclass
class SyncResult:
    case_id: str
    success: bool
    status: str
    transaction_id: Optional[str] = None
    portal_status_code: int = 200
    message: str = "Success"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    time_saved_sec: float = 33.0  # Based on empirical Dataset B median of 33.0s

    def to_dict(self):
        return asdict(self)
