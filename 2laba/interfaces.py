from abc import ABC, abstractmethod
from datetime import date

class ICardReader(ABC):
    @abstractmethod
    def readCard(self) -> str: pass

class IPassRepository(ABC):
    @abstractmethod
    def findByBarcode(self, cardid: str): pass

    @abstractmethod
    def save(self, pass_obj): pass

class IAccessController(ABC):
    @abstractmethod
    def processPass(self, cardid: str, pointid: str) -> str: pass

    @abstractmethod
    def grantAccess(self, p: str) -> bool: pass

class IExecutiveDevice(ABC):
    @abstractmethod
    def open(self): pass

    @abstractmethod
    def close(self): pass

class IMonitoringService(ABC):
    @abstractmethod
    def showHolder(self, p): pass

    @abstractmethod
    def raiseAlarm(self, p): pass

class ITimeTrackingService(ABC):
    @abstractmethod
    def register(self, e): pass

    @abstractmethod
    def calcBalance(self, emp, d: date): pass

class IEventJournal(ABC):
    @abstractmethod
    def write(self, e): pass

    @abstractmethod
    def query(self, filters=None) -> list: pass