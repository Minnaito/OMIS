"""Схема SQLite + DAO. Соответствует ER-диаграмме."""
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "skud.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS department (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS work_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, start_time TEXT, end_time TEXT, days TEXT);
    CREATE TABLE IF NOT EXISTS zone (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT);
    CREATE TABLE IF NOT EXISTS access_level (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT, 
        time_start TEXT DEFAULT '08:00', time_end TEXT DEFAULT '19:00', days TEXT DEFAULT 'пн вт ср чт пт');
    CREATE TABLE IF NOT EXISTS zone_level (
        zone_id INTEGER, level_id INTEGER, PRIMARY KEY (zone_id, level_id),
        FOREIGN KEY (zone_id) REFERENCES zone(id),
        FOREIGN KEY (level_id) REFERENCES access_level(id));
    CREATE TABLE IF NOT EXISTS device (
        id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS access_point (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
        zone_id INTEGER, device_id INTEGER, type TEXT,
        FOREIGN KEY (zone_id) REFERENCES zone(id),
        FOREIGN KEY (device_id) REFERENCES device(id));
    CREATE TABLE IF NOT EXISTS employee (
        id INTEGER PRIMARY KEY AUTOINCREMENT, personnel_number TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL, position TEXT, phone TEXT, email TEXT,
        department_id INTEGER, schedule_id INTEGER, photo TEXT,
        FOREIGN KEY (department_id) REFERENCES department(id),
        FOREIGN KEY (schedule_id) REFERENCES work_schedule(id));
    CREATE TABLE IF NOT EXISTS visitor (
        id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT NOT NULL, document TEXT, purpose TEXT, host_employee TEXT);
    CREATE TABLE IF NOT EXISTS access_pass (
        id INTEGER PRIMARY KEY AUTOINCREMENT, card_number TEXT UNIQUE NOT NULL,
        holder_type TEXT NOT NULL, holder_id INTEGER, type TEXT,
        active INTEGER DEFAULT 1, valid_from TEXT, valid_to TEXT,
        access_level_id INTEGER,
        FOREIGN KEY (access_level_id) REFERENCES access_level(id));
    CREATE TABLE IF NOT EXISTS access_event (
        id INTEGER PRIMARY KEY AUTOINCREMENT, point_id INTEGER NOT NULL, pass_id INTEGER,
        card_number TEXT, timestamp TEXT NOT NULL, event_type TEXT, result TEXT,
        FOREIGN KEY (point_id) REFERENCES access_point(id));
    CREATE TABLE IF NOT EXISTS timesheet_record (
        id INTEGER PRIMARY KEY AUTOINCREMENT, employee_id INTEGER NOT NULL, date TEXT NOT NULL,
        check_in TEXT, check_out TEXT,
        FOREIGN KEY (employee_id) REFERENCES employee(id));
    CREATE TABLE IF NOT EXISTS incident (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, point_id INTEGER,
        description TEXT, status TEXT DEFAULT 'новый', type TEXT DEFAULT 'Тревога', comment TEXT,
        FOREIGN KEY (point_id) REFERENCES access_point(id));
    CREATE TABLE IF NOT EXISTS visit (
        id INTEGER PRIMARY KEY AUTOINCREMENT, visitor_id INTEGER NOT NULL,
        point_id INTEGER NOT NULL, entry_time TEXT NOT NULL,
        FOREIGN KEY (visitor_id) REFERENCES visitor(id),
        FOREIGN KEY (point_id) REFERENCES access_point(id));
    CREATE TABLE IF NOT EXISTS operator (
        id INTEGER PRIMARY KEY AUTOINCREMENT, login TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL, role TEXT NOT NULL, full_name TEXT);
    """)
    conn.commit()

    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(employee)")
    if 'photo' not in [row['name'] for row in cursor.fetchall()]:
        cursor.execute("ALTER TABLE employee ADD COLUMN photo TEXT")
        conn.commit()

    cursor.execute("PRAGMA table_info(work_schedule)")
    if 'days' not in [row['name'] for row in cursor.fetchall()]:
        cursor.execute("ALTER TABLE work_schedule ADD COLUMN days TEXT")
        cursor.execute("UPDATE work_schedule SET days='пн-пт'")
        conn.commit()

    cursor.execute("PRAGMA table_info(visitor)")
    if 'host_employee' not in [row['name'] for row in cursor.fetchall()]:
        cursor.execute("ALTER TABLE visitor ADD COLUMN host_employee TEXT")
        conn.commit()

    cursor.execute("PRAGMA table_info(access_level)")
    al_cols = [row['name'] for row in cursor.fetchall()]
    if 'time_start' not in al_cols:
        cursor.execute("ALTER TABLE access_level ADD COLUMN time_start TEXT DEFAULT '08:00'")
        cursor.execute("ALTER TABLE access_level ADD COLUMN time_end TEXT DEFAULT '19:00'")
        cursor.execute("ALTER TABLE access_level ADD COLUMN days TEXT DEFAULT 'пн вт ср чт пт'")
        conn.commit()

    cursor.execute("PRAGMA table_info(incident)")
    inc_cols = [row['name'] for row in cursor.fetchall()]
    if 'type' not in inc_cols:
        cursor.execute("ALTER TABLE incident ADD COLUMN type TEXT DEFAULT 'Тревога'")
        cursor.execute("ALTER TABLE incident ADD COLUMN comment TEXT")
        conn.commit()

    if conn.execute("SELECT COUNT(*) FROM operator").fetchone()[0] == 0:
        _seed(conn)

    guest_levels = [
        ("Гостевой (1 этаж)", "Только 1 этаж"), ("Гостевой (2 этаж)", "Только 2 этаж"),
        ("Гостевой (серверная)", "Только серверная"), ("Гостевой VIP", "Переговорные комнаты")
    ]
    for name, desc in guest_levels:
        cursor.execute("SELECT id FROM access_level WHERE name=?", (name,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO access_level (name, description) VALUES (?,?)", (name, desc))
    conn.commit()

    cursor.execute("SELECT id FROM access_level WHERE name LIKE 'Гостевой%' LIMIT 1")
    level_row = cursor.fetchone()
    guest_level_id = level_row['id'] if level_row else 1

    cursor.execute("DELETE FROM access_pass WHERE card_number LIKE 'GUEST-%' AND holder_id IS NULL")
    conn.commit()

    for i in range(1, 21):
        card = f"GUEST-{i}"
        cursor.execute("SELECT id FROM access_pass WHERE card_number=?", (card,))
        if not cursor.fetchone():
            cursor.execute("""INSERT INTO access_pass (card_number, holder_type, holder_id, type, active, valid_from, valid_to, access_level_id)
                              VALUES (?, 'visitor', NULL, 'гостевой', 1, '2024-01-01', '2030-12-31', ?)""", (card, guest_level_id))
    conn.commit()
    conn.close()


def _seed(conn):
    c = conn.cursor()
    for name in ["Отдел разработки", "Бухгалтерия", "Отдел кадров", "Служба безопасности", "Руководство", "IT-отдел"]:
        c.execute("INSERT INTO department (name) VALUES (?)", (name,))

    for name, desc in [("Холл","Входная зона"), ("Офис","Офисные помещения"), ("Техзона","Серверная комната"), ("Периметр","Территория")]:
        c.execute("INSERT INTO zone (name, description) VALUES (?,?)", (name, desc))

    for name, desc in [
        ("Уровень 1 — общий","Территория"), ("Уровень 2 — офисный","Офис"),
        ("Уровень 3 — расширенный","Офис + серверная"), ("Уровень 4 — полный","Все зоны")]:
        c.execute("INSERT INTO access_level (name, description) VALUES (?,?)", (name, desc))

    for z, l in [(1,1),(1,2),(1,3),(1,4),(2,2),(2,3),(2,4),(3,3),(3,4),(4,4)]:
        c.execute("INSERT INTO zone_level (zone_id, level_id) VALUES (?,?)", (z, l))

    for t in ("Turnstile", "MagneticLock"):
        c.execute("INSERT INTO device (type) VALUES (?)", (t,))

    for name, zone, t, dev in [
        ("Турникет №1", 1, "вход/выход", 1), ("Турникет №2", 1, "вход/выход", 1),
        ("Серверная", 3, "вход", 2), ("КПП Южный", 4, "вход/выход", 2)]:
        c.execute("INSERT INTO access_point (name, zone_id, device_id, type) VALUES (?,?,?,?)", (name, zone, dev, t))

    for name, s, e, d in [("Стандартный 9-18", "09:00", "18:00", "пн-пт"), ("Смена утро 8-17", "08:00", "17:00", "пн-пт")]:
        c.execute("INSERT INTO work_schedule (name, start_time, end_time, days) VALUES (?,?,?,?)", (name, s, e, d))

    employees = [
        ("0001","Иванов Иван Иванович","Директор",5,1),
        ("0002","Петров Петр Петрович","Главный инженер",1,1),
        ("0003","Сидоров Сергей Сергеевич","Разработчик",1,2),
        ("0004","Кузнецова Анна Викторовна","Бухгалтер",2,1),
        ("0005","Смирнова Ольга Игоревна","HR-специалист",3,1),
        ("0006","Морозов Дмитрий Олегович","Системный администратор",6,1),
        ("0007","Волков Алексей Николаевич","Охранник",4,2),
    ]
    for row in employees:
        c.execute("""INSERT INTO employee (personnel_number, full_name, position, department_id, schedule_id)
                     VALUES (?,?,?,?,?)""", row)

    for i in range(1, 8):
        level = 4 if i in (1, 2) else 3 if i in (3, 6) else 2
        c.execute("""INSERT INTO access_pass (card_number, holder_type, holder_id, type, active, valid_from, valid_to, access_level_id)
                     VALUES (?, 'employee', ?, 'постоянный', 1, '2024-01-01', '2030-12-31', ?)""", (f"EMP-{1000+i}", i, level))

    for login, pwd, role, name in [
        ("guard","guard","security_guard","Волков Алексей Николаевич"),
        ("hr","hr","hr_specialist","Смирнова Ольга Игоревна"),
        ("sysadmin","sysadmin","system_admin","Морозов Дмитрий Олегович")]:
        c.execute("INSERT INTO operator (login, password, role, full_name) VALUES (?,?,?,?)", (login, pwd, role, name))

    now = datetime.now()
    for i, (card, point, res, evt) in enumerate([
        ("EMP-1001", 1, "разрешён", "проход разрешён"), ("EMP-1003", 1, "разрешён", "проход разрешён"),
        ("UNKNOWN-1", 1, "отказ", "неизвестный пропуск"), ("EMP-1004", 2, "разрешён", "проход разрешён")]):
        ts = (now - timedelta(minutes=10 - i*2)).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""INSERT INTO access_event (point_id, card_number, timestamp, event_type, result)
                     VALUES (?,?,?,?,?)""", (point, card, ts, evt, res))
    conn.commit()


