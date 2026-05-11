from supabase import create_client, Client
from config import Config
import logging

logger = logging.getLogger(__name__)

class Database:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        try:
            self.client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
            logger.info("Successfully connected to Supabase.")
        except Exception as e:
            logger.error(f"Supabase connection failed: {e}")
            self.client = None

    def insert_log(self, log_data: dict) -> bool:
        if not self.client: return False
        try:
            payload = {
                "message": log_data.get("message", "Empty message"),
                "log_level": log_data.get("level", "INFO").upper(),
                "source": log_data.get("source", "unknown"),
                "raw_log": log_data.get("raw", ""),
                "is_anomaly": log_data.get("is_anomaly", False),
                "structured_data": log_data.get("structured_data", {})
            }
            self.client.table("logs").insert(payload).execute()
            return True
        except Exception as e:
            logger.error(f"DB Insert Error: {e}")
            return False

    def get_logs(self, page: int = 1, per_page: int = 50, level: str = None) -> dict:
        if not self.client: return {"data": [], "count": 0}
        try:
            start = (page - 1) * per_page
            end = start + per_page - 1
            
            query = self.client.table("logs").select("*", count="exact")
            
            if level and level != "ALL":
                query = query.eq("log_level", level.upper())

            response = query.order("timestamp", desc=True).range(start, end).execute()
            
            return {
                "data": response.data,
                "count": response.count
            }
        except Exception as e:
            logger.error(f"DB Logs Fetch Error: {e}")
            return {"data": [], "count": 0}

    def get_unanalyzed_anomalies(self, limit: int = 5) -> list:
        if not self.client: return []
        try:
            res = (self.client.table("logs")
                   .select("id, message, log_level, source")
                   .eq("is_anomaly", True)
                   .eq("is_analyzed", False)
                   .order("timestamp", desc=True)
                   .limit(limit)
                   .execute())
            return res.data
        except Exception as e:
            logger.error(f"DB Fetch Error: {e}")
            return []

    def insert_analysis(self, log_id: int, analysis_data: dict):
        if not self.client: return
        try:
            payload = {
                "log_id": log_id,
                "severity": analysis_data.get("severity", "Unknown"),
                "root_cause": analysis_data.get("root_cause", "Unknown"),
                "recommended_actions": analysis_data.get("recommended_actions", []),
                "confidence_score": analysis_data.get("confidence_score", 0.0),
                "model": Config.LLM_MODEL
            }
            self.client.table("analysis").insert(payload).execute()
            # Mark the log as analyzed
            self.client.table("logs").update({"is_analyzed": True}).eq("id", log_id).execute()
        except Exception as e:
            logger.error(f"DB Analysis Insert Error: {e}")

    def get_analysis_by_log_id(self, log_id: int) -> dict:
        if not self.client: return None
        try:
            res = self.client.table("analysis").select("*").eq("log_id", log_id).single().execute()
            return res.data
        except:
            return None

    def get_analysis_by_message_hash(self, msg_hash: str) -> dict:
        if not self.client: return None
        try:
            # We search for an analysis with this hash saved in root_cause (simplified mapping)
            res = self.client.table("analysis").select("*").filter("root_cause", "ilike", f"%{msg_hash}%").limit(1).execute()
            return res.data[0] if res.data else None
        except:
            return None

    def create_alert(self, log_id: int, severity: str, message: str):
        if not self.client: return
        try:
            self.client.table("alerts").insert({
                "log_id": log_id,
                "severity": severity,
                "message": message
            }).execute()
        except Exception as e:
            logger.error(f"Alert Insert Error: {e}")

    def get_stats(self) -> dict:
        if not self.client: return {"total_logs": 0, "anomalies": 0, "analyzed": 0, "alerts": 0}
        try:
            logs = self.client.table("logs").select("id", count="exact").execute().count or 0
            anomalies = self.client.table("logs").select("id", count="exact").eq("is_anomaly", True).execute().count or 0
            analyzed = self.client.table("analysis").select("id", count="exact").execute().count or 0
            alerts = self.client.table("alerts").select("id", count="exact").eq("is_resolved", False).execute().count or 0
            
            return {
                "total_logs": logs,
                "anomalies": anomalies,
                "analyzed": analyzed,
                "alerts": alerts
            }
        except Exception as e:
            logger.error(f"DB Stats Error: {e}")
            return {"total_logs": 0, "anomalies": 0, "analyzed": 0, "alerts": 0}
