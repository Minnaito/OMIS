import os
import random
import sqlite3
import tkinter as tk
from datetime import datetime, timedelta

DB_NAME = "skud_system.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def ensure_assets():
    os.makedirs("assets", exist_ok=True)
    male_path = os.path.join("assets", "male.png")
    female_path = os.path.join("assets", "female.png")

    if not os.path.exists(male_path):
        img = tk.PhotoImage(width=110, height=130)
        img.put("#d9e2ec", to=(0, 0, 110, 130))
        img.put("#486581", to=(35, 20, 75, 60))
        img.put("#486581", to=(20, 68, 90, 125))
        img.write(male_path, format="png")

    if not os.path.exists(female_path):
        img = tk.PhotoImage(width=110, height=130)
        img.put("#fce8ec", to=(0, 0, 110, 130))
        img.put("#9b2c2c", to=(30, 18, 80, 65))
        img.put("#c53030", to=(22, 70, 88, 125))
        img.write(female_path, format="png")

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS Department (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS CardHolder (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullName TEXT NOT NULL,
            type TEXT NOT NULL,
            personnelNumber TEXT,
            position TEXT,
            schedule TEXT DEFAULT '09:00 - 18:00, пн-пт',
            purpose TEXT,
            document TEXT,
            hostName TEXT,
            gender TEXT DEFAULT 'male',
            photoPath TEXT DEFAULT '',
            department_id INTEGER,
            FOREIGN KEY(department_id) REFERENCES Department(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS AccessPass (
            cardNumber TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            active INTEGER NOT NULL,
            validUntil TEXT,
            level_id INTEGER,
            holder_id INTEGER,
            FOREIGN KEY(holder_id) REFERENCES CardHolder(id),
            FOREIGN KEY(level_id) REFERENCES AccessLevel(id)
        )
    """)
    cursor.execute("CREATE TABLE IF NOT EXISTS AccessLevel (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, timeFrom TEXT, timeTo TEXT, days TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS Zone (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, level INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS AccessPoint (id TEXT PRIMARY KEY, name TEXT NOT NULL, direction TEXT, zone_id INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS AccessLevelPoint (level_id INTEGER, point_id TEXT, PRIMARY KEY(level_id, point_id))")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS AccessEvent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT NOT NULL,
            type TEXT NOT NULL,
            result TEXT NOT NULL,
            description TEXT,
            card_number TEXT,
            point_id TEXT,
            status TEXT DEFAULT 'не обработан',
            comment TEXT DEFAULT ''
        )
    """)
    cursor.execute("CREATE TABLE IF NOT EXISTS GuestCardPool (cardNumber TEXT PRIMARY KEY, is_free INTEGER DEFAULT 1)")

    cursor.execute("SELECT COUNT(*) FROM Department")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO Department (name) VALUES (?)", [
            ('Отдел разработки',), ('Руководство',), ('Бухгалтерия',), ('Служба безопасности',), ('Отдел кадров',), ('ИТ-отдел',)
        ])

        cursor.executemany("INSERT INTO Zone (name, level) VALUES (?, ?)", [
            ('Периметр', 0), ('Холл', 1), ('Техзона', 2)
        ])

        cursor.executemany("INSERT INTO AccessPoint (id, name, direction, zone_id) VALUES (?, ?, ?, ?)", [
            ('KP1', 'КПП Южный', 'вход/выход', 1),
            ('TP1', 'Турникет №1', 'вход/выход', 2),
            ('TP2', 'Турникет №2', 'вход/выход', 2),
            ('SRV', 'Серверная', 'вход', 3)
        ])

        cursor.executemany("INSERT INTO AccessLevel (name, timeFrom, timeTo, days) VALUES (?, ?, ?, ?)", [
            ('Уровень 1 — общий', '08:00', '19:00', 'пн вт ср чт пт'),
            ('Уровень 2 — офисный', '07:00', '21:00', 'пн вт ср чт пт'),
            ('Уровень 3 — расширенный', '00:00', '23:59', 'пн вт ср чт пт сб вс'),
            ('Гостевой (1 этаж)', '09:00', '18:00', 'пн вт ср чт пт')
        ])

        cursor.executemany("INSERT INTO AccessLevelPoint (level_id, point_id) VALUES (?, ?)", [
            (1, 'KP1'), (1, 'TP1'), (1, 'TP2'),
            (2, 'KP1'), (2, 'TP1'), (2, 'TP2'),
            (3, 'KP1'), (3, 'TP1'), (3, 'TP2'), (3, 'SRV'),
            (4, 'KP1'), (4, 'TP1')
        ])

        staff_seed = [
            ("Иванов Иван Иванович", "0001", "Генеральный директор", 2, "male", 3, 1),
            ("Петров Пётр Петрович", "0002", "Ведущий разработчик", 1, "male", 3, 1),
            ("Сидоров Сергей Сергеевич", "0003", "Инженер-программист", 1, "male", 2, 1),
            ("Кузнецова Анна Викторовна", "0004", "Бухгалтер", 3, "female", 1, 1),
            ("Смирнова Ольга Игоревна", "0005", "Главный бухгалтер", 3, "female", 2, 0),
            ("Морозов Дмитрий Олегович", "0006", "Системный администратор", 6, "male", 3, 1),
            ("Волков Алексей Николаевич", "0007", "Начальник службы безопасности", 4, "male", 3, 1),
            ("Семенов Михаил Андреевич", "0008", "Специалист по кадрам", 5, "male", 2, 1),
            ("Степанов Михаил Алексеевич", "0010", "Экономист", 3, "male", 1, 1),
            ("Иванова Екатерина Николаевна", "0011", "Бухгалтер-кассир", 3, "female", 1, 1),
            ("Новиков Александр Николаевич", "0012", "HR-менеджер", 5, "male", 2, 1),
            ("Кузнецов Евгений Иванович", "0013", "Специалист отдела кадров", 5, "male", 2, 1),
            ("Павлов Дмитрий Дмитриевич", "0014", "Финансовый аналитик", 3, "male", 1, 1),
            ("Кузнецов Дмитрий Сергеевич", "0015", "Старший бухгалтер", 3, "male", 2, 1),
            ("Лебедева Татьяна Сергеевна", "0016", "DevOps-инженер", 6, "female", 3, 1),
            ("Михайлов Алексей Николаевич", "0018", "Сетевой инженер", 6, "male", 3, 1),
            ("Новикова Мария Алексеевна", "0019", "Специалист техподдержки", 6, "female", 2, 1),
            ("Морозова Анна Сергеевна", "0020", "Backend-разработчик", 1, "female", 2, 1),
            ("Семенова Мария Александровна", "0021", "QA-инженер", 6, "female", 2, 1),
            ("Лебедев Евгений Андреевич", "0022", "Исполнительный директор", 2, "male", 3, 1),
            ("Кузнецова Юлия Николаевна", "0023", "Frontend-разработчик", 1, "female", 2, 1),
            ("Семёнов Сергей Николаевич", "0024", "Дежурный охранник", 4, "male", 3, 1),
        ]

        generated_passes = []
        for idx, (fio, tab, pos, dep_id, gender, lvl_id, active) in enumerate(staff_seed, start=1):
            photo = f"assets/{gender}.png"
            sched = "08:00 - 20:00, сменный" if dep_id == 4 else "09:00 - 18:00, пн-пт"
            cursor.execute("""
                INSERT INTO CardHolder (fullName, type, personnelNumber, position, schedule, gender, photoPath, department_id)
                VALUES (?, 'Employee', ?, ?, ?, ?, ?, ?)
            """, (fio, tab, pos, sched, gender, photo, dep_id))

            card_num = f"0041{int(tab):03d}"
            cursor.execute("""
                INSERT INTO AccessPass (cardNumber, type, active, validUntil, level_id, holder_id)
                VALUES (?, 'постоянный', ?, '2030-12-31', ?, ?)
            """, (card_num, active, lvl_id, idx))
            generated_passes.append((card_num, active, lvl_id))

        for i in range(1, 21):
            cursor.execute("INSERT INTO GuestCardPool (cardNumber, is_free) VALUES (?, 1)", (f"00500{i:02d}",))

        # Генерация событий за ноябрь 2026 для отчетов и монитора
        base_date = datetime(2026, 11, 18, 18, 0, 0)
        point_names = {"TP1": "Турникет №1", "TP2": "Турникет №2", "KP1": "КПП Южный", "SRV": "Серверная"}

        events = []
        for i in range(40):
            days_ago = random.randint(0, 10)
            hour = random.randint(8, 19)
            minute = random.randint(0, 59)
            ev_dt = base_date - timedelta(days=days_ago, hours=random.randint(0, 5), minutes=minute)
            ev_time_str = ev_dt.strftime("%Y-%m-%d %H:%M:%S")

            card_num, is_act, lvl = random.choice(generated_passes)
            pt = random.choice(["TP1", "TP2", "KP1", "SRV"])

            if not is_act:
                events.append((ev_time_str, "Отказ", "ОТКАЗ", f"{card_num}: пропуск заблокирован на {point_names[pt]}", card_num, pt, "не обработан"))
            elif pt == "SRV" and lvl < 3:
                events.append((ev_time_str, "Отказ", "ОТКАЗ", f"{card_num}: нет прав доступа на Серверная", card_num, pt, "не обработан"))
            else:
                events.append((ev_time_str, "Проход", "разрешён", f"Штатный проход через {point_names[pt]}", card_num, pt, "обработан"))

        events.append(("2026-11-18 09:15:00", "Тревога", "ТРЕВОГА", "Неизвестная карта UNKNOWN-235, Турникет №1", "UNKNOWN-235", "TP1", "не обработан"))
        events.append(("2026-11-15 14:20:00", "Тревога", "ТРЕВОГА", "Неизвестная карта UNKNOWN-597, Турникет №2", "UNKNOWN-597", "TP2", "обработан"))

        events.sort(key=lambda x: x[0], reverse=True)
        cursor.executemany("""
            INSERT INTO AccessEvent (time, type, result, description, card_number, point_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, events)

    conn.commit()
    conn.close()