def find_operator(login, password):
    conn = get_connection(); r = conn.execute("SELECT * FROM operator WHERE login=? AND password=?", (login, password)).fetchone(); conn.close()
    return dict(r) if r else None

def find_pass_by_card(card_number):
    conn = get_connection(); r = conn.execute("""SELECT ap.*, al.name AS level_name FROM access_pass ap
                        LEFT JOIN access_level al ON ap.access_level_id = al.id WHERE ap.card_number=?""", (card_number,)).fetchone(); conn.close()
    return dict(r) if r else None

def get_passes_by_holder(holder_type, holder_id):
    conn = get_connection(); rows = [dict(r) for r in conn.execute("""SELECT ap.*, al.name AS level_name
                                             FROM access_pass ap LEFT JOIN access_level al ON ap.access_level_id=al.id
                                             WHERE holder_type=? AND holder_id=?""", (holder_type, holder_id)).fetchall()]; conn.close()
    return rows

def set_pass_active(pass_id, active):
    conn = get_connection(); conn.execute("UPDATE access_pass SET active=? WHERE id=?", (1 if active else 0, pass_id)); conn.commit(); conn.close()

def get_free_guest_cards():
    conn = get_connection(); rows = [dict(r) for r in conn.execute("""SELECT * FROM access_pass
                                             WHERE holder_type='visitor' AND holder_id IS NULL AND type='гостевой'""").fetchall()]; conn.close()
    return rows

