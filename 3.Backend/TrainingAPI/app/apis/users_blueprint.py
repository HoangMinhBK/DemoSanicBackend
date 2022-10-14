from app.decorators.json_validator import validate_with_jsonschema
from app.databases.mongodb import MongoDB
from sanic import Blueprint
from sanic.response import json
from app.models.user import User, login_schema, signup_schema
from app.utils.jwt_utils import generate_jwt

user_bp = Blueprint("user_blueprint", url_prefix="/")

_db = MongoDB()


@user_bp.route("/login", methods={"POST"})
@validate_with_jsonschema(login_schema)
async def login_handler(request):
    body = request.json
    user = User().from_dict(body)
    search = _db.get_user(user.username, user.password)
    if not search:
        return json({"Login status": "failed"})
    
    jwt = generate_jwt(user.username)
    return json({"Login status": "Successful", "username": user.username, "jwt": jwt})


@user_bp.route("/signup", methods={"POST"})
@validate_with_jsonschema(signup_schema)
async def signup_handler(request):
    body = request.json
    user = User().from_dict(body)
    search = _db.get_user(user.username)
    if not search:
        inserted = _db.add_user(user)
        if not inserted:
            return json({"Registration status": "failed"})
        return json({"Registration status": "successful"})
    else:
        return json({"Registration status": "account existed"})
