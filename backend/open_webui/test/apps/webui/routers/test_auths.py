from datetime import date

from test.util.abstract_integration_test import AbstractPostgresTest
from test.util.mock_user import mock_webui_user


class TestAuths(AbstractPostgresTest):
    BASE_PATH = "/api/v1/auths"

    def setup_class(cls):
        super().setup_class()
        from open_webui.models.auths import Auths
        from open_webui.models.users import Users

        cls.users = Users
        cls.auths = Auths

    def test_get_session_user(self):
        with mock_webui_user():
            response = self.fast_api_client.get(self.create_url(""))
        assert response.status_code == 200
        assert response.json() == {
            "id": "1",
            "name": "John Doe",
            "email": "john.doe@openwebui.com",
            "role": "user",
            "profile_image_url": "/user.png",
            "last_name": None,
            "first_name": None,
            "gender": None,
            "oreegami_edu_email": None,
            "campus_region": None,
            "session": None,
            "rncp_title": None,
            "apprenticeship_company": None,
            "apprenticeship_start_date": None,
            "apprenticeship_end_date": None,
        }

    def test_update_profile(self):
        from open_webui.utils.auth import get_password_hash

        user = self.auths.insert_new_auth(
            email="john.doe@openwebui.com",
            password=get_password_hash("old_password"),
            name="John Doe",
            profile_image_url="/user.png",
            role="user",
        )

        with mock_webui_user(id=user.id):
            response = self.fast_api_client.post(
                self.create_url("/update/profile"),
                json={
                    "name": "John Doe 2",
                    "profile_image_url": "/user2.png",
                    "last_name": "Doe",
                    "first_name": "John",
                    "gender": "Homme",
                    "oreegami_edu_email": "JOHN.DOE@OREEGAMI-EDU.COM",
                    "campus_region": "Occitanie",
                    "session": "2026",
                    "rncp_title": "Expert en IA",
                    "apprenticeship_company": "Example Corp",
                    "apprenticeship_start_date": "2026-09-01",
                    "apprenticeship_end_date": "2027-08-31",
                },
            )
        assert response.status_code == 200
        db_user = self.users.get_user_by_id(user.id)
        assert db_user.name == "John Doe 2"
        assert db_user.profile_image_url == "/user2.png"
        assert db_user.last_name == "Doe"
        assert db_user.first_name == "John"
        assert db_user.oreegami_edu_email == "john.doe@oreegami-edu.com"
        assert db_user.apprenticeship_start_date == date(2026, 9, 1)
        assert db_user.apprenticeship_end_date == date(2027, 8, 31)

        # Older clients that only update the display profile must not clear
        # education fields they do not send.
        with mock_webui_user(id=user.id):
            response = self.fast_api_client.post(
                self.create_url("/update/profile"),
                json={"name": "John Doe 3", "profile_image_url": "/user3.png"},
            )
        assert response.status_code == 200
        db_user = self.users.get_user_by_id(user.id)
        assert db_user.last_name == "Doe"
        assert db_user.oreegami_edu_email == "john.doe@oreegami-edu.com"

    def test_update_password(self):
        from open_webui.utils.auth import get_password_hash

        user = self.auths.insert_new_auth(
            email="john.doe@openwebui.com",
            password=get_password_hash("old_password"),
            name="John Doe",
            profile_image_url="/user.png",
            role="user",
        )

        with mock_webui_user(id=user.id):
            response = self.fast_api_client.post(
                self.create_url("/update/password"),
                json={"password": "old_password", "new_password": "new_password"},
            )
        assert response.status_code == 200

        old_auth = self.auths.authenticate_user(
            "john.doe@openwebui.com", "old_password"
        )
        assert old_auth is None
        new_auth = self.auths.authenticate_user(
            "john.doe@openwebui.com", "new_password"
        )
        assert new_auth is not None

    def test_signin(self):
        from open_webui.utils.auth import get_password_hash

        user = self.auths.insert_new_auth(
            email="john.doe@openwebui.com",
            password=get_password_hash("password"),
            name="John Doe",
            profile_image_url="/user.png",
            role="user",
        )
        response = self.fast_api_client.post(
            self.create_url("/signin"),
            json={"email": "john.doe@openwebui.com", "password": "password"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user.id
        assert data["name"] == "John Doe"
        assert data["email"] == "john.doe@openwebui.com"
        assert data["role"] == "user"
        assert data["profile_image_url"] == "/user.png"
        assert data["token"] is not None and len(data["token"]) > 0
        assert data["token_type"] == "Bearer"

    def test_signup(self):
        response = self.fast_api_client.post(
            self.create_url("/signup"),
            json={
                "name": "John Doe",
                "email": "john.doe@openwebui.com",
                "password": "password",
                "last_name": "Doe",
                "first_name": "John",
                "oreegami_edu_email": "john.doe@oreegami-edu.com",
                "campus_region": "Occitanie",
                "session": "2026",
                "rncp_title": "Expert en IA",
                "apprenticeship_company": "Example Corp",
                "apprenticeship_start_date": "2026-09-01",
                "apprenticeship_end_date": "2027-08-31",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] is not None and len(data["id"]) > 0
        assert data["name"] == "John Doe"
        assert data["email"] == "john.doe@openwebui.com"
        assert data["role"] in ["admin", "user", "pending"]
        assert data["profile_image_url"] == "/user.png"
        assert data["last_name"] == "Doe"
        assert data["first_name"] == "John"
        assert data["oreegami_edu_email"] == "john.doe@oreegami-edu.com"
        assert data["apprenticeship_start_date"] == "2026-09-01"
        assert data["apprenticeship_end_date"] == "2027-08-31"
        assert data["token"] is not None and len(data["token"]) > 0
        assert data["token_type"] == "Bearer"

    def test_add_user(self):
        with mock_webui_user():
            response = self.fast_api_client.post(
                self.create_url("/add"),
                json={
                    "name": "John Doe 2",
                    "email": "john.doe2@openwebui.com",
                    "password": "password2",
                    "role": "admin",
                    "last_name": "Doe",
                    "first_name": "Jane",
                    "gender": "Femme",
                    "oreegami_edu_email": "jane.doe@oreegami-edu.com",
                    "campus_region": "Île-de-France",
                    "session": "2027",
                    "rncp_title": "Data Engineer",
                    "apprenticeship_company": "Example Corp",
                    "apprenticeship_start_date": "2027-09-01",
                    "apprenticeship_end_date": "2028-08-31",
                },
            )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] is not None and len(data["id"]) > 0
        assert data["name"] == "John Doe 2"
        assert data["email"] == "john.doe2@openwebui.com"
        assert data["role"] == "admin"
        assert data["profile_image_url"] == "/user.png"
        assert data["last_name"] == "Doe"
        assert data["first_name"] == "Jane"
        assert data["oreegami_edu_email"] == "jane.doe@oreegami-edu.com"
        assert data["campus_region"] == "Île-de-France"
        assert data["token"] is not None and len(data["token"]) > 0
        assert data["token_type"] == "Bearer"

    def test_get_admin_details(self):
        self.auths.insert_new_auth(
            email="john.doe@openwebui.com",
            password="password",
            name="John Doe",
            profile_image_url="/user.png",
            role="admin",
        )
        with mock_webui_user():
            response = self.fast_api_client.get(self.create_url("/admin/details"))

        assert response.status_code == 200
        assert response.json() == {
            "name": "John Doe",
            "email": "john.doe@openwebui.com",
        }

    def test_create_api_key_(self):
        user = self.auths.insert_new_auth(
            email="john.doe@openwebui.com",
            password="password",
            name="John Doe",
            profile_image_url="/user.png",
            role="admin",
        )
        with mock_webui_user(id=user.id):
            response = self.fast_api_client.post(self.create_url("/api_key"))
        assert response.status_code == 200
        data = response.json()
        assert data["api_key"] is not None
        assert len(data["api_key"]) > 0

    def test_delete_api_key(self):
        user = self.auths.insert_new_auth(
            email="john.doe@openwebui.com",
            password="password",
            name="John Doe",
            profile_image_url="/user.png",
            role="admin",
        )
        self.users.update_user_api_key_by_id(user.id, "abc")
        with mock_webui_user(id=user.id):
            response = self.fast_api_client.delete(self.create_url("/api_key"))
        assert response.status_code == 200
        assert response.json() == True
        db_user = self.users.get_user_by_id(user.id)
        assert db_user.api_key is None

    def test_get_api_key(self):
        user = self.auths.insert_new_auth(
            email="john.doe@openwebui.com",
            password="password",
            name="John Doe",
            profile_image_url="/user.png",
            role="admin",
        )
        self.users.update_user_api_key_by_id(user.id, "abc")
        with mock_webui_user(id=user.id):
            response = self.fast_api_client.get(self.create_url("/api_key"))
        assert response.status_code == 200
        assert response.json() == {"api_key": "abc"}