def get_active_guest_passes():
    conn = get_connection()
    q = """SELECT ap.card_number, v.full_name, v.document, v.purpose, v.host_employee, ap.valid_to
           FROM access_pass ap JOIN visitor v ON ap.holder_id = v.id
           WHERE ap.holder_type='visitor' AND ap.holder_id IS NOT NULL"""
    rows = [dict(r) for r in conn.execute(q).fetchall()]; conn.close(); return rows

def return_guest_card(card_number):
    conn = get_connection(); conn.execute("UPDATE access_pass SET holder_id=NULL WHERE card_number=?", (card_number,)); conn.commit(); conn.close()

def add_new_pass(card_number, holder_type, holder_id, ptype, access_level_id, valid_to):
    conn = get_connection()
    conn.execute("""INSERT INTO access_pass (card_number, holder_type, holder_id, type, active, valid_from, valid_to, access_level_id)
                    VALUES (?, ?, ?, ?, 1, date('now'), ?, ?)""", (card_number, holder_type, holder_id, ptype, valid_to, access_level_id))
    conn.commit(); conn.close()

def get_employees(dept_id=None):
    conn = get_connection()
    q = """SELECT e.id, e.personnel_number, e.full_name, e.position, e.photo,
                  d.name AS department_name, ws.start_time, ws.end_time, ws.days, 
                  MAX(ap.card_number) AS card_number
           FROM employee e 
           LEFT JOIN department d ON e.department_id=d.id 
           LEFT JOIN work_schedule ws ON e.schedule_id=ws.id
           LEFT JOIN access_pass ap ON e.id = ap.holder_id AND ap.holder_type = 'employee' AND ap.active = 1"""
    params = []
    if dept_id:
        q += " WHERE e.department_id=?"; params.append(dept_id)
    q += " GROUP BY e.id ORDER BY e.full_name"
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]; conn.close(); return rows

