from flask import Blueprint, jsonify
from services.isbn import lookup, normalize_isbn

scan_bp = Blueprint("scan", __name__)


@scan_bp.get("/isbn/<isbn>")
def scan_isbn(isbn):
    try:
        normalized = normalize_isbn(isbn)
    except ValueError as error:
        return jsonify(message=str(error)), 400
    data, status = lookup(normalized)
    return jsonify(data), status
