import time


class User:
    def __init__(self):
        self.username = ""
        self.password = ""
        self.created_at = int(time.time())

    def to_dict(self):
        return {"username": self.username, "password": self.password}

    def from_dict(self, json_dict: dict):
        self.username = json_dict.get("username", "")
        self.password = json_dict.get("password", "")
        self.created_at = json_dict.get("createdAt", int(time.time()))
        self.last_updated_at = json_dict.get("lastUpdatedAt", int(time.time()))
        return self


login_schema = {
    "type": "object",
    "properties": {"username": {"type": "string"}, "password": {"type": "string"}},
    "required": ["username", "password"],
}

signup_schema = {
    "type": "object",
    "properties": {"username": {"type": "string"}, "password": {"type": "string"}},
    "required": ["username", "password"],
}
