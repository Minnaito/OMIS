"""Доменные классы — соответствуют диаграмме классов (рис. 6)."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Department:
    id: Optional[int] = None
    name: str = ""


@dataclass
class WorkSchedule:
    id: Optional[int] = None
    name: str = ""
    start_time: str = ""
    end_time: str = ""


@dataclass
class Zone:
    id: Optional[int] = None
    name: str = ""
    description: str = ""


@dataclass
class AccessLevel:
    id: Optional[int] = None
    name: str = ""
    description: str = ""


@dataclass
class Device:
    """«Устройство» из ER-диаграммы (рис. 1)."""
    id: Optional[int] = None
    type: str = ""


@dataclass
class AccessPoint:
    id: Optional[int] = None
    name: str = ""
    type: str = ""
    zone_id: Optional[int] = None
    device_id: Optional[int] = None


@dataclass
class CardHolder:
    id: Optional[int] = None
    full_name: str = ""


@dataclass
class Employee(CardHolder):
    personnel_number: str = ""
    position: str = ""
    phone: str = ""
    email: str = ""
    department_id: Optional[int] = None
    schedule_id: Optional[int] = None


@dataclass
class Visitor(CardHolder):
    document: str = ""
    purpose: str = ""


@dataclass
class AccessPass:
    id: Optional[int] = None
    card_number: str = ""
    holder_type: str = ""
    holder_id: Optional[int] = None
    type: str = ""
    active: bool = True
    valid_from: str = ""
    valid_to: str = ""
    access_level_id: Optional[int] = None
    level_name: str = ""


@dataclass
class AccessEvent:
    """Событие прохода — слабая сущность на «Точка доступа» (ER, рис. 1)."""
    id: Optional[int] = None
    point_id: Optional[int] = None
    pass_id: Optional[int] = None
    card_number: str = ""
    timestamp: str = ""
    event_type: str = ""
    result: str = ""


@dataclass
class TimesheetRecord:
    """Запись табеля — слабая сущность на «Сотрудник» (ER, рис. 1)."""
    id: Optional[int] = None
    employee_id: Optional[int] = None
    date: str = ""
    check_in: Optional[str] = None
    check_out: Optional[str] = None


@dataclass
class Incident:
    id: Optional[int] = None
    timestamp: str = ""
    point_id: Optional[int] = None
    description: str = ""
    status: str = "новый"


@dataclass
class Visit:
    """«Посещение» из ER (рис. 1) — M:N между Visitor и AccessPoint."""
    id: Optional[int] = None
    visitor_id: Optional[int] = None
    point_id: Optional[int] = None
    entry_time: str = ""


@dataclass
class Operator:
    id: Optional[int] = None
    login: str = ""
    password: str = ""
    role: str = ""
    full_name: str = ""