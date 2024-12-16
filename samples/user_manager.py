from dataclasses import dataclass

@dataclass
class User:
    username: str
    email: str

class UserManager:
    """Manages a list of users."""

    def __init__(self) -> None:
        """Initialize an empty list of users."""
        self.users: list[User] = []

    def add_user(self, username: str, email: str) -> bool:
        """
        Add a new user to the list.

        Args:
            username (str): The username of the user.
            email (str): The email address of the user.

        Returns:
            bool: True if the user was added successfully, False otherwise.
        """
        if not username or not email:
            return False
        self.users.append(User(username, email))
        return True

    def get_user(self, username: str) -> User | None:
        """
        Retrieve a user by their username.

        Args:
            username (str): The username of the user to retrieve.

        Returns:
            User | None: The User object if found, otherwise None.
        """
        return next((user for user in self.users if user.username == username), None)

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
