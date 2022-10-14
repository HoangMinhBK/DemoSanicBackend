from pymongo import MongoClient

from app.constants.mongodb_constants import MongoCollections
from app.models.book import Book
from app.models.user import User
from app.utils.logger_utils import get_logger
from config import MongoDBConfig

logger = get_logger("MongoDB")


class MongoDB:
    def __init__(self, connection_url=None):
        if connection_url is None:
            connection_url = f"mongodb://{MongoDBConfig.USERNAME}:{MongoDBConfig.PASSWORD}@{MongoDBConfig.HOST}:{MongoDBConfig.PORT}"

        self.connection_url = connection_url.split("@")[-1]
        self.client = MongoClient(connection_url)
        self.db = self.client[MongoDBConfig.DATABASE]

        self._books_col = self.db[MongoCollections.books]
        self._user_col = self.db[MongoCollections.users]

    def get_books(self, filter_=None, projection=None):
        try:
            if not filter_:
                filter_ = {}
            cursor = self._books_col.find(filter_, projection=projection)
            data = []
            for doc in cursor:
                data.append(Book().from_dict(doc))
            return data
        except Exception as ex:
            logger.exception(ex)
        return []

    # def add_book(self, book: Book):
    #     try:
    #         inserted_doc = self._books_col.insert_one(book.to_dict())
    #         return inserted_doc
    #     except Exception as ex:
    #         logger.exception(ex)
    #     return None

    # TODO: write functions CRUD with books

    def add_books(self, book: Book):
        try:
            inserted_doc = self._books_col.insert_one(book.to_dict())
            return inserted_doc
        except Exception as ex:
            logger.exception(ex)
        return None

    def delete_books(self, id):
        try:
            delete_doc = self._books_col.delete_one({"_id": id})
            return delete_doc
        except Exception as ex:
            logger.exception(ex)
        return None

    def update_books(self, id, jsonObject):
        try:
            update_doc = self._books_col.update_one({"_id": id}, {"$set": jsonObject})
            return update_doc
        except Exception as ex:
            logger.exception(ex)
        return None

    def add_user(self, user: User):
        try:
            inserted_doc = self._user_col.insert_one(user.to_dict())
            return inserted_doc
        except Exception as ex:
            logger.exception(ex)
        return None

    def get_user(self, username, password=None):
        if not password: 
            try:
                get_doc = self._user_col.find_one({"username": username})
                return get_doc 
            except Exception as ex:
                logger.exception(ex)
            return None
        else:
            try:
                get_doc = self._user_col.find_one({"username": username, "password": password})
                return get_doc
            except Exception as ex:
                logger.exception(ex)
            return None
