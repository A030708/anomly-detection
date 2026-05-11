import re
import json
from datetime import datetime
from dataclasses import dataclass

@dataclass
class ParsedLog:
    timestamp: datetime
    level: str
    source: str
    message: str
    extra_data: dict
    raw: str

class LogParser:
    def parse(self, raw_log: str) -> ParsedLog:
        # Try JSON format first (Docker, Kubernetes, modern apps use this)
        try:
            data = json.loads(raw_log)
            return ParsedLog(
                timestamp=self._parse_time(data.get('timestamp', data.get('time', ''))),
                level=str(data.get('level', data.get('severity', 'INFO'))).upper(),
                source=data.get('source', data.get('service', data.get('logger', 'unknown'))),
                message=data.get('message', data.get('msg', '')),
                extra_data=data,
                raw=raw_log
            )
        except json.JSONDecodeError:
            pass

        # Try standard format: "2024-01-15 10:30:00 [ERROR] [source] message"
        match = re.match(
            r'(?P<ts>\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}[.\d]*)\s*\[?(?P<level>\w+)\]?\s*\[?(?P<source>[^\]]+)\]?\s*(?P<msg>.*)',
            raw_log
        )
        if match:
            g = match.groupdict()
            return ParsedLog(
                timestamp=self._parse_time(g['ts']),
                level=g['level'].upper(),
                source=g['source'],
                message=g['msg'],
                extra_data={},
                raw=raw_log
            )

        # Fallback if we can't figure out the format
        return ParsedLog(
            timestamp=datetime.now(),
            level='INFO',
            source='unknown',
            message=raw_log,
            extra_data={},
            raw=raw_log
        )

    def _parse_time(self, ts_str: str) -> datetime:
        if not ts_str: return datetime.now()
        formats = ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']
        for fmt in formats:
            try: return datetime.strptime(ts_str.strip(), fmt)
            except ValueError: continue
        return datetime.now()
