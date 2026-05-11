import json
import logging
import hashlib
from groq import Groq
from database import Database
from config import Config

logger = logging.getLogger(__name__)

class SmartLLMAnalyzer:
    def __init__(self):
        self.db = Database.get_instance()
        self.groq_client = Groq(api_key=Config.GROQ_API_KEY) if Config.GROQ_API_KEY else None
        self.cache = {}

    def analyze_batch(self, logs: list):
        if not self.groq_client:
            logger.warning("Groq client not initialized.")
            return

        for log in logs:
            log_id = log.get("id")
            message = log.get("message", "")
            msg_hash = hashlib.md5(message.strip().encode()).hexdigest()

            # 1. Local Cache
            if msg_hash in self.cache:
                logger.info(f"Local Cache Hit: {log_id}")
                self._apply_past_analysis(log_id, self.cache[msg_hash])
                continue

            # 2. DB Cache
            past_analysis = self.db.get_analysis_by_message_hash(msg_hash)
            if past_analysis:
                logger.info(f"DB Cache Hit: {log_id}")
                self.cache[msg_hash] = past_analysis
                self._apply_past_analysis(log_id, past_analysis)
                continue

            # 3. AI Analysis
            analysis = self._perform_analysis(log)
            if analysis:
                analysis['msg_hash'] = msg_hash
                self.cache[msg_hash] = analysis
                self.db.insert_analysis(log_id, analysis)
                
                # 4. Alerting
                if analysis.get('severity') in ['CRITICAL', 'HIGH']:
                    self.db.create_alert(log_id, analysis.get('severity'), f"AI Alert: {analysis.get('root_cause')}")

    def _apply_past_analysis(self, log_id, analysis):
        self.db.insert_analysis(log_id, analysis)
        if analysis.get('severity') in ['CRITICAL', 'HIGH']:
            self.db.create_alert(log_id, analysis.get('severity'), f"Cached AI Alert: {analysis.get('root_cause')}")

    def _perform_analysis(self, log: dict) -> dict:
        prompt = f"""
        Analyze this system log and provide a JSON response:
        Log: [{log.get('log_level')}] {log.get('message')}
        
        Format:
        {{
            "severity": "LOW|MEDIUM|HIGH|CRITICAL",
            "root_cause": "brief technical explanation",
            "recommended_actions": ["step 1", "step 2"],
            "confidence_score": 0.95
        }}
        """
        try:
            response = self.groq_client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            data = json.loads(response.choices[0].message.content)
            # Ensure confidence is a decimal if the AI sends it as a percentage
            if data.get('confidence_score', 0) > 1:
                data['confidence_score'] = data['confidence_score'] / 100
            return data
        except Exception as e:
            logger.error(f"AI Error: {e}")
            return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    analyzer = SmartLLMAnalyzer()
    db = Database.get_instance()
    logs = db.get_unanalyzed_anomalies(limit=5)
    if logs:
        analyzer.analyze_batch(logs)
    else:
        print("No new anomalies to analyze.")
