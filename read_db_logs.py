import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

from app.database import SessionLocal, engine, Base
from app.models import Baseline, BaselineScreenshot, RegressionTestRun, RegressionTestResult

def read_db_logs():
    # Automatically initialize tables if they don't exist in the SQLite file
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        print("====================================================================")
        print("   QA.AI Platform Local SQLite Database Log Auditor")
        print("====================================================================")
        
        # 1. Audit Baselines
        baselines = db.query(Baseline).all()
        print(f"\n📁 [1/4] Baselines Captured: {len(baselines)}")
        for b in baselines:
            screenshots = db.query(BaselineScreenshot).filter(BaselineScreenshot.baseline_id == b.id).all()
            print(f"  - ID {b.id}: Name: '{b.name}' | URL: {b.url} | Created: {b.created_at}")
            print(f"    Screenshots tracked: {len(screenshots)} viewports")
            for s in screenshots:
                print(f"      * Viewport: {s.viewport} -> Path: {s.image_path}")

        # 2. Audit Test Runs
        runs = db.query(RegressionTestRun).all()
        print(f"\n📋 [2/4] Regression Test Runs: {len(runs)}")
        for r in runs:
            print(f"  - ID {r.id}: Baseline ID {r.baseline_id} | Target URL: {r.target_url}")
            print(f"    Status: '{r.status}' | Created: {r.created_at}")
            print(f"    Summary: '{r.summary}'")

            # 3. Audit Viewport Results
            results = db.query(RegressionTestResult).filter(RegressionTestResult.run_id == r.id).all()
            print(f"    Viewport Results: {len(results)}")
            for res in results:
                print(f"      * Viewport: {res.viewport} | Score: {res.similarity_score}% | Mismatch: {res.is_mismatch}")
                if res.error_message:
                    print(f"        🚨 Error: {res.error_message}")

        print("\n====================================================================")
    except Exception as e:
        print("Error reading database logs:", e)
    finally:
        db.close()

if __name__ == "__main__":
    read_db_logs()
