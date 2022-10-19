import hashlib
from app.decorators.json_validator import validate_with_jsonschema
from app.databases.mongodb import MongoDB
from sanic import Blueprint
from sanic.response import json
from app.models.user import User, login_schema, signup_schema
from app.utils.jwt_utils import generate_jwt
from app.constants.salt import salt

user_bp = Blueprint("user_blueprint", url_prefix="/")

_db = MongoDB()


@user_bp.route("/login", methods={"POST"})
@validate_with_jsonschema(login_schema)
async def login_handler(request):
    body = request.json
    user = User().from_dict(body)
    user.password = hashlib.sha256((user.password + salt).encode()).hexdigest()
    search = _db.get_user(user.username, user.password)
    if not search:
        return json(
            {
                "description": "Bad request",
                "status": 400,
                "message": "Incorrect username or password",
            },
            status=400,
        )

    jwt = generate_jwt(user.username)
    return json(
        {
            "description": "Success",
            "status": 200,
            "username": user.username,
            "jwt": jwt,
        }
    )


@user_bp.route("/signup", methods={"POST"})
@validate_with_jsonschema(signup_schema)
async def signup_handler(request):
    body = request.json
    user = User().from_dict(body)
    search = _db.get_user(user.username)
    hashed_password = hashlib.sha256((user.password + salt).encode())
    user.password = hashed_password.hexdigest()
    print(hashed_password.hexdigest())
    if not search:
        inserted = _db.add_user(user)
        if not inserted:
            return json(
                {
                    "description": "Internal server errors",
                    "status": 500,
                    "message": "Cannot create new account due to server's internal errors",
                },
                status=500,
            )
        return json(
            {
                "description": "Success",
                "status": 200,
                "message": "New account created",
            }
        )
    else:
        return json(
            {
                "description": "Account existed",
                "status": 400,
                "message": "Unable to create new account because this account exists",
            },
            status=400,
        )
