"""
Memo Parser & Field Extractor
Extracts structured payroll adjustment items from Japanese memos and text streams.
"""
import re
from typing import List, Dict, Any, Optional
from .models import PayrollAdjustmentItem

class MemoParser:
    """
    Parses unstructured and semi-structured Japanese adjustment notes.
    """
    
    # Regex patterns for key fields
    CASE_PATTERN = re.compile(r'([A-Z0-9]{2,4}-[0-9]{6,10}-[0-9]{2,4}|[A-Z0-9]{2,8}-[0-9]{3,6})')
    AMOUNT_PATTERN = re.compile(r'(?:金額|調整額|計)[：:\s]*([0-9,]+)\s*円?')
    STANDALONE_YEN_PATTERN = re.compile(r'([0-9,]+)\s*円')
    CATEGORY_PATTERN = re.compile(r'(?:給与備考控除申請|給与備考|費目|区分|項目)[：:\s]*([^\s\r\n。、]+)')
    EMPLOYEE_PATTERN = re.compile(r'(?:申請者|対象者|社員名|氏名|社員|氏)[：:\s]*([^\s\r\n。、]+(?:\s+[^\s\r\n。、]+)?)')
    
    @classmethod
    def parse_text(cls, raw_text: str, source_name: str = "memo.txt") -> List[PayrollAdjustmentItem]:
        """
        Parses a block of text containing one or more adjustment memos.
        """
        items = []
        # Split by potential multiple records or process line-by-line
        blocks = re.split(r'\n={3,}\n|\r?\n\r?\n', raw_text.strip())
        
        for idx, block in enumerate(blocks):
            if not block.strip():
                continue
            item = cls._parse_single_block(block.strip(), source_name, fallback_id=f"CASE-{idx+1:03d}")
            if item:
                items.append(item)
                
        return items

    @classmethod
    def _parse_single_block(cls, text: str, source_name: str, fallback_id: str) -> Optional[PayrollAdjustmentItem]:
        clean_text = text.replace('\r', '')
        
        # 1. Extract Case ID
        case_match = cls.CASE_PATTERN.search(clean_text)
        case_id = case_match.group(1) if case_match else fallback_id
        
        # 2. Extract Amount
        amount = 0.0
        amt_match = cls.AMOUNT_PATTERN.search(clean_text)
        if amt_match:
            amount = float(amt_match.group(1).replace(',', ''))
        else:
            yen_match = cls.STANDALONE_YEN_PATTERN.search(clean_text)
            if yen_match:
                amount = float(yen_match.group(1).replace(',', ''))
                
        # 3. Extract Category / 費目
        cat_match = cls.CATEGORY_PATTERN.search(clean_text)
        if cat_match:
            category = cat_match.group(1).strip()
        else:
            # Fallback categories based on keywords
            if "出張旅費" in clean_text or "旅費" in clean_text:
                category = "出張旅費"
            elif "時間外手当" in clean_text or "残業" in clean_text:
                category = "時間外手当"
            elif "控除" in clean_text:
                category = "控除調整"
            elif "棚卸" in clean_text or "在庫" in clean_text:
                category = "在庫調整"
            elif "機器" in clean_text or "IT" in clean_text:
                category = "機器手当"
            else:
                category = "一般給与調整"
                
        # 4. Extract Employee / 申請者
        emp_match = cls.EMPLOYEE_PATTERN.search(clean_text)
        emp_name = emp_match.group(1).strip() if emp_match else "社内担当"
        
        # 5. Check rule confirmation (規程内確認)
        rule_confirmed = bool(
            "規程内であることを確認" in clean_text or 
            "規程内確認" in clean_text or 
            "確認済み" in clean_text or
            "承認済" in clean_text
        )
        
        # 6. Clean note body for submission
        # Extract meaningful sentence or format standard note
        sentences = [s.strip() for s in clean_text.splitlines() if s.strip()]
        remark = " / ".join(sentences)
        
        return PayrollAdjustmentItem(
            case_id=case_id,
            employee_name_or_id=emp_name,
            category=category,
            amount=amount,
            rule_confirmed=rule_confirmed,
            remark=remark,
            source_memo=source_name,
            raw_text=clean_text
        )

    @classmethod
    def parse_structured_dict(cls, data: Dict[str, Any], source_name: str = "json_feed") -> PayrollAdjustmentItem:
        """
        Parses structured dictionary directly from API or JSON feed.
        """
        return PayrollAdjustmentItem(
            case_id=data.get("case_id", "GEN-001"),
            employee_name_or_id=data.get("employee", data.get("employee_name", "社内担当")),
            category=data.get("category", "給与備考調整"),
            amount=float(data.get("amount", 0.0)),
            rule_confirmed=bool(data.get("rule_confirmed", data.get("confirmed", True))),
            remark=data.get("remark", data.get("note", "")),
            source_memo=source_name,
            raw_text=str(data)
        )


def parse_memo(raw_text: str) -> Optional[PayrollAdjustmentItem]:
    """Convenience functional wrapper for parsing a memo text block."""
    items = MemoParser.parse_text(raw_text)
    return items[0] if items else None
