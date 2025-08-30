import firebase_admin
from firebase_admin import credentials, auth, exceptions

class Auth:
    def __init__(self, service_account_key_path: str):
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(service_account_key_path)
                firebase_admin.initialize_app(cred)
                print("Firebase initialized successfully.")
            else:
                print("ℹFirebase already initialized.")
            self.auth = auth
        except Exception as e:
            print(f"Error initializing Firebase Auth: {e}")
            self.auth = None

    def create_user(self, email: str, password: str, display_name: str = None) -> str | None:
        if not self.auth: return None
        try:
            user = self.auth.create_user(email=email, password=password, display_name=display_name)
            print(f"User created: {user.uid}")
            return user.uid
        except exceptions.FirebaseError as e:
            print(f"Error creating user: {e}")
            return None

    def get_user_by_email(self, email: str) -> dict | None:
        if not self.auth: return None
        try:
            user = self.auth.get_user_by_email(email)
            return {"uid": user.uid, "email": user.email, "display_name": user.display_name,
                    "phone_number": user.phone_number, "photo_url": user.photo_url}
        except exceptions.FirebaseError as e:
            print(f"Error fetching user: {e}")
            return None

    def get_user_by_uid(self, uid: str) -> dict | None:
        if not self.auth: return None
        try:
            user = self.auth.get_user(uid)
            return {"uid": user.uid, "email": user.email, "display_name": user.display_name,
                    "phone_number": user.phone_number, "photo_url": user.photo_url}
        except exceptions.FirebaseError as e:
            print(f"Error fetching user: {e}")
            return None

    def get_uid_by_email(self, email: str) -> str | None:
        user = self.get_user_by_email(email)
        return user["uid"] if user else None

    def get_email_by_uid(self, uid: str) -> str | None:
        user = self.get_user_by_uid(uid)
        return user["email"] if user else None

    def get_phone_by_email(self, email: str) -> str | None:
        user = self.get_user_by_email(email)
        return user["phone_number"] if user else None

    def get_profile_picture_by_email(self, email: str) -> str | None:
        user = self.get_user_by_email(email)
        return user["photo_url"] if user else None

    def delete_user(self, uid: str) -> bool:
        if not self.auth: return False
        try:
            self.auth.delete_user(uid)
            print(f"User {uid} deleted.")
            return True
        except exceptions.FirebaseError as e:
            print(f"Error deleting user: {e}")
            return False

    def delete_user_by_email(self, email: str) -> bool:
        user = self.get_user_by_email(email)
        return self.delete_user(user["uid"]) if user else False

    def update_user(self, uid: str, email: str = None, password: str = None,
                    display_name: str = None, phone_number: str = None,
                    photo_url: str = None) -> bool:
        if not self.auth: return False
        try:
            self.auth.update_user(uid, email=email, password=password,
                                  display_name=display_name, phone_number=phone_number,
                                  photo_url=photo_url)
            print(f"User {uid} updated.")
            return True
        except exceptions.FirebaseError as e:
            print(f"Error updating user: {e}")
            return False

    def reset_password_by_email(self, email: str, new_password: str) -> bool:
        user = self.get_user_by_email(email)
        return self.update_user(user["uid"], password=new_password) if user else False

    def disable_account_by_email(self, email: str) -> bool:
        user = self.get_user_by_email(email)
        if not user: return False
        try:
            self.auth.update_user(user["uid"], disabled=True)
            print(f"User {email} disabled.")
            return True
        except exceptions.FirebaseError as e:
            print(f"Error disabling user: {e}")
            return False

    def list_users(self, max_results: int = 1000):
        if not self.auth: return []
        try:
            users = self.auth.list_users(max_results=max_results).iterate_all()
            return [{"uid": u.uid, "email": u.email, "display_name": u.display_name,
                     "phone_number": u.phone_number, "photo_url": u.photo_url} for u in users]
        except exceptions.FirebaseError as e:
            print(f"Error listing users: {e}")
            return []