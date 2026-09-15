"""
Business Rule Engine & Risk Validation
Implements compliance checks, anomaly detection, and human-in-the-loop routing.
"""
from typing import Set, Tuple
from .models import PayrollAdjustmentItem, ValidationResult

class BusinessRuleEngine:
    """
    Validates items against enterprise financial controls.
    """
    
    def __init__(self, high_value_threshold: float = 100000.0):
        self.high_value_threshold = high_value_threshold
        self.processed_cases: Set[str] = set()

    def validate(self, item: PayrollAdjustmentItem) -> ValidationResult:
        flags = []
        
        # Rule 1: Case ID check
        if not item.case_id or item.case_id.strip() == "":
            return ValidationResult(is_valid=False, status="REJECTED", flags=["MISSING_CASE_ID"], confidence=0.0)
            
        # Rule 2: Duplicate check
        if item.case_id in self.processed_cases:
            flags.append("DUPLICATE_CASE_ID")
            return ValidationResult(is_valid=False, status="REJECTED", flags=flags, confidence=0.0)
            
        # Rule 3: Valid positive amount
        if item.amount < 0:
            flags.append("NEGATIVE_AMOUNT")
            return ValidationResult(is_valid=False, status="REJECTED", flags=flags, confidence=0.0)
            
        # Rule 4: Zero amount check
        if item.amount == 0.0 and item.category not in ["在庫調整", "ステータス更新"]:
            flags.append("ZERO_AMOUNT_WARNING")
            
        # Rule 5: High Value Anomaly Detection (Requires Human Approval)
        if item.amount > self.high_value_threshold:
            flags.append(f"HIGH_VALUE_THRESHOLD_EXCEEDED(>{self.high_value_threshold:,.0f}JPY)")
            
        # Rule 6: Internal Compliance / Policy confirmation
        if not item.rule_confirmed:
            flags.append("POLICY_COMPLIANCE_UNCONFIRMED")
            
        # Final status decision
        if flags:
            return ValidationResult(is_valid=True, status="FLAGGED_FOR_REVIEW", flags=flags, confidence=0.85)
            
        return ValidationResult(is_valid=True, status="AUTO_APPROVED", flags=[], confidence=1.0)

    def register_processed(self, case_id: str):
        self.processed_cases.add(case_id)
