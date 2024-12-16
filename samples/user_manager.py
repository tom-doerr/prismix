class UserManager:
    def __init__(self):
        self.users = []


def add_user(self, username: str, email: str) -> bool:
    if not username or not email:
        return False
    self.users.append({"username": username, "email": email})
    return True


def get_user(self, username: str) -> dict | None:
    for user in self.users:
        if user["username"] == username:
            return user
    return None


def main() -> None:
    manager = UserManager()
    manager.add_user("alice", "alice@example.com")
    print(manager.get_user("alice"))


if __name__ == "__main__":
    main()
