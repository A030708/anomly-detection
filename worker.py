import time
import logging
import threading
from database import Database
from config import Config
from llm_analyzer import SmartLLMAnalyzer

logger = logging.getLogger(__name__)

class AIWorker:
    def __init__(self):
        self.db = Database.get_instance()
        self.analyzer = SmartLLMAnalyzer()
        self.is_running = False

    def start(self):
        self.is_running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("AI Worker thread started.")

    def _run_loop(self):
        while self.is_running:
            try:
                # 1. Fetch unanalyzed anomalies (Batching)
                anomalies = self.db.get_unanalyzed_anomalies(limit=Config.BATCH_SIZE)
                
                if not anomalies:
                    time.sleep(Config.WORKER_SLEEP_SECONDS)
                    continue

                logger.info(f"Worker picked up {len(anomalies)} anomalies for analysis.")
                
                # 2. Process Batch with Smart Analyzer (Caching)
                self.analyzer.analyze_batch(anomalies)

                # 3. Rate limiting
                time.sleep(Config.LLM_RATE_LIMIT_SECONDS)

            except Exception as e:
                logger.error(f"Worker Loop Error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    worker = AIWorker()
    worker._run_loop() # Run in foreground if called directly
