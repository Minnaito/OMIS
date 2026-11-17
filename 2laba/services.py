"""Бизнес-логика. Соответствует 4 подсистемам + классам диаграмм последовательности/состояний."""
from datetime import datetime, date
from collections import defaultdict
import database as db


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _time_to_min(t):
    if not t: return None
    try:
        h, m = t.split(':')[:2]
        return int(h) * 60 + int(m)
    except ValueError:
        return None


class AuthService:
    @staticmethod
    def login(login, password):
        return db.find_operator(login, password)


class AccessRepository:
    @staticmethod
    def find_by_card(card_number):
        return db.find_pass_by_card(card_number)


class CardReader:
    @staticmethod
    def process_pass(card_number, point_id):
        return AccessControlService.process_swipe(card_number, point_id)


class EventJournal:
    @staticmethod
    def write(event_type, result, point_id, pass_id=None, card_number=None, ts=None):
        ts = ts or _now()
        return db.add_event(point_id, pass_id, card_number or "", ts, event_type, result)


class MonitoringService:
    @staticmethod
    def show_holder(pass_info):
        return pass_info

    @staticmethod
    def raise_alarm(point_id, description, itype="Тревога"):
        return db.add_incident(_now(), point_id, description, itype)

    @staticmethod
    def get_events(point_id=None):
        return db.get_events(point_id)

    @staticmethod
    def get_incidents(status=None):
        return db.get_incidents(status)


class TimeTrackingService:
    @staticmethod
    def record_event(employee_id, point, ts):
        day = ts.split(' ')[0]
        t = ts.split(' ')[1]
        rec = db.get_timesheet(employee_id, day)
        if point['type'] == 'вход':
            if rec and not rec['check_in']: db.update_timesheet(rec['id'], check_in=t)
            elif not rec: db.add_timesheet(employee_id, day, check_in=t)
        elif point['type'] == 'выход':
            if rec: db.update_timesheet(rec['id'], check_out=t)
            else: db.add_timesheet(employee_id, day, check_out=t)

    @staticmethod
    def build_discipline_report(dept_id, date_from, date_to):
        rows = db.get_discipline_data(dept_id, date_from, date_to)
        agg = defaultdict(lambda: {"full_name": "", "personnel_number": "", "late": 0, "early": 0, "overtime": 0, "total_min": 0, "days": 0})

        for r in rows:
            a = agg[r['id']]
            a['full_name'] = r['full_name']
            a['personnel_number'] = r['personnel_number']

            if r['date']:
                ci = _time_to_min(r['check_in'])
                co = _time_to_min(r['check_out'])
                st = _time_to_min(r['start_time'])
                et = _time_to_min(r['end_time'])

                if ci is not None or co is not None:
                    a['days'] += 1

                if ci is not None and co is not None and co > ci:
                    a['total_min'] += (co - ci)

                if st is not None and ci is not None and ci > st + 5:
                    a['late'] += 1

                if et is not None and co is not None and co > et + 30:
                    a['overtime'] += 1

        return list(agg.values())


