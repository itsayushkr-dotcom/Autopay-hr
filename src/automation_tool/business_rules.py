"""
Business Rule Engine & Risk Validation
Implements compliance checks, anomaly detection, routine vs adjustment guards,
and enterprise circuit-breaker fault isolation.
"""
from typing import Set, Tuple, List, Optional
import os
import re
from .models import PayrollAdjustmentItem, ValidationResult


class CircuitBreakerTrippedException(Exception):
    """Raised when consecutive failure threshold is exceeded, halting automated execution."""
    pass


class CircuitBreaker:
    """
    Automated safety circuit breaker preventing cascading portal corruption
    upon DOM drift, network failure, or systemic data format changes.
    """
    def __init__(self, max_consecutive_failures: int = 3):
        self.max_consecutive_failures = max_consecutive_failures
        self.consecutive_failures = 0
        self.state = "CLOSED"  # CLOSED (Normal), TRIPPED (Halted)
        self.trip_reason: Optional[str] = None

    def record_success(self):
        """Reset consecutive failure counter upon a verified success."""
        self.consecutive_failures = 0

    def record_failure(self, reason: str = "Execution error"):
        """Increment failure counter and trip circuit breaker if threshold is reached."""
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.max_consecutive_failures:
            self.state = "TRIPPED"
            self.trip_reason = (
                f"Circuit breaker TRIPPED after {self.consecutive_failures} "
                f"consecutive failures: {reason}"
            )
            raise CircuitBreakerTrippedException(self.trip_reason)

    def is_tripped(self) -> bool:
        return self.state == "TRIPPED"

    def reset(self):
        self.consecutive_failures = 0
        self.state = "CLOSED"
        self.trip_reason = None


class BusinessRuleEngine:
    """
    Validates items against enterprise financial controls, empirical routine guards,
    and circuit breaker protections.
    """
    
    def __init__(self, high_value_threshold: float = 100000.0, max_consecutive_failures: int = 3):
        self.high_value_threshold = high_value_threshold
        self.processed_cases: Set[str] = set()
        self.circuit_breaker = CircuitBreaker(max_consecutive_failures=max_consecutive_failures)

    def validate(self, item: PayrollAdjustmentItem) -> ValidationResult:
        if self.circuit_breaker.is_tripped():
            return ValidationResult(
                is_valid=False,
                status="REJECTED",
                flags=[f"CIRCUIT_BREAKER_TRIPPED: {self.circuit_breaker.trip_reason}"],
                confidence=0.0
            )

        flags = []
        
        # Rule 1: Case ID check
        if not item.case_id or item.case_id.strip() == "":
            flags.append("MISSING_CASE_ID")
            return ValidationResult(is_valid=False, status="REJECTED", flags=flags, confidence=0.0)
            
        # Rule 2: Duplicate check
        if item.case_id in self.processed_cases:
            flags.append("DUPLICATE_CASE_ID")
            return ValidationResult(is_valid=False, status="REJECTED", flags=flags, confidence=0.0)
            
        # Rule 3: Valid positive amount
        if item.amount < 0:
            flags.append("NEGATIVE_AMOUNT")
            return ValidationResult(is_valid=False, status="REJECTED", flags=flags, confidence=0.0)
            
        # Rule 4: Zero amount check
        if item.amount == 0.0 and item.category not in ["控除整備", "資格取得補助"]:
            flags.append("ZERO_AMOUNT_WARNING")

        # Rule 5: Empirical Routine vs Adjustment Guard (種別: 定常 vs 調整)
        # In corporate telemetry, only 定常 (Routine) can complete unattended.
        # 調整 (Adjustment) cases MUST be escalated to human reviewers with pre-filled notes.
        if getattr(item, "classification", "定常") == "調整":
            flags.append("DISCRETIONARY_ADJUSTMENT_REQUIRES_HUMAN_REVIEW(種別:調整)")
            
        # Rule 6: High Value Anomaly Detection (Requires Human Approval)
        if item.amount > self.high_value_threshold:
            flags.append(f"HIGH_VALUE_THRESHOLD_EXCEEDED(>{self.high_value_threshold:,.0f}JPY)")
            
        # Rule 7: Internal Compliance / Policy confirmation
        if not item.rule_confirmed:
            flags.append("POLICY_COMPLIANCE_UNCONFIRMED")
            
        # Final status decision
        if flags:
            return ValidationResult(is_valid=True, status="FLAGGED_FOR_REVIEW", flags=flags, confidence=0.85)
            
        return ValidationResult(is_valid=True, status="AUTO_APPROVED", flags=[], confidence=1.0)

    def register_processed(self, case_id: str):
        self.processed_cases.add(case_id)
        self.circuit_breaker.record_success()

    def mark_processed(self, case_id: str):
        self.register_processed(case_id)


def validate_case(item: PayrollAdjustmentItem) -> ValidationResult:
    engine = BusinessRuleEngine()
    return engine.validate(item)


def load_procedure(name: str = "payroll_items") -> dict:
    """
    Loads declarative process specification YAML file from procedures directory.
    Fallback to built-in dictionary if pyyaml is not installed.
    """
    proc_dir = os.path.join(os.path.dirname(__file__), "procedures")
    yaml_file = os.path.join(proc_dir, f"{name}.yaml")
    
    if os.path.exists(yaml_file):
        try:
            import yaml
            with open(yaml_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception:
            pass
            
    # Built-in specification for payroll_items
    return {
        "process": "payroll_items",
        "process_ja": "給与備考・控除整備",
        "case_prefixes": ["P4", "P1", "CASE"],
        "system": "HR",
        "route": "payroll-items",
        "evidence": {
            "observed_executions": 93,
            "share_of_total_time_pct": 36.3,
            "routine_share": 0.88,
            "adjustment_share": 0.12
        },
        "guard": {
            "automate_when": {"column": "種別", "equals": "定常", "max_amount_jpy": 100000},
            "escalate_when": {"column": "種別", "equals": "調整", "amount_exceeds_jpy": 100000},
            "circuit_breaker": {"stop_after_consecutive_failures": 3}
        },
        "selectors": {
            "table": "#pi-table",
            "row_by_case": "#rt-row-{case_id}",
            "note_input": "#pi-note",
            "confirm_button": "#btn-pi-ok"
        }
    }
