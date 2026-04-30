from flask import Blueprint, render_template


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    return render_template("pages/home.html")


@main_bp.route("/inventory")
def inventory():
    return render_template(
        "pages/inventory.html"
    )


@main_bp.route("/costs")
def costs():
    return render_template(
        "pages/costs.html"
    )

@main_bp.route("/analytics")
def analytics():
    return render_template("pages/analytics.html")