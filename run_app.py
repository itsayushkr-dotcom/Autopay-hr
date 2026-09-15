"""
AutoPay-HR: One-Click Interactive Application Launcher
Starts the portal web dashboard and automation engine.
Open http://127.0.0.1:5135 in your browser.
"""
import sys
import os
import time
import webbrowser

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from automation_tool.mock_portal_server import start_portal_server

def main():
    port = 5135
    server = start_portal_server(port=port)
    url = f"http://127.0.0.1:{port}"
    
    print("\n" + "=" * 70)
    print("  AUTOPAY-HR: INTERACTIVE ENTERPRISE PORTAL & AUTOMATION ENGINE")
    print("=" * 70)
    print(f"  [+] Web Dashboard Live URL: {url}")
    print("  [+] Simulating: HR人事給与システム (2026年度)")
    print("  [+] Control Panel: Run Batch Memos / Anomaly Tests / Custom Memos")
    print("  [+] Press Ctrl+C in this terminal to stop the server.")
    print("=" * 70 + "\n")
    
    try:
        # Try to open in browser automatically
        webbrowser.open(url)
    except Exception:
        pass
        
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping AutoPay-HR server...")
        server.shutdown()
        print("Server stopped cleanly.")

if __name__ == "__main__":
    main()
