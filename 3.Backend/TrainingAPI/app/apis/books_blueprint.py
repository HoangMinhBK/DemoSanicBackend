import uuid
import json
from app.utils.jwt_utils import generate_jwt
from app.decorators.auth import protected, check_token

from sanic import Blueprint
from sanic.response import json

from app.constants.cache_constants import CacheConstants
from app.databases.mongodb import MongoDB
from app.databases.redis_cached import get_cache, set_cache
from app.decorators.json_validator import validate_with_jsonschema

# from app.hooks.error import ApiInternalError
from app.models.book import create_book_json_schema, update_book_json_schema, Book

books_bp = Blueprint("books_blueprint", url_prefix="/books")

_db = MongoDB()


@books_bp.route("/")
async def get_all_books(request):
    # # TODO: use cache to optimize api
    async with request.app.ctx.redis as r:
        books = await get_cache(r, CacheConstants.all_books)
        if books is None:
            book_objs = _db.get_books()
            books = [book.to_dict() for book in book_objs]
            await set_cache(r, CacheConstants.all_books, books)

    number_of_books = len(books)
    return json({"n_books": number_of_books, "books": books})


@books_bp.route("/<book_id>", methods={"GET"})
async def get_single_book(request, book_id):
    book_obj = _db.get_books({"_id": book_id})
    book = [book.to_dict() for book in book_obj][0]
    return json({"description": "Success", "status": 200, "book": book})


@books_bp.route("/", methods={"POST"})
@validate_with_jsonschema(create_book_json_schema)  # To validate request body
async def create_book(request, username=None):
    body = request.json
    token = check_token(request)
    username = token[1]["username"]
    if token == (False, None):
        return json(
            {
                "description": "Unauthorized",
                "status": 401,
                "message": "Login is required",
            },
            status=401,
        )
    book_id = str(uuid.uuid4())
    book = Book(book_id).from_dict(body)
    book.owner = username

    # # TODO: Save book to database
    inserted = _db.add_books(book)
    if not inserted:
        return json(
            {
                "description": "Internal server errors",
                "status": 500,
                "message": "Cannot add this book into the database",
            },
            status=500,
        )

    # TODO: Update cache
    async with request.app.ctx.redis as r:
        books = await get_cache(r, CacheConstants.all_books)
        if not books:
            book_objs = _db.get_books()
            books = [book.to_dict() for book in book_objs]
            await set_cache(r, CacheConstants.all_books, books)

        new_books = books.append(book)
        await set_cache(r, CacheConstants.all_books, new_books)

    return json(
        {
            "description": "Success",
            "status": 200,
            "message": "This book is successfully added to the database",
        }
    )


# TODO: write api get, update, delete book


@books_bp.route("/<book_id>", methods={"DELETE"})
@protected
async def delete_book(request, book_id: str, username):
    token = check_token(request)
    book_obj = _db.get_books({"_id": book_id})
    book = [book.to_dict() for book in book_obj][0]
    username = token[1]["username"]
    role = token[1]["role"]
    if username != book["owner"]:
        return json(
            {
                "description": "Forbidden",
                "status": 403,
                "message": "Cannot delete this because you are not the owner",
            },
            status=403,
        )

    deleted = _db.delete_books(book_id)
    if not deleted:
        return json(
            {
                "description": "Internal server errors",
                "status": 500,
                "message": "Cannot delete this book from the database",
            },
            status=500,
        )
    return json(
        {
            "description": "Success",
            "status": 200,
            "message": "Successfully delete this book from the database",
        }
    )


@books_bp.route("/<book_id>", methods={"PUT"})
@validate_with_jsonschema(update_book_json_schema)
@protected
async def update_book(request, book_id, username):
    token = check_token(request)
    book_obj = _db.get_books({"_id": book_id})
    book = [book.to_dict() for book in book_obj][0]
    username = token[1]["username"]
    body = request.json
    if "owner" in body:
        return json(
            {
                "description": "Bad Request",
                "status": 400,
                "message": "'owner' is immutable property",
            },
            status=400,
        )
    if "_id" in body:
        return json(
            {
                "description": "Bad Request",
                "status": 400,
                "message": "'_id' is immutable property",
            },
            status=400,
        )
    if "createdAt" in body:
        return json(
            {
                "description": "Bad Request",
                "status": 400,
                "message": "'createdAt' is immutable property",
            },
            status=400,
        )
    if "lastUpdatedAt" in body:
        return json(
            {
                "description": "Bad Request",
                "status": 400,
                "message": "'lastUpdatedAt' is immutable property",
            },
            status=400,
        )
    print(body)

    if username != book["owner"]:
        return json(
            {
                "description": "Forbidden",
                "status": 403,
                "message": "Cannot update this because you are not the owner",
            },
            status=403,
        )

    body = request.json

    updated = _db.update_books(book_id, body)

    if not updated:
        return json(
            {
                "description": "Internal server errors",
                "status": 500,
                "message": "Cannot update the information of this book",
            },
            status=500,
        )

    async with request.app.ctx.redis as r:
        book_objs = _db.get_books()
        books = [book.to_dict() for book in book_objs]
        await set_cache(r, CacheConstants.all_books, books)

    return json(
        {
            "description": "Success",
            "status": 200,
            "message": "Successfully update the information of this book",
        }
    )
