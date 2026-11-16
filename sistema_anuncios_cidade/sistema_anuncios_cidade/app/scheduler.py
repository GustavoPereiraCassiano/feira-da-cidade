from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os

_scheduler = None

def start_scheduler(app):
    global _scheduler
    if _scheduler is not None:
        return
    scheduler = BackgroundScheduler(daemon=True)
    def monthly_report():
        with app.app_context():
            from .reports import build_monthly_pdf
            build_monthly_pdf()
    scheduler.add_job(monthly_report, "cron", day=1, hour=7, minute=0, id="monthly_report", replace_existing=True)
    scheduler.start()
    _scheduler = scheduler
