from sanic import Blueprint

from app.apis.books_blueprint import books_bp
from app.apis.users_blueprint import user_bp
from app.apis.example_blueprint import example

api = Blueprint.group(example, books_bp, user_bp)
