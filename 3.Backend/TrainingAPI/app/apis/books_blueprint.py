import uuid
from app.utils.jwt_utils import generate_jwt
from app.decorators.auth import protected

from sanic import Blueprint
from sanic.response import json

from app.constants.cache_constants import CacheConstants
from app.databases.mongodb import MongoDB
from app.databases.redis_cached import get_cache, set_cache
from app.decorators.json_validator import validate_with_jsonschema

# from app.hooks.error import ApiInternalError
from app.models.book import create_book_json_schema, Book

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
    book = [book.to_dict() for book in book_obj]
    return json({"book": book})

@books_bp.route("/", methods={"POST"})
@validate_with_jsonschema(create_book_json_schema)  # To validate request body
async def create_book(request, username=None):
    body = request.json
    if request.args: 
        username = request.args.get("username")
    token = request.token
    print(token)
    if not token:
        return json({"Message": "Login is required"})
    book_id = str(uuid.uuid4())
    book = Book(book_id).from_dict(body)
    book.owner = username

    # # TODO: Save book to database
    inserted = _db.add_books(book)
    if not inserted:
        return json({"Cannot add this book into the database"})

    # TODO: Update cache
    async with request.app.ctx.redis as r:
        books = await get_cache(r, CacheConstants.all_books)
        if not books: 
            book_objs = _db.get_books()
            books = [book.to_dict() for book in book_objs]
            await set_cache(r, CacheConstants.all_books, books)

        new_books = books.append(book)
        await set_cache(r, CacheConstants.all_books, new_books)

    return json({"status": "success"})


# TODO: write api get, update, delete book


@books_bp.route("/<book_id>", methods={"DELETE"})
@protected
async def delete_book(request, book_id, username):
    username = Book(book_id).owner

    deleted = _db.delete_books(book_id)
    if not deleted:
        return json({"Cannot delete this book from the database"})
    return json({"status": "success"})


@books_bp.route("/<book_id>", methods={"PUT"})
@protected
async def update_book(request, book_id, username):
    username = Book(book_id).owner
    body = request.json
    
    updated = _db.update_books(book_id, body)
        
    if not updated:
        return json({"Cannot update the information of this book"})
    
    async with request.app.ctx.redis as r:
        book_objs = _db.get_books()
        books = [book.to_dict() for book in book_objs]
        await set_cache(r, CacheConstants.all_books, books)
    
    return json({"status": "success"})
