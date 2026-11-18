from datetime import datetime, date, timedelta
from database import get_connection
from interfaces import (
    ICardReader, IPassRepository, IAccessController,
    IMonitoringService, ITimeTrackingService, IEventJournal
)
from models import AccessPass, AccessEvent


class PassRepository(IPassRepository):
    def findByBarcode(self, cardid: str):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT cardNumber, type, active, validUntil, level_id, holder_id FROM AccessPass WHERE cardNumber = ?",
            (cardid,))
        row = cursor.fetchone()
        conn.close()
        return AccessPass(row[0], row[1], row[2], row[3], row[4], row[5]) if row else None

    def save(self, pass_obj: AccessPass):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO AccessPass (cardNumber, type, active, validUntil, level_id, holder_id) VALUES (?, ?, ?, ?, ?, ?)",
            (pass_obj.cardNumber, pass_obj.type, int(pass_obj.active), pass_obj.validUntil, pass_obj.level_id,
             pass_obj.holder_id)
        )
        conn.commit()
        conn.close()


class EventJournal(IEventJournal):
    def write(self, e: AccessEvent):
        conn = get_connection()
        cursor = conn.cursor()
        status = "обработан" if e.result == "разрешён" else "не обработан"
        cursor.execute(
            "INSERT INTO AccessEvent (time, type, result, description, card_number, point_id, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (e.time, e.eventType, e.result, e.description, e.cardNumber, e.pointId, status)
        )
        conn.commit()
        conn.close()

    def query(self, filters=None) -> list:
        conn = get_connection()
        cursor = conn.cursor()
        query_str = """
            SELECT ev.id, ev.time, COALESCE(ch.fullName, 'неизвестный'), COALESCE(ap.name, ev.point_id),
                   ev.result, ev.type, ev.description, ev.status, ev.card_number, ch.id
            FROM AccessEvent ev
            LEFT JOIN AccessPass p ON ev.card_number = p.cardNumber
            LEFT JOIN CardHolder ch ON p.holder_id = ch.id
            LEFT JOIN AccessPoint ap ON ev.point_id = ap.id
            WHERE 1=1
        """
        params = []
        if filters:
            if filters.get("point") and filters["point"] != "все":
                query_str += " AND ap.name = ?"
                params.append(filters["point"])
            if filters.get("type") and filters["type"] != "все":
                query_str += " AND ev.type = ?"
                params.append(filters["type"])
            if filters.get("search"):
                query_str += " AND (ch.fullName LIKE ? OR ev.card_number LIKE ?)"
                params.extend([f"%{filters['search']}%", f"%{filters['search']}%"])

            period = filters.get("period")
            now = datetime.now()
            if period == "сегодня":
                start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                query_str += " AND datetime(ev.time) >= datetime(?)"
                params.append(start_date.strftime("%Y-%m-%d %H:%M:%S"))
            elif period == "вчера":
                start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                query_str += " AND datetime(ev.time) >= datetime(?) AND datetime(ev.time) < datetime(?)"
                params.extend([start_date.strftime("%Y-%m-%d %H:%M:%S"), end_date.strftime("%Y-%m-%d %H:%M:%S")])
            elif period in ("неделя", "сутки"):
                start_date = now - timedelta(days=7 if period == "неделя" else 1)
                query_str += " AND datetime(ev.time) >= datetime(?)"
                params.append(start_date.strftime("%Y-%m-%d %H:%M:%S"))
            elif period == "месяц":
                start_date = now - timedelta(days=30)
                query_str += " AND datetime(ev.time) >= datetime(?)"
                params.append(start_date.strftime("%Y-%m-%d %H:%M:%S"))

        query_str += " ORDER BY datetime(ev.time) DESC"
        cursor.execute(query_str, params)
        rows = cursor.fetchall()
        conn.close()
        return rows


class MonitoringService(IMonitoringService):
    def showHolder(self, p): pass

    def raiseAlarm(self, p): pass


class TimeTrackingService(ITimeTrackingService):
    def register(self, e): pass

    def calcBalance(self, emp, d: date): return "8 ч 00 м"


class AccessController(IAccessController):
    def __init__(self, repository: IPassRepository, journal: IEventJournal, monitoring: IMonitoringService,
                 time_tracking: ITimeTrackingService):
        self.repository = repository
        self.journal = journal

    def processPass(self, cardid: str, pointid: str) -> str:
        return "разрешён"

    def grantAccess(self, p: str) -> bool: return True