def get_employee_by_id(emp_id):
    conn = get_connection()
    r = conn.execute("""SELECT e.*, d.name AS department_name, ws.start_time, ws.end_time, ws.days
                        FROM employee e LEFT JOIN department d ON e.department_id=d.id LEFT JOIN work_schedule ws ON e.schedule_id=ws.id
                        WHERE e.id=?""", (emp_id,)).fetchone(); conn.close()
    return dict(r) if r else None

def update_employee_photo(employee_id, photo_path):
    conn = get_connection(); conn.execute("UPDATE employee SET photo=? WHERE id=?", (photo_path, employee_id)); conn.commit(); conn.close()

def add_employee(personnel_number, full_name, position, dept_id, schedule_id, card_number, access_level_id):
    conn = get_connection(); c = conn.cursor()
    c.execute("""INSERT INTO employee (personnel_number, full_name, position, phone, email, department_id, schedule_id)
                 VALUES (?,?,?, NULL, NULL, ?,?)""", (personnel_number, full_name, position, dept_id, schedule_id))
    eid = c.lastrowid
    c.execute("""INSERT INTO access_pass (card_number, holder_type, holder_id, type, active, valid_from, valid_to, access_level_id)
                 VALUES (?, 'employee', ?, 'постоянный', 1, date('now'), '2030-12-31', ?)""", (card_number, eid, access_level_id))
    conn.commit(); conn.close(); return eid

def delete_employee(employee_id):
    conn = get_connection(); c = conn.cursor()
    c.execute("DELETE FROM access_pass WHERE holder_type='employee' AND holder_id=?", (employee_id,))
    c.execute("DELETE FROM employee WHERE id=?", (employee_id,))
    conn.commit(); conn.close()

def get_visitor_by_id(vid):
    conn = get_connection(); r = conn.execute("SELECT * FROM visitor WHERE id=?", (vid,)).fetchone(); conn.close()
    return dict(r) if r else None

