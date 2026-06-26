from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models import AuditLog

router = APIRouter(prefix="/api/audit-logs", tags=["System Audit Logs"])

# =====================================================================
# PYDANTIC SCHEMAS
# =====================================================================

class AuditLogCreateRequest(BaseModel):
    action: str  # 'visual_testing', 'testcase_generator', 'bug_reporter', 'config'
    details: str


class AuditLogResponseSchema(BaseModel):
    id: int
    action: str
    details: str
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# UTILITY HELPER
# =====================================================================

def log_audit(db: Session, action: str, details: str):
    """
    Globally available thread-safe logger helper to register visual and logical 
    platform operations inside our relational SQLite storage.
    Spawns a private, isolated database session strictly to prevent SQLAlchemy transaction leaks.
    Also, automatically clears/prunes any audit logs that are older than 7 days to maintain
    a clean, self-healing data retention policy!
    """
    from app.database import SessionLocal
    from datetime import datetime, timedelta
    private_db = SessionLocal()
    try:
        # 1. Write the new system log entry
        log_entry = AuditLog(action=action, details=details)
        private_db.add(log_entry)
        private_db.commit()

        # 2. Clean-slate prune: Automatically clear logs older than 7 days!
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        deleted_count = private_db.query(AuditLog).filter(AuditLog.created_at < seven_days_ago).delete()
        if deleted_count > 0:
            private_db.commit()
            print(f"   🧹 [LOG PRUNER] Automatically cleared {deleted_count} system audit logs older than 7 days!")
            
    except Exception as e:
        print(f"Failed to record or prune system audit logs: {e}")
    finally:
        private_db.close()


# =====================================================================
# API ENDPOINTS
# =====================================================================

@router.get("/", response_model=List[AuditLogResponseSchema])
async def list_audit_logs(limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all platform and agent execution logs sorted chronologically descending.
    """
    try:
        logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
        return logs
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to query audit logs: {str(err)}"
        )


@router.post("/", response_model=AuditLogResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_audit_log(payload: AuditLogCreateRequest, db: Session = Depends(get_db)):
    """
    Explicitly write a custom event log directly onto the system audit table.
    """
    try:
        log_entry = AuditLog(action=payload.action, details=payload.details)
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write audit log: {str(err)}"
        )


@router.delete("/clear", status_code=status.HTTP_200_OK)
async def clear_audit_logs(db: Session = Depends(get_db)):
    """
    Truncates the audit logs relational table, purging all historical event logs.
    """
    try:
        db.query(AuditLog).delete()
        db.commit()
        return {"message": "System audit log history successfully cleared."}
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear audit logs: {str(err)}"
        )
