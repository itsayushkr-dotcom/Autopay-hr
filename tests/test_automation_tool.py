"""
Automated Test Suite for AutoPay-HR
Verifies parser accuracy, business rule validation, anomaly detection, and portal integration.
"""
import unittest
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from automation_tool.models import PayrollAdjustmentItem
from automation_tool.memo_parser import MemoParser
from automation_tool.business_rules import BusinessRuleEngine
from automation_tool.mock_portal_server import start_portal_server
from automation_tool.portal_client import PortalClient

class TestAutoPayTool(unittest.TestCase):
    
    def setUp(self):
        self.engine = BusinessRuleEngine(high_value_threshold=100000.0)

    def test_memo_parser_extraction(self):
        sample_text = """
        精算確認メモ
        P1-07080388-002
        申請者：田中 麻里
        経費精算確認済み。費目：出張旅費 金額：35,241円。規程内であることを確認した。
        """
        items = MemoParser.parse_text(sample_text)
        self.assertEqual(len(items), 1)
        item = items[0]
        
        self.assertEqual(item.case_id, "P1-07080388-002")
        self.assertEqual(item.employee_name_or_id, "田中 麻里")
        self.assertEqual(item.category, "出張旅費")
        self.assertEqual(item.amount, 35241.0)
        self.assertTrue(item.rule_confirmed)

    def test_business_rules_auto_approval(self):
        item = PayrollAdjustmentItem(
            case_id="TEST-001",
            employee_name_or_id="山田 太郎",
            category="時間外手当",
            amount=45000.0,
            rule_confirmed=True,
            remark="残業代調整",
            source_memo="test",
            raw_text="test"
        )
        res = self.engine.validate(item)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.status, "AUTO_APPROVED")
        self.assertEqual(len(res.flags), 0)

    def test_business_rules_high_value_anomaly(self):
        item = PayrollAdjustmentItem(
            case_id="TEST-002",
            employee_name_or_id="社長 太郎",
            category="役員手当",
            amount=250000.0,  # Exceeds 100k
            rule_confirmed=True,
            remark="高額手当",
            source_memo="test",
            raw_text="test"
        )
        res = self.engine.validate(item)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.status, "FLAGGED_FOR_REVIEW")
        self.assertTrue(any("HIGH_VALUE" in f for f in res.flags))

    def test_business_rules_duplicate_rejection(self):
        item = PayrollAdjustmentItem(
            case_id="DUP-001",
            employee_name_or_id="テスト社員",
            category="一般調整",
            amount=10000.0,
            rule_confirmed=True,
            remark="初回申請",
            source_memo="test",
            raw_text="test"
        )
        res1 = self.engine.validate(item)
        self.assertEqual(res1.status, "AUTO_APPROVED")
        self.engine.register_processed(item.case_id)
        
        # Second submission of same case
        res2 = self.engine.validate(item)
        self.assertFalse(res2.is_valid)
        self.assertEqual(res2.status, "REJECTED")
        self.assertIn("DUPLICATE_CASE_ID", res2.flags)

    def test_portal_client_live_sync(self):
        # Start local mock portal
        server = start_portal_server(port=5136)
        client = PortalClient(base_url="http://127.0.0.1:5136")
        
        item = PayrollAdjustmentItem(
            case_id="SYNC-TEST-001",
            employee_name_or_id="同期 テスト",
            category="出張旅費",
            amount=12000.0,
            rule_confirmed=True,
            remark="自動テスト案件",
            source_memo="test",
            raw_text="test"
        )
        sync = client.sync_item(item)
        self.assertTrue(sync.success)
        self.assertEqual(sync.portal_status_code, 201)
        self.assertTrue(sync.transaction_id.startswith("TXN-"))

if __name__ == "__main__":
    unittest.main()