class AccessControlService:
    @staticmethod
    def process_swipe(card_number, point_id):
        p = AccessRepository.find_by_card(card_number)
        if not p:
            eid = EventJournal.write("неизвестный пропуск", "отказ", point_id, card_number=card_number)
            iid = MonitoringService.raise_alarm(point_id, f"Неизвестная карта {card_number}", itype="Тревога")
            return {"result": "denied", "reason": "unknown_card", "event_id": eid, "incident_id": iid}

        if not p['active']:
            eid = EventJournal.write("пропуск заблокирован", "отказ", point_id, pass_id=p['id'], card_number=card_number)
            iid = MonitoringService.raise_alarm(point_id, f"Попытка прохода по заблокированному пропуску {card_number}", itype="Отказ")
            return {"result": "denied", "reason": "blocked_card", "event_id": eid, "incident_id": iid, "pass": p}

        today = date.today().isoformat()
        if (p['valid_from'] and today < p['valid_from']) or (p['valid_to'] and today > p['valid_to']):
            eid = EventJournal.write("вне срока действия", "отказ", point_id, pass_id=p['id'], card_number=card_number)
            return {"result": "denied", "reason": "expired", "event_id": eid, "pass": p}

        pt = db.get_point_by_id(point_id)
        if not db.is_zone_allowed(pt['zone_id'], p['access_level_id']):
            eid = EventJournal.write("нет прав доступа", "отказ", point_id, pass_id=p['id'], card_number=card_number)
            iid = MonitoringService.raise_alarm(point_id, f"Нет прав доступа: {card_number} → {pt['name']}", itype="Отказ")
            return {"result": "denied", "reason": "no_access", "event_id": eid, "incident_id": iid, "pass": p}

        eid = EventJournal.write("проход разрешён", "разрешён", point_id, pass_id=p['id'], card_number=card_number)

        if p['holder_type'] == 'employee':
            TimeTrackingService.record_event(p['holder_id'], pt, _now())
        elif p['holder_type'] == 'visitor' and p['holder_id']:
            db.add_visit(p['holder_id'], point_id, _now())

        return {"result": "granted", "event_id": eid, "pass": p}


class AdminService:
    get_departments = staticmethod(db.get_departments)
    get_zones = staticmethod(db.get_zones)
    get_access_levels = staticmethod(db.get_access_levels)
    get_access_points = staticmethod(db.get_access_points)
    get_devices = staticmethod(db.get_devices)
    get_zones_for_level = staticmethod(db.get_zones_for_level)
    set_zones_for_level = staticmethod(db.set_zones_for_level)
    get_employees = staticmethod(db.get_employees)
    delete_employee = staticmethod(db.delete_employee)
    get_free_guest_cards = staticmethod(db.get_free_guest_cards)
    get_active_guest_passes = staticmethod(db.get_active_guest_passes)
    return_guest_card = staticmethod(db.return_guest_card)
    set_pass_active = staticmethod(db.set_pass_active)
    mark_incident_processed = staticmethod(db.mark_incident_processed)
    add_access_level = staticmethod(db.add_access_level)
    update_access_level_details = staticmethod(db.update_access_level_details)
    delete_access_level = staticmethod(db.delete_access_level)
    add_access_point = staticmethod(db.add_access_point)
    delete_access_point = staticmethod(db.delete_access_point)

    @staticmethod
    def get_pass_by_card(card_number):
        p = db.find_pass_by_card(card_number)
        if not p: return None
        if p['holder_type'] == 'employee':
            p['holder'] = db.get_employee_by_id(p['holder_id'])
        elif p['holder_id']:
            p['holder'] = db.get_visitor_by_id(p['holder_id'])
        else:
            p['holder'] = None
        return p

    @staticmethod
    def get_passes_for_holder(holder_type, holder_id):
        return db.get_passes_by_holder(holder_type, holder_id)

    @staticmethod
    def issue_guest_pass(full_name, document, purpose, host_employee, card_number, level_id, valid_to):
        vid = db.add_visitor(full_name, document, purpose, host_employee)
        conn = db.get_connection()
        conn.execute("""UPDATE access_pass SET holder_id=?, valid_from=date('now'), valid_to=?, access_level_id=?, active=1 WHERE card_number=?""",
                     (vid, valid_to, level_id, card_number))
        conn.commit(); conn.close()
        return vid

    @staticmethod
    def add_new_pass(card_number, holder_type, holder_id, ptype, level_id, valid_to):
        db.add_new_pass(card_number, holder_type, holder_id, ptype, level_id, valid_to)

    @staticmethod
    def add_employee(personnel_number, full_name, position, dept_id, schedule_id, card_number, access_level_id):
        # Убрали телефон и почту
        return db.add_employee(personnel_number, full_name, position, dept_id, schedule_id, card_number, access_level_id)

    @staticmethod
    def update_photo(employee_id, photo_path):
        db.update_employee_photo(employee_id, photo_path)