from dataclasses import dataclass

@dataclass
class User:
    username: str
    email: str

class UserManager:
    def __init__(self):
        self.users: list[User] = []

    def add_user(self, username: str, email: str) -> bool:
        if not username or not email:
            return False
        self.users.append(User(username, email))
        return True

    def get_user(self, username: str) -> User | None:
        for user in self.users:
            if user.username == username:
                return user
        return None

def main() -> None:
    manager = UserManager()
    manager.add_user("alice", "alice@example.com")
    user = manager.get_user("alice")
    if user:
        print(f"User found: {user}")
    else:
        print("User not found")

if __name__ == "__main__":
    main()