def add_visitor(full_name, document, purpose, host_employee=""):
    conn = get_connection(); c = conn.cursor()
    c.execute("INSERT INTO visitor (full_name, document, purpose, host_employee) VALUES (?,?,?,?)", (full_name, document, purpose, host_employee))
    vid = c.lastrowid; conn.commit(); conn.close(); return vid

def get_departments():
    conn = get_connection(); rows = [dict(r) for r in conn.execute("SELECT * FROM department ORDER BY name").fetchall()]; conn.close(); return rows

def get_zones():
    conn = get_connection(); rows = [dict(r) for r in conn.execute("SELECT * FROM zone ORDER BY id").fetchall()]; conn.close(); return rows

def get_access_levels():
    conn = get_connection(); rows = [dict(r) for r in conn.execute("SELECT * FROM access_level ORDER BY id").fetchall()]; conn.close(); return rows

def add_access_level(name):
    conn = get_connection(); conn.execute("INSERT INTO access_level (name, description) VALUES (?, '')", (name,)); conn.commit(); conn.close()

def update_access_level_details(level_id, t_start, t_end, days):
    conn = get_connection(); conn.execute("UPDATE access_level SET time_start=?, time_end=?, days=? WHERE id=?", (t_start, t_end, days, level_id)); conn.commit(); conn.close()

def delete_access_level(level_id):
    conn = get_connection()
    used = conn.execute("SELECT COUNT(*) FROM access_pass WHERE access_level_id=?", (level_id,)).fetchone()[0]
    if used > 0:
        conn.close(); return False
    conn.execute("DELETE FROM zone_level WHERE level_id=?", (level_id,))
    conn.execute("DELETE FROM access_level WHERE id=?", (level_id,))
    conn.commit(); conn.close(); return True

def get_access_points():
    conn = get_connection(); rows = [dict(r) for r in conn.execute("""SELECT ap.*, z.name AS zone_name, d.type AS device_type
                                             FROM access_point ap LEFT JOIN zone z ON ap.zone_id=z.id LEFT JOIN device d ON ap.device_id=d.id ORDER BY ap.id""").fetchall()]; conn.close(); return rows

def get_devices():
    conn = get_connection(); rows = [dict(r) for r in conn.execute("SELECT * FROM device ORDER BY id").fetchall()]; conn.close(); return rows

def add_access_point(name, zone_id, device_id, ptype):
    conn = get_connection()
    conn.execute("INSERT INTO access_point (name, zone_id, device_id, type) VALUES (?,?,?,?)", (name, zone_id, device_id, ptype))
    conn.commit(); conn.close()

def delete_access_point(point_id):
    conn = get_connection()
    conn.execute("DELETE FROM access_event WHERE point_id=?", (point_id,))
    conn.execute("DELETE FROM incident WHERE point_id=?", (point_id,))
    conn.execute("DELETE FROM visit WHERE point_id=?", (point_id,))
    conn.execute("DELETE FROM access_point WHERE id=?", (point_id,))
    conn.commit(); conn.close()

def get_point_by_id(pid):
    conn = get_connection(); r = conn.execute("SELECT * FROM access_point WHERE id=?", (pid,)).fetchone(); conn.close()
    return dict(r) if r else None

def get_zones_for_level(level_id):
    conn = get_connection(); rows = [dict(r) for r in conn.execute("""SELECT z.* FROM zone z JOIN zone_level zl ON z.id=zl.zone_id WHERE zl.level_id=?""", (level_id,)).fetchall()]; conn.close(); return rows

def set_zones_for_level(level_id, zone_ids):
    conn = get_connection(); c = conn.cursor()
    c.execute("DELETE FROM zone_level WHERE level_id=?", (level_id,))
    for z in zone_ids: c.execute("INSERT INTO zone_level (zone_id, level_id) VALUES (?,?)", (z, level_id))
    conn.commit(); conn.close()

def is_zone_allowed(zone_id, level_id):
    conn = get_connection(); r = conn.execute("SELECT 1 FROM zone_level WHERE zone_id=? AND level_id=?", (zone_id, level_id)).fetchone(); conn.close()
    return bool(r)

