"""
Command-Line Interface (CLI) for AutoPay-HR
Provides interactive options to process batches, launch mock portal, and export audit trails.
"""
import argparse
import sys
import os

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from .main import AutoPayPipeline

def run_cli():
    parser = argparse.ArgumentParser(
        description="AutoPay-HR: Intelligent Payroll Adjustment & Compliance Bridge",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.automation_tool.cli --demo
  python -m src.automation_tool.cli --file data/sample_memos/routine_batch.txt
  python -m src.automation_tool.cli --portal-url http://127.0.0.1:5135
        """
    )
    parser.add_argument("--file", "-f", help="Path to text or JSON memo file to process")
    parser.add_argument("--demo", action="store_true", help="Run comprehensive demo across all sample batches")
    parser.add_argument("--portal-url", default="http://127.0.0.1:5135", help="URL of the HR Portal (default: http://127.0.0.1:5135)")
    parser.add_argument("--no-server", action="store_true", help="Do not launch the built-in mock portal server")
    
    args = parser.parse_args()
    
    pipeline = AutoPayPipeline(portal_url=args.portal_url, auto_start_server=not args.no_server)
    
    if args.file:
        if not os.path.exists(args.file):
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
        pipeline.process_memo_file(args.file)
        pipeline.save_audit_report()
    else:
        # Default or --demo
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        data_dir = os.path.join(base_dir, "data", "sample_memos")
        
        batch1 = os.path.join(data_dir, "routine_batch.txt")
        batch2 = os.path.join(data_dir, "exception_batch.txt")
        batch3 = os.path.join(data_dir, "enterprise_feed.json")
        
        pipeline.process_memo_file(batch1)
        pipeline.process_memo_file(batch2)
        pipeline.process_memo_file(batch3)
        pipeline.save_audit_report(os.path.join(base_dir, "output"))

if __name__ == "__main__":
    run_cli()
