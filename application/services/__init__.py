from application.services.task import scheduler

def init_app(app):
    scheduler.init_app(app)
    scheduler.start()

