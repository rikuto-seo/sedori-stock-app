import requests

from flask import Blueprint, jsonify


scan_bp = Blueprint("scan", __name__)


@scan_bp.route("/isbn/<isbn>")
def scan_isbn(isbn):

    url = (
        f"https://www.googleapis.com/books/v1/volumes"
        f"?q=isbn:{isbn}"
    )

    response = requests.get(url)

    data = response.json()

    items = data.get("items")

    if not items:

        return jsonify({
            "error": "Book not found"
        }), 404

    volume_info = items[0]["volumeInfo"]

    return jsonify({

        "title": volume_info.get("title"),

        "publisher": volume_info.get("publisher"),

        "genre": (
            volume_info.get("categories", [None])[0]
        )

    })