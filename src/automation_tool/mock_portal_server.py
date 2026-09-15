"""
Enhanced Interactive Mock HR Portal & Web Demo Dashboard
Hosts a visual management interface on http://127.0.0.1:5135
"""
import sys
import os
import json
import uuid
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

PORTAL_DATABASE = [
    {"case_id": "P1-07080388-001", "employee": "山田 太郎", "category": "出張旅費", "amount": 18500, "remark": "旅費精算確認済", "status": "REGISTERED", "transaction_id": "TXN-INIT-01", "synced_at": "2026-09-15T10:00:00Z"},
]

STATS = {
    "total_processed": 1,
    "auto_synced": 1,
    "flagged_review": 0,
    "rejected": 0,
    "time_saved_sec": 33.0
}

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoPay-HR: Enterprise Payroll Automation Portal</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0f172a;
            --surface: #1e293b;
            --surface-hover: #334155;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg); color: var(--text-main); line-height: 1.5; padding: 24px; }
        .container { max-width: 1200px; margin: 0 auto; }
        
        /* Header */
        .navbar { display: flex; justify-content: space-between; align-items: center; padding-bottom: 20px; border-bottom: 1px solid var(--border); margin-bottom: 24px; }
        .brand { display: flex; align-items: center; gap: 12px; }
        .logo { background: linear-gradient(135deg, #3b82f6, #8b5cf6); padding: 8px 14px; border-radius: 8px; font-weight: 700; font-size: 18px; }
        .tagline { font-size: 13px; color: var(--text-muted); }
        .live-chip { background: rgba(16, 185, 129, 0.2); color: #34d399; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; display: flex; align-items: center; gap: 6px; }
        .live-dot { width: 8px; height: 8px; background: #10b981; border-radius: 50%; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(1.2); } }

        /* KPI Cards */
        .kpi-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .kpi-card { background: var(--surface); border: 1px solid var(--border); padding: 20px; border-radius: 12px; }
        .kpi-title { font-size: 13px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
        .kpi-value { font-size: 28px; font-weight: 700; }
        .val-primary { color: #60a5fa; }
        .val-success { color: #34d399; }
        .val-warning { color: #fbbf24; }
        .val-purple { color: #c084fc; }

        /* Action Panel */
        .actions-panel { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 24px; }
        .panel-title { font-size: 16px; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
        .btn-group { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
        .btn { padding: 10px 18px; border-radius: 8px; font-size: 14px; font-weight: 600; border: none; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 8px; }
        .btn-primary { background: var(--primary); color: white; }
        .btn-primary:hover { background: var(--primary-hover); transform: translateY(-1px); }
        .btn-warning { background: #d97706; color: white; }
        .btn-warning:hover { background: #b45309; transform: translateY(-1px); }
        .btn-secondary { background: var(--surface-hover); color: var(--text-main); border: 1px solid var(--border); }
        .btn-secondary:hover { background: #475569; }

        /* Custom Input Form */
        .memo-box { width: 100%; height: 85px; background: #0f172a; border: 1px solid var(--border); border-radius: 8px; padding: 12px; color: white; font-family: monospace; font-size: 13px; resize: vertical; margin-bottom: 12px; }
        .memo-box:focus { outline: none; border-color: var(--primary); }

        /* Table */
        .table-wrapper { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
        .table-header { padding: 16px 20px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; }
        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; }
        th { background: #162032; padding: 14px 18px; font-weight: 600; color: var(--text-muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid var(--border); }
        td { padding: 14px 18px; border-bottom: 1px solid var(--border); }
        tr:hover { background: rgba(255,255,255,0.02); }
        .pill { padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; display: inline-block; }
        .pill-success { background: rgba(16, 185, 129, 0.15); color: #34d399; }
        .pill-cat { background: rgba(59, 130, 246, 0.15); color: #60a5fa; }
        .pill-warning { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }
        .case-code { font-family: monospace; font-weight: 600; color: #93c5fd; }
        .amount-val { font-family: monospace; font-weight: 600; color: #f1f5f9; }
        .empty-state { padding: 40px; text-align: center; color: var(--text-muted); }
    </style>
</head>
<body>
    <div class="container">
        <!-- Top Navbar -->
        <header class="navbar">
            <div class="brand">
                <div class="logo">AutoPay-HR</div>
                <div>
                    <h2>HR人事給与システム (2026年度)</h2>
                    <div class="tagline">給与備考・控除整備 自動化ブリッジ (Port 5135 Live Bridge)</div>
                </div>
            </div>
            <div class="live-chip">
                <div class="live-dot"></div>
                <span>AUTOMATION ENGINE READY</span>
            </div>
        </header>

        <!-- KPI Metrics Grid -->
        <section class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-title">Total Cases Ingested</div>
                <div class="kpi-value val-primary" id="kpi-total">0</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Auto-Synced (Zero Touch)</div>
                <div class="kpi-value val-success" id="kpi-synced">0</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Human-in-the-Loop Flags</div>
                <div class="kpi-value val-warning" id="kpi-flagged">0</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Staff Time Saved</div>
                <div class="kpi-value val-purple" id="kpi-time">0.0 min</div>
            </div>
        </section>

        <!-- Action Control Center -->
        <section class="actions-panel">
            <div class="panel-title">⚡ Interactive Execution Control</div>
            <div class="btn-group">
                <button class="btn btn-primary" onclick="triggerBatch('routine')">
                    <span>▶️ Run Routine Compliant Batch</span>
                </button>
                <button class="btn btn-warning" onclick="triggerBatch('exception')">
                    <span>⚠️ Run Risk & Exception Batch (>¥100k, Dup)</span>
                </button>
                <button class="btn btn-secondary" onclick="triggerBatch('enterprise')">
                    <span>📂 Run Enterprise Feed (JSON)</span>
                </button>
            </div>
            
            <div style="margin-top: 15px;">
                <label style="font-size: 13px; color: var(--text-muted); display: block; margin-bottom: 6px;">
                    📝 Or Paste Custom Japanese Memo / Ticket to Process Live:
                </label>
                <textarea id="custom-memo" class="memo-box" placeholder="精算確認メモ&#10;P1-07080388-099&#10;申請者：佐藤 健司&#10;経費精算確認済み。費目：出張旅費 金額：48,000円。規程内であることを確認した。"></textarea>
                <button class="btn btn-secondary" onclick="processCustomMemo()" style="font-size: 13px; padding: 6px 14px;">
                    🚀 Process Custom Memo with AutoPay-HR
                </button>
            </div>
        </section>

        <!-- Live Transactions Table -->
        <section class="table-wrapper">
            <div class="table-header">
                <h3>登録済み案件リアルタイム一覧 (Registered Payroll Items)</h3>
                <span style="font-size: 13px; color: var(--text-muted);" id="row-count">0 items loaded</span>
            </div>
            <table id="payroll-table">
                <thead>
                    <tr>
                        <th>Case ID</th>
                        <th>対象社員 (Employee)</th>
                        <th>費目 (Category)</th>
                        <th>金額 (Amount)</th>
                        <th>備考・規程確認 (Remark)</th>
                        <th>TXN ID</th>
                        <th>ステータス (Status)</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- Injected via JavaScript -->
                </tbody>
            </table>
        </section>
    </div>

    <script>
        function updateDashboard() {
            fetch('/api/payroll-items')
                .then(r => r.json())
                .then(data => {
                    const tbody = document.querySelector('#payroll-table tbody');
                    tbody.innerHTML = '';
                    document.getElementById('row-count').innerText = `${data.length} registered adjustments`;
                    
                    data.slice().reverse().forEach(item => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td><span class="case-code">${item.case_id}</span></td>
                            <td><strong>${item.employee}</strong></td>
                            <td><span class="pill pill-cat">${item.category}</span></td>
                            <td><span class="amount-val">¥${Number(item.amount).toLocaleString()}</span></td>
                            <td style="max-width: 320px; color: #cbd5e1; font-size: 13px;">${item.remark}</td>
                            <td style="font-family: monospace; font-size: 12px; color: #94a3b8;">${item.transaction_id || '-'}</td>
                            <td><span class="pill pill-success">✔ 登録済 (SYNCED)</span></td>
                        `;
                        tbody.appendChild(tr);
                    });
                });

            fetch('/api/stats')
                .then(r => r.json())
                .then(s => {
                    document.getElementById('kpi-total').innerText = s.total_processed;
                    document.getElementById('kpi-synced').innerText = s.auto_synced;
                    document.getElementById('kpi-flagged').innerText = s.flagged_review;
                    const mins = (s.time_saved_sec / 60.0).toFixed(1);
                    document.getElementById('kpi-time').innerText = `${mins} min (${s.time_saved_sec.toFixed(0)}s)`;
                });
        }

        function triggerBatch(type) {
            fetch(`/api/trigger-batch?type=${type}`, { method: 'POST' })
                .then(r => r.json())
                .then(res => {
                    updateDashboard();
                    alert(`Batch [${type}] Processed!\n\n• Total: ${res.total}\n• Auto-Synced: ${res.synced}\n• Flagged for Human Review: ${res.flagged}\n• Rejected: ${res.rejected}\n• Staff Time Saved: ${(res.time_saved_sec/60).toFixed(2)} min`);
                });
        }

        function processCustomMemo() {
            const text = document.getElementById('custom-memo').value;
            if (!text.trim()) {
                alert('Please enter or paste a memo text.');
                return;
            }
            fetch('/api/process-custom', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ raw_text: text })
            })
            .then(r => r.json())
            .then(res => {
                updateDashboard();
                document.getElementById('custom-memo').value = '';
                alert(`Custom Memo Processed!\n\n• Case ID: ${res.case_id}\n• Status: ${res.status}\n• Amount: ¥${Number(res.amount).toLocaleString()}\n• Result: ${res.message}`);
            });
        }

        updateDashboard();
        setInterval(updateDashboard, 2500);
    </script>
</body>
</html>
"""

class PortalHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
        
    def do_GET(self):
        if self.path in ["/", "/#/payroll-items"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_DASHBOARD.encode("utf-8"))
        elif self.path.startswith("/api/payroll-items"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(PORTAL_DATABASE, ensure_ascii=False).encode("utf-8"))
        elif self.path == "/api/stats":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(STATS).encode("utf-8"))
        elif self.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "healthy"}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len) if content_len > 0 else b'{}'
        
        if self.path == "/api/payroll-items":
            try:
                item_data = json.loads(body.decode('utf-8'))
                txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
                
                record = {
                    "case_id": item_data.get("case_id"),
                    "employee": item_data.get("employee_name_or_id", "社内担当"),
                    "category": item_data.get("category", "一般調整"),
                    "amount": float(item_data.get("amount", 0)),
                    "remark": item_data.get("remark", ""),
                    "status": "REGISTERED",
                    "transaction_id": txn_id,
                    "synced_at": datetime.now(timezone.utc).isoformat()
                }
                PORTAL_DATABASE.append(record)
                
                STATS["total_processed"] += 1
                STATS["auto_synced"] += 1
                STATS["time_saved_sec"] += 33.0
                
                response = {
                    "status": "SUCCESS",
                    "transaction_id": txn_id,
                    "case_id": record["case_id"],
                    "synced_at": record["synced_at"]
                }
                self.send_response(201)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ERROR", "message": str(e)}).encode("utf-8"))
                
        elif self.path.startswith("/api/trigger-batch"):
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            b_type = query.get("type", ["routine"])[0]
            
            from .memo_parser import MemoParser
            from .business_rules import BusinessRuleEngine
            
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            data_dir = os.path.join(base_dir, "data", "sample_memos")
            
            file_map = {
                "routine": os.path.join(data_dir, "routine_batch.txt"),
                "exception": os.path.join(data_dir, "exception_batch.txt"),
                "enterprise": os.path.join(data_dir, "enterprise_feed.json")
            }
            target_file = file_map.get(b_type, file_map["routine"])
            
            if target_file.endswith(".json"):
                with open(target_file, "r", encoding="utf-8") as f:
                    items = [MemoParser.parse_structured_dict(d, "batch") for d in json.load(f)]
            else:
                with open(target_file, "r", encoding="utf-8") as f:
                    items = MemoParser.parse_text(f.read(), "batch")
                    
            engine = BusinessRuleEngine()
            for rec in PORTAL_DATABASE:
                engine.register_processed(rec["case_id"])
                
            res = {"total": len(items), "synced": 0, "flagged": 0, "rejected": 0, "time_saved_sec": 0.0}
            
            for it in items:
                v = engine.validate(it)
                if v.status == "AUTO_APPROVED":
                    txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
                    PORTAL_DATABASE.append({
                        "case_id": it.case_id,
                        "employee": it.employee_name_or_id,
                        "category": it.category,
                        "amount": it.amount,
                        "remark": it.remark,
                        "status": "REGISTERED",
                        "transaction_id": txn_id,
                        "synced_at": datetime.now(timezone.utc).isoformat()
                    })
                    engine.register_processed(it.case_id)
                    res["synced"] += 1
                    res["time_saved_sec"] += 33.0
                    STATS["auto_synced"] += 1
                    STATS["time_saved_sec"] += 33.0
                elif v.status == "FLAGGED_FOR_REVIEW":
                    res["flagged"] += 1
                    STATS["flagged_review"] += 1
                else:
                    res["rejected"] += 1
                    STATS["rejected"] += 1
                STATS["total_processed"] += 1
                
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode("utf-8"))
            
        elif self.path == "/api/process-custom":
            from .memo_parser import MemoParser
            from .business_rules import BusinessRuleEngine
            
            req_data = json.loads(body.decode('utf-8'))
            raw_text = req_data.get("raw_text", "")
            items = MemoParser.parse_text(raw_text, "custom_input")
            
            if not items:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"status": "ERROR", "message": "Could not parse memo"}')
                return
                
            it = items[0]
            engine = BusinessRuleEngine()
            for rec in PORTAL_DATABASE:
                engine.register_processed(rec["case_id"])
                
            v = engine.validate(it)
            STATS["total_processed"] += 1
            
            if v.status == "AUTO_APPROVED":
                txn = f"TXN-{uuid.uuid4().hex[:8].upper()}"
                PORTAL_DATABASE.append({
                    "case_id": it.case_id,
                    "employee": it.employee_name_or_id,
                    "category": it.category,
                    "amount": it.amount,
                    "remark": it.remark,
                    "status": "REGISTERED",
                    "transaction_id": txn,
                    "synced_at": datetime.now(timezone.utc).isoformat()
                })
                STATS["auto_synced"] += 1
                STATS["time_saved_sec"] += 33.0
                resp = {"case_id": it.case_id, "status": "AUTO_SYNCED", "amount": it.amount, "message": f"Successfully registered into portal! Transaction ID: {txn}"}
            elif v.status == "FLAGGED_FOR_REVIEW":
                STATS["flagged_review"] += 1
                resp = {"case_id": it.case_id, "status": "FLAGGED_FOR_REVIEW", "amount": it.amount, "message": f"Held for Human Manager Review. Flags: {', '.join(v.flags)}"}
            else:
                STATS["rejected"] += 1
                resp = {"case_id": it.case_id, "status": "REJECTED", "amount": it.amount, "message": f"Rejected by business rules. Flags: {', '.join(v.flags)}"}
                
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

def start_portal_server(port=5135):
    server = HTTPServer(("127.0.0.1", port), PortalHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    return server

if __name__ == "__main__":
    port = 5135
    server = start_portal_server(port)
    print(f"Interactive AutoPay-HR Dashboard live at: http://127.0.0.1:{port}")
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping server.")
        server.shutdown()
