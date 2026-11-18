from abc import ABC, abstractmethod
from datetime import date
from interfaces import IExecutiveDevice

class CardHolder(ABC):
    def __init__(self, id: int, fullName: str, gender: str = 'male', photoPath: str = ''):
        self.id = id
        self.fullName = fullName
        self.gender = gender
        self.photoPath = photoPath

    @abstractmethod
    def getTitle(self) -> str: pass

class Employee(CardHolder):
    def __init__(self, id: int, fullName: str, personnelNumber: str, position: str, gender: str = 'male', photoPath: str = ''):
        super().__init__(id, fullName, gender, photoPath)
        self.personnelNumber = personnelNumber
        self.position = position

    def getTitle(self) -> str:
        return f"{self.fullName} ({self.position})"

class Visitor(CardHolder):
    def __init__(self, id: int, fullName: str, purpose: str, hostName: str, document: str = ''):
        super().__init__(id, fullName, 'male', '')
        self.purpose = purpose
        self.hostName = hostName
        self.document = document

    def getTitle(self) -> str:
        return f"Посетитель: {self.fullName}"

class Department:
    def __init__(self, name: str):
        self.name = name

class AccessPass:
    def __init__(self, cardNumber: str, type: str, active: bool, validUntil: str, level_id: int = 1, holder_id: int = None):
        self.cardNumber = cardNumber
        self.type = type
        self.active = bool(active)
        self.validUntil = validUntil
        self.level_id = level_id
        self.holder_id = holder_id

    def isValid(self, d: date) -> bool:
        return self.active

    def block(self):
        self.active = False

class AccessLevel:
    def __init__(self, name: str, timeFrom: str, timeTo: str, days: str = 'пн вт ср чт пт'):
        self.name = name
        self.timeFrom = timeFrom
        self.timeTo = timeTo
        self.days = days

    def allows(self, point: str, t: str) -> bool:
        return True

class Zone:
    def __init__(self, name: str, level: int):
        self.name = name
        self.level = level

class AccessPoint:
    def __init__(self, id: str, name: str, direction: str):
        self.id = id
        self.name = name
        self.direction = direction

class ExecutiveDevice(IExecutiveDevice, ABC):
    def __init__(self, id: str, opened: bool = False):
        self.id = id
        self.opened = opened

class Turnstile(ExecutiveDevice):
    def open(self): self.opened = True
    def close(self): self.opened = False

class MagneticLock(ExecutiveDevice):
    def open(self): self.opened = True
    def close(self): self.opened = False

class AccessEvent:
    def __init__(self, time: str, result: str, cardNumber: str = "", pointId: str = "", eventType: str = "Проход", description: str = ""):
        self.time = time
        self.result = result
        self.cardNumber = cardNumber
        self.pointId = pointId
        self.eventType = eventType
        self.description = description

class User:
    def __init__(self, login: str, full_name: str):
        self.login = login
        self.full_name = full_name
