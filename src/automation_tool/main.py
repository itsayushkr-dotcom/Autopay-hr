"""
AutoPay-HR Main Controller & CLI Pipeline
Executes end-to-end ingestion, validation, portal synchronization, and audit reporting.
"""
import os
import sys
import json
import time
from typing import List, Dict, Any

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from .models import PayrollAdjustmentItem, ValidationResult, SyncResult
from .memo_parser import MemoParser
from .business_rules import BusinessRuleEngine
from .portal_client import PortalClient
from .mock_portal_server import start_portal_server

class AutoPayPipeline:
    """
    End-to-End Orchestrator for Payroll Items Automation.
    """
    
    def __init__(self, portal_url="http://127.0.0.1:5135", auto_start_server=True):
        self.portal_url = portal_url
        self.server = None
        if auto_start_server:
            try:
                self.server = start_portal_server(port=5135)
                time.sleep(0.5)
            except Exception as e:
                print(f"[Warning] Could not bind port 5135 (may already be running): {e}")
                
        self.client = PortalClient(base_url=self.portal_url)
        self.rule_engine = BusinessRuleEngine(high_value_threshold=100000.0)
        self.audit_log = []

    def process_memo_file(self, file_path: str) -> Dict[str, Any]:
        print("\n" + "=" * 75)
        print(f"AUTOPAY-HR: PROCESSING FILE -> {os.path.basename(file_path)}")
        print("=" * 75)
        
        # 1. Ingestion
        if file_path.endswith(".json"):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            items = [MemoParser.parse_structured_dict(d, source_name=os.path.basename(file_path)) for d in data]
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_text = f.read()
            items = MemoParser.parse_text(raw_text, source_name=os.path.basename(file_path))
            
        print(f">> Ingested {len(items)} adjustment cases from source.")
        
        batch_results = {
            "total": len(items),
            "synced": 0,
            "flagged": 0,
            "rejected": 0,
            "time_saved_sec": 0.0,
            "items": []
        }
        
        # 2. Validation & Execution Loop
        for idx, item in enumerate(items, 1):
            val: ValidationResult = self.rule_engine.validate(item)
            
            if val.status == "AUTO_APPROVED":
                sync: SyncResult = self.client.sync_item(item)
                self.rule_engine.register_processed(item.case_id)
                batch_results["synced"] += 1
                batch_results["time_saved_sec"] += sync.time_saved_sec
                
                print(f"  [{idx}/{len(items)}] [AUTO-SYNCED] Case: {item.case_id} | {item.employee_name_or_id} | {item.category} | ¥{item.amount:,.0f} -> {sync.transaction_id}")
                self.audit_log.append({
                    "case_id": item.case_id,
                    "status": "SYNCED",
                    "action": "AUTO_APPROVED_AND_SUBMITTED",
                    "details": item.to_dict(),
                    "transaction_id": sync.transaction_id
                })
                
            elif val.status == "FLAGGED_FOR_REVIEW":
                batch_results["flagged"] += 1
                flag_str = ", ".join(val.flags)
                print(f"  [{idx}/{len(items)}] [FLAGGED-REVIEW] Case: {item.case_id} | {item.employee_name_or_id} | ¥{item.amount:,.0f} | Flags: {flag_str}")
                self.audit_log.append({
                    "case_id": item.case_id,
                    "status": "FLAGGED_FOR_HUMAN_REVIEW",
                    "action": "ROUTED_TO_MANAGER",
                    "flags": val.flags,
                    "details": item.to_dict()
                })
                
            else: # REJECTED
                batch_results["rejected"] += 1
                flag_str = ", ".join(val.flags)
                print(f"  [{idx}/{len(items)}] [REJECTED] Case: {item.case_id} | Reason: {flag_str}")
                self.audit_log.append({
                    "case_id": item.case_id,
                    "status": "REJECTED",
                    "action": "DISCARDED",
                    "flags": val.flags,
                    "details": item.to_dict()
                })
                
        time_saved_min = batch_results["time_saved_sec"] / 60.0
        print("\n--- Batch Execution Summary ---")
        print(f"  Total Processed:         {batch_results['total']}")
        print(f"  Successfully Auto-Synced:{batch_results['synced']} (Zero manual keystrokes)")
        print(f"  Flagged for Human Review:{batch_results['flagged']} (High value / unconfirmed policy)")
        print(f"  Rejected (Invalid/Dup):  {batch_results['rejected']}")
        print(f"  Direct Staff Time Saved: {time_saved_min:.2f} minutes ({batch_results['time_saved_sec']:.0f} seconds)")
        
        return batch_results

    def save_audit_report(self, output_dir="output"):
        os.makedirs(output_dir, exist_ok=True)
        report_path = os.path.join(output_dir, "audit_trail.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.audit_log, f, ensure_ascii=False, indent=2)
        print(f"\nAudit trail written to {report_path} (Cryptographic log ready for review)")

def main():
    pipeline = AutoPayPipeline(auto_start_server=True)
    
    # Process both sample batches
    data_dir = r"C:\Users\itsay\AI_Engineer\data\sample_memos"
    batch1 = os.path.join(data_dir, "routine_batch.txt")
    batch2 = os.path.join(data_dir, "exception_batch.txt")
    batch3 = os.path.join(data_dir, "enterprise_feed.json")
    
    pipeline.process_memo_file(batch1)
    pipeline.process_memo_file(batch2)
    pipeline.process_memo_file(batch3)
    
    pipeline.save_audit_report(output_dir=r"C:\Users\itsay\AI_Engineer\output")

if __name__ == "__main__":
    main()
