import random
import sqlite3
from datetime import datetime, timedelta
from database import get_connection, init_db

MALE_NAMES = ["Александр", "Дмитрий", "Сергей", "Андрей", "Алексей", "Максим", "Евгений", "Иван", "Михаил", "Николай"]
FEMALE_NAMES = ["Елена", "Ольга", "Наталья", "Анна", "Мария", "Татьяна", "Ирина", "Светлана", "Юлия", "Екатерина"]
LAST_NAMES = ["Иванов", "Смирнов", "Кузнецов", "Попов", "Васильев", "Петров", "Соколов", "Михайлов", "Новиков",
              "Федоров", "Морозов", "Волков", "Алексеев", "Лебедев", "Семенов", "Егоров", "Павлов", "Козлов",
              "Степанов", "Николаев"]
PATRONYMICS_M = ["Иванович", "Петрович", "Сергеевич", "Александрович", "Дмитриевич", "Николаевич", "Андреевич",
                 "Алексеевич"]
PATRONYMICS_F = ["Ивановна", "Петровна", "Сергеевна", "Александровна", "Дмитриевна", "Николаевна", "Андреевна",
                 "Алексеевна"]
POSITIONS = ["Разработчик", "Старший разработчик", "Системный администратор", "Тестировщик", "Менеджер проектов",
             "Бизнес-аналитик", "Бухгалтер", "Специалист по кадрам", "Инженер", "Офис-менеджер", "Юрист", "Маркетолог"]


def generate_phone():
    return f"+37529{random.randint(1000000, 9999999)}"


def generate_email(name, lastname):
    translit = {'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e', 'ж': 'zh', 'з': 'z', 'и': 'i',
                'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't',
                'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '',
                'э': 'e', 'ю': 'yu', 'я': 'ya'}

    def tr(s): return "".join(translit.get(c.lower(), c) for c in s)

    return f"{tr(name)}.{tr(lastname)}@example.by"


def get_random_time():
    """Генерирует случайное время за последние 3 дня (с 8:00 до 19:00)"""
    day_offset = random.randint(0, 3)
    target_date = (datetime.now() - timedelta(days=day_offset)).date()
    hour = random.randint(8, 18)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    ts = datetime.combine(target_date, datetime.min.time()).replace(hour=hour, minute=minute, second=second)
    return ts


