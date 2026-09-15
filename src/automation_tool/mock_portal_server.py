"""
Mock Enterprise Portal Server
Simulates the client's internal HR Web System (HR人事給与システム) on localhost.
Uses Python standard http.server (no external dependencies).
"""
import sys
import json
import uuid
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# In-memory mock database
PORTAL_DATABASE = [
    {"case_id": "P1-07080388-001", "employee": "山田 太郎", "category": "出張旅費", "amount": 18500, "remark": "旅費精算確認済", "status": "REGISTERED"},
    {"case_id": "P1-07080388-002", "employee": "佐藤 花子", "category": "時間外手当", "amount": 42000, "remark": "残業手当調整", "status": "REGISTERED"},
]

HTML_PAGE = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>HR人事給与システム - 給与備考・控除管理</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 20px; background: #f4f6f9; color: #333; }
        .header { background: #1a365d; color: white; padding: 15px 25px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
        .badge { background: #3182ce; padding: 4px 10px; border-radius: 12px; font-size: 13px; }
        .table-card { background: white; padding: 20px; border-radius: 8px; margin-top: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.06); }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 14px; }
        th { background: #edf2f7; color: #4a5568; }
        .status-ok { color: #276749; font-weight: bold; }
        .status-sync { color: #2b6cb0; font-weight: bold; }
        .tag { background: #e2e8f0; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h2>HR人事給与システム (2026年度 · 人事部門)</h2>
        <span class="badge">給与備考・控除整備ポータル (Port 5132 Mock)</span>
    </div>
    <div class="table-card">
        <h3>登録済み案件一覧 (Registered Payroll Adjustments)</h3>
        <p style="color: #718096; font-size: 13px;">AutoPay-HR 連携稼働中 — 同期された案件がリアルタイムに反映されます。</p>
        <table id="payroll-table">
            <thead>
                <tr>
                    <th>Case ID</th>
                    <th>対象社員 (Employee)</th>
                    <th>費目 (Category)</th>
                    <th>金額 (Amount)</th>
                    <th>備考 / 規程確認 (Remark)</th>
                    <th>ステータス (Status)</th>
                </tr>
            </thead>
            <tbody>
                <!-- Populated via API -->
            </tbody>
        </table>
    </div>
    <script>
        function loadData() {
            fetch('/api/payroll-items')
                .then(r => r.json())
                .then(data => {
                    const tbody = document.querySelector('#payroll-table tbody');
                    tbody.innerHTML = '';
                    data.forEach(item => {
                        const tr = document.createElement('tr');
                        tr.innerHTML = `
                            <td><strong>${item.case_id}</strong></td>
                            <td>${item.employee}</td>
                            <td><span class="tag">${item.category}</span></td>
                            <td>¥${Number(item.amount).toLocaleString()}</td>
                            <td>${item.remark}</td>
                            <td><span class="status-ok">✔ 登録済</span></td>
                        `;
                        tbody.appendChild(tr);
                    });
                });
        }
        loadData();
        setInterval(loadData, 2000);
    </script>
</body>
</html>
"""

class PortalHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Suppress noisy default logging
        
    def do_GET(self):
        if self.path in ["/", "/#/payroll-items"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif self.path.startswith("/api/payroll-items"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(PORTAL_DATABASE, ensure_ascii=False).encode("utf-8"))
        elif self.path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "healthy"}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/payroll-items":
            content_len = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_len)
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
        else:
            self.send_response(404)
            self.end_headers()

def start_portal_server(port=5135):
    server = HTTPServer(("127.0.0.1", port), PortalHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"Mock HR Portal Server running on http://127.0.0.1:{port}")
    return server

if __name__ == "__main__":
    port = 5135
    server = start_portal_server(port)
    print(f"Server is listening. Press Ctrl+C to stop.")
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping server.")
        server.shutdown()
