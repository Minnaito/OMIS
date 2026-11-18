from database import init_db, ensure_assets
from services import PassRepository, EventJournal, MonitoringService, TimeTrackingService, AccessController
from ui import OperatorApp

def main():
    init_db()
    ensure_assets()

    pass_repo = PassRepository()
    event_journal = EventJournal()
    monitoring_service = MonitoringService()
    time_service = TimeTrackingService()

    access_controller = AccessController(
        repository=pass_repo,
        journal=event_journal,
        monitoring=monitoring_service,
        time_tracking=time_service
    )

    app = OperatorApp(controller=access_controller, journal=event_journal)
    app.mainloop()

if __name__ == "__main__":
    main()