def populate_db(amount=10):
    init_db()
    conn = get_connection()
    c = conn.cursor()

    depts = c.execute("SELECT id FROM department").fetchall()
    schedules = c.execute("SELECT id FROM work_schedule").fetchall()
    if not depts or not schedules:
        print("ОШИБКА: Нет подразделений или графиков в базе!")
        return

    dept_ids = [d['id'] for d in depts]
    sched_ids = [s['id'] for s in schedules]

    max_emp = c.execute("SELECT MAX(CAST(personnel_number AS INTEGER)) FROM employee").fetchone()[0]
    max_card = c.execute(
        "SELECT MAX(CAST(SUBSTR(card_number, 5) AS INTEGER)) FROM access_pass WHERE card_number LIKE 'EMP-%'").fetchone()[
        0]

    emp_counter = (max_emp or 0) + 1
    card_counter = (max_card or 1000) + 1

    print(f"--- 1. Генерация {amount} случайных сотрудников ---")
    for _ in range(amount):
        is_male = random.choice([True, False])
        first_name = random.choice(MALE_NAMES if is_male else FEMALE_NAMES)
        last_name = random.choice(LAST_NAMES) + ("а" if not is_male else "")
        patronymic = random.choice(PATRONYMICS_M if is_male else PATRONYMICS_F)
        full_name = f"{last_name} {first_name} {patronymic}"

        try:
            c.execute("""INSERT INTO employee (personnel_number, full_name, position, department_id, schedule_id)
                         VALUES (?, ?, ?, ?, ?)""",
                      (f"{emp_counter:04d}", full_name, random.choice(POSITIONS), random.choice(dept_ids),
                       random.choice(sched_ids)))
            emp_id = c.lastrowid

            c.execute("""INSERT INTO access_pass (card_number, holder_type, holder_id, type, active, valid_from, valid_to, access_level_id)
                         VALUES (?, 'employee', ?, 'постоянный', 1, '2024-01-01', '2030-12-31', ?)""",
                      (f"EMP-{card_counter}", emp_id, random.choice([1, 2, 3, 4])))
            emp_counter += 1
            card_counter += 1
        except sqlite3.IntegrityError:
            continue

    print("--- 2. Добавление Кулдыковой и Самодумкина ---")
    manual_emps = [
        ("0018", "Кулдыкова Виктория Витальевна", "Менеджер", 5, "EMP-1123"),
        ("0029", "Самодумкин Сергей Александрович", "Разработчик", 1, "EMP-1067")
    ]
    for num, fio, pos, dept, card in manual_emps:
        try:
            c.execute("""INSERT INTO employee (personnel_number, full_name, position, department_id, schedule_id)
                         VALUES (?, ?, ?, ?, 1)""", (num, fio, pos, dept))
            emp_id = c.lastrowid
            c.execute("""INSERT INTO access_pass (card_number, holder_type, holder_id, type, active, valid_from, valid_to, access_level_id)
                         VALUES (?, 'employee', ?, 'постоянный', 1, '2024-01-01', '2030-12-31', 3)""", (card, emp_id))
            print(f"Добавлен: {fio}")
        except sqlite3.IntegrityError:
            pass

    print("--- 3. Генерация смен (часов работы) для ВСЕХ сотрудников ---")
    points = c.execute("SELECT id, name, type FROM access_point").fetchall()
    passes = c.execute("SELECT id, card_number, holder_id FROM access_pass WHERE holder_type='employee'").fetchall()

    c.execute("DELETE FROM timesheet_record")

    for emp in passes:
        num_shifts = random.randint(3, 5)
        for _ in range(num_shifts):
            day_offset = random.randint(0, 6)
            target_date = (datetime.now() - timedelta(days=day_offset)).date()
            day_str = target_date.isoformat()

            pt_in = next((p for p in points if p['type'] in ('вход', 'вход/выход')), points[0])
            pt_out = next((p for p in points if p['type'] in ('выход', 'вход/выход')), points[-1])

            in_hour, in_min = random.randint(8, 9), random.randint(0, 59)
            out_hour, out_min = random.randint(17, 18), random.randint(0, 59)

            ts_in = datetime.combine(target_date, datetime.min.time()).replace(hour=in_hour, minute=in_min)
            ts_out = datetime.combine(target_date, datetime.min.time()).replace(hour=out_hour, minute=out_min)

            c.execute("""INSERT INTO access_event (point_id, pass_id, card_number, timestamp, event_type, result)
                         VALUES (?, ?, ?, ?, 'проход разрешён', 'разрешён')""",
                      (pt_in['id'], emp['id'], emp['card_number'], ts_in.strftime("%Y-%m-%d %H:%M:%S")))
            c.execute("""INSERT INTO access_event (point_id, pass_id, card_number, timestamp, event_type, result)
                         VALUES (?, ?, ?, ?, 'проход разрешён', 'разрешён')""",
                      (pt_out['id'], emp['id'], emp['card_number'], ts_out.strftime("%Y-%m-%d %H:%M:%S")))

            c.execute("""INSERT INTO timesheet_record (employee_id, date, check_in, check_out)
                         VALUES (?, ?, ?, ?)""",
                      (emp['holder_id'], day_str, ts_in.strftime("%H:%M:%S"), ts_out.strftime("%H:%M:%S")))

    print("--- 4. Генерация 2 тревог (неизвестные карты) ---")
    for _ in range(2):
        pt = random.choice(points)
        ts_str = get_random_time().strftime("%Y-%m-%d %H:%M:%S")
        fake_card = f"UNKNOWN-{random.randint(100, 999)}"

        c.execute("""INSERT INTO access_event (point_id, card_number, timestamp, event_type, result)
                     VALUES (?, ?, ?, 'неизвестный пропуск', 'отказ')""", (pt['id'], fake_card, ts_str))
        c.execute("""INSERT INTO incident (timestamp, point_id, description, status, type)
                     VALUES (?, ?, ?, 'новый', 'Тревога')""",
                  (ts_str, pt['id'], f"Неизвестная карта {fake_card}, {pt['name']}"))

    print("--- 5. Генерация 5 отказов (нет прав/заблокирован) ---")
    for _ in range(5):
        pt = random.choice(points)
        emp = random.choice(passes)
        reason = random.choice(["пропуск заблокирован", "нет прав доступа"])
        ts_str = get_random_time().strftime("%Y-%m-%d %H:%M:%S")

        c.execute("""INSERT INTO access_event (point_id, pass_id, card_number, timestamp, event_type, result)
                     VALUES (?, ?, ?, ?, ?, 'отказ')""", (pt['id'], emp['id'], emp['card_number'], ts_str, reason))
        c.execute("""INSERT INTO incident (timestamp, point_id, description, status, type)
                     VALUES (?, ?, ?, 'новый', 'Отказ')""",
                  (ts_str, pt['id'], f"{emp['card_number']}: {reason} на {pt['name']}"))

    conn.commit()
    conn.close()
    print("ГОТОВО! База заполнена, события разбросаны по времени.")


if __name__ == "__main__":
    populate_db(18)