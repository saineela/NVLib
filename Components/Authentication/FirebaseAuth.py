import os
import sys
import firebase_admin
from firebase_admin import credentials, auth

class Auth:
    def __init__(self, service_account_key):
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.getcwd()

            key_path = os.path.join(base_path, service_account_key)
            key_path = os.path.normpath(key_path)

            if not os.path.exists(key_path):
                raise FileNotFoundError(f"Firebase key not found: {key_path}")

            if not firebase_admin._apps:
                cred = credentials.Certificate(key_path)
                firebase_admin.initialize_app(cred)

            self.auth = auth
            print("Firebase initialized successfully.")
        except Exception as e:
            print(f"Error initializing Firebase: {e}")
            self.auth = None

    def create_user(self, email, password, display_name=None, phone_number=None, photo_url=None):
        user = self.auth.create_user(email=email,password=password,display_name=display_name,phone_number=phone_number,photo_url=photo_url)
        return user.uid  # return UID string


    def get_user_by_email(self, email):
        return self.auth.get_user_by_email(email)

    def get_uid_by_email(self, email):
        return self.auth.get_user_by_email(email).uid

    def get_email_by_uid(self, uid):
        return self.auth.get_user(uid).email

    def get_phone_by_email(self, email):
        return self.auth.get_user_by_email(email).phone_number

    def get_photo_by_email(self, email):
        return self.auth.get_user_by_email(email).photo_url

    def update_user(self, uid, email=None, password=None, display_name=None, phone_number=None, photo_url=None):
        return self.auth.update_user(
            uid,
            email=email,
            password=password,
            display_name=display_name,
            phone_number=phone_number,
            photo_url=photo_url
        )

    def reset_password(self, email, new_password):
        uid = self.get_uid_by_email(email)
        return self.auth.update_user(uid, password=new_password)

    def disable_user(self, email):
        uid = self.get_uid_by_email(email)
        return self.auth.update_user(uid, disabled=True)

    def delete_user(self, email):
        uid = self.get_uid_by_email(email)
        return self.auth.delete_user(uid)

    def list_users(self, max_results=1000):
        return [
            {"uid": u.uid, "email": u.email, "display_name": u.display_name}
            for u in self.auth.list_users(max_results=max_results).iterate_all()
        ]
