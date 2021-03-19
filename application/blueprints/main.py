from flask import Blueprint, render_template
from flask import current_app as app

main_bp = Blueprint("main_bp", __name__)


@main_bp.route("/", methods=["GET"])
def index():
    return render_template('dashboard/index.html', username='Admin'), 200


@main_bp.route("/console", methods=["GET"])
def view_console():
    return render_template('dashboard/console.html'), 200


@app.errorhandler(404)
def page_not_found():
    return render_template('404.html'), 404