def add_event(point_id, pass_id, card_number, timestamp, event_type, result):
    conn = get_connection()
    eid = conn.execute("""INSERT INTO access_event (point_id, pass_id, card_number, timestamp, event_type, result)
                          VALUES (?,?,?,?,?,?)""", (point_id, pass_id, card_number, timestamp, event_type, result)).lastrowid
    conn.commit(); conn.close(); return eid

def get_events(point_id=None, limit=200):
    conn = get_connection()
    q = """SELECT ae.*, ap.name AS point_name, COALESCE(e.full_name, v.full_name, 'Неизвестно') AS holder_name
           FROM access_event ae LEFT JOIN access_point ap ON ae.point_id = ap.id
           LEFT JOIN access_pass p ON ae.card_number = p.card_number
           LEFT JOIN employee e ON p.holder_type='employee' AND p.holder_id = e.id
           LEFT JOIN visitor v ON p.holder_type='visitor' AND p.holder_id = v.id WHERE 1=1"""
    params = []
    if point_id: q += " AND ae.point_id=?"; params.append(point_id)
    q += " ORDER BY ae.timestamp DESC LIMIT ?"; params.append(limit)
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]; conn.close(); return rows

def add_incident(timestamp, point_id, description, itype="Тревога"):
    conn = get_connection(); iid = conn.execute("INSERT INTO incident (timestamp, point_id, description, type) VALUES (?,?,?,?)", (timestamp, point_id, description, itype)).lastrowid
    conn.commit(); conn.close(); return iid

def get_incidents(status=None):
    conn = get_connection()
    q = """SELECT i.*, ap.name AS point_name FROM incident i LEFT JOIN access_point ap ON i.point_id = ap.id WHERE 1=1"""
    params = []
    if status: q += " AND i.status=?"; params.append(status)
    q += " ORDER BY i.timestamp DESC"
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]; conn.close(); return rows

def mark_incident_processed(incident_id, comment=""):
    conn = get_connection(); conn.execute("UPDATE incident SET status='обработан', comment=? WHERE id=?", (comment, incident_id)); conn.commit(); conn.close()

def add_visit(visitor_id, point_id, entry_time):
    conn = get_connection(); conn.execute("INSERT INTO visit (visitor_id, point_id, entry_time) VALUES (?,?,?)", (visitor_id, point_id, entry_time)); conn.commit(); conn.close()

def get_timesheet(employee_id, day):
    conn = get_connection(); r = conn.execute("SELECT * FROM timesheet_record WHERE employee_id=? AND date=?", (employee_id, day)).fetchone(); conn.close()
    return dict(r) if r else None

def add_timesheet(employee_id, day, check_in=None, check_out=None):
    conn = get_connection(); conn.execute("INSERT INTO timesheet_record (employee_id, date, check_in, check_out) VALUES (?,?,?,?)", (employee_id, day, check_in, check_out)); conn.commit(); conn.close()

def update_timesheet(rec_id, check_in=None, check_out=None):
    conn = get_connection()
    if check_in is not None: conn.execute("UPDATE timesheet_record SET check_in=? WHERE id=?", (check_in, rec_id))
    if check_out is not None: conn.execute("UPDATE timesheet_record SET check_out=? WHERE id=?", (check_out, rec_id))
    conn.commit(); conn.close()

def get_discipline_data(dept_id, date_from, date_to):
    conn = get_connection()
    q = """SELECT e.id, e.full_name, e.personnel_number, ws.start_time, ws.end_time, ts.date, ts.check_in, ts.check_out
           FROM employee e LEFT JOIN work_schedule ws ON e.schedule_id = ws.id
           LEFT JOIN timesheet_record ts ON ts.employee_id = e.id AND ts.date BETWEEN ? AND ? WHERE 1=1"""
    params = [date_from, date_to]
    if dept_id: q += " AND e.department_id=?"; params.append(dept_id)
    q += " ORDER BY e.full_name, ts.date"
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]; conn.close(); return rows