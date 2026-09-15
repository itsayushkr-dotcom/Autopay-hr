"""
Generate Realistic Test Memos for AutoPay-HR
Directly grounded in the actual Japanese operation logs from Dataset B.
"""
import os
import json

DATA_DIR = r"C:\Users\itsay\AI_Engineer\data\sample_memos"
os.makedirs(DATA_DIR, exist_ok=True)

# 1. Standard Compliant Batch (Routine Daily Paperwork)
BATCH_1 = """========================================
精算確認メモ
P1-07080388-002
申請者：田中 麻里
経費精算確認済み。費目：出張旅費 金額：35,241円。規程内であることを確認した。
========================================
給与手当連絡票
P1-07080388-003
対象者：高橋 健司
2026-06分 時間外手当調整 57,500円を給与備考欄に登録。通常処理。規程内確認済み。
========================================
IT申請メモ
P1-07080388-004
申請者：上野 大樹
PC新規発行申請 費目：機器手当 金額：45,000円。承認済。
========================================
福利厚生費精算
P1-07080388-005
対象者：小林 翔太
費目：資格取得補助 金額：28,000円。規程内確認済み。
"""

with open(os.path.join(DATA_DIR, "routine_batch.txt"), "w", encoding="utf-8") as f:
    f.write(BATCH_1)

# 2. Risk & Exception Batch (Contains Anomaly, Policy Violation, and Duplicate)
BATCH_2 = """========================================
精算確認メモ
P1-07080388-006
申請者：渡辺 翼
費目：海外出張手当 金額：285,000円。規程内確認済み。
========================================
未承認メモ
P1-07080388-007
申請者：中村 祐介
費目：特別役職手当 金額：60,000円。上長確認待ちのため規程未確認。
========================================
重複テスト案件
P1-07080388-002
申請者：田中 麻里
費目：出張旅費 金額：35,241円。重複申請。
"""

with open(os.path.join(DATA_DIR, "exception_batch.txt"), "w", encoding="utf-8") as f:
    f.write(BATCH_2)

# 3. Enterprise Structured JSON Feed
JSON_FEED = [
    {"case_id": "P1-07080388-010", "employee": "加藤 恵", "category": "出張旅費", "amount": 22400, "confirmed": True, "remark": "大阪支社出張旅費精算"},
    {"case_id": "P1-07080388-011", "employee": "伊藤 潤", "category": "時間外手当", "amount": 64800, "confirmed": True, "remark": "プロジェクト繁忙期残業手当調整"},
    {"case_id": "P1-07080388-012", "employee": "山本 雅也", "category": "研修手当", "amount": 150000, "confirmed": True, "remark": "海外技術研修費用（高額案件）"}
]

with open(os.path.join(DATA_DIR, "enterprise_feed.json"), "w", encoding="utf-8") as f:
    json.dump(JSON_FEED, f, ensure_ascii=False, indent=2)

print("Sample test memos created in", DATA_DIR)
