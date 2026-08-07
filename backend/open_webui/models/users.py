import time
from datetime import date
from typing import Optional

from open_webui.internal.db import Base, JSONField, get_db


from open_webui.models.chats import Chats
from open_webui.models.groups import Groups


from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from sqlalchemy import BigInteger, Column, Date, String, Text, func, or_

####################
# User DB Schema
####################


class User(Base):
    __tablename__ = "user"

    id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String)
    role = Column(String)
    profile_image_url = Column(Text)

    last_active_at = Column(BigInteger)
    updated_at = Column(BigInteger)
    created_at = Column(BigInteger)

    api_key = Column(String, nullable=True, unique=True)
    settings = Column(JSONField, nullable=True)
    info = Column(JSONField, nullable=True)

    oauth_sub = Column(Text, unique=True)

    last_name = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    oreegami_edu_email = Column(String, nullable=True)
    campus_region = Column(String, nullable=True)
    session = Column(String, nullable=True)
    rncp_title = Column(String, nullable=True)
    apprenticeship_company = Column(String, nullable=True)
    apprenticeship_start_date = Column(Date, nullable=True)
    apprenticeship_end_date = Column(Date, nullable=True)


class UserSettings(BaseModel):
    ui: Optional[dict] = {}
    model_config = ConfigDict(extra="allow")
    pass


USER_PROFILE_FIELDS = frozenset(
    {
        "last_name",
        "first_name",
        "gender",
        "oreegami_edu_email",
        "campus_region",
        "session",
        "rncp_title",
        "apprenticeship_company",
        "apprenticeship_start_date",
        "apprenticeship_end_date",
    }
)

USER_PROFILE_STRING_FIELDS = tuple(
    USER_PROFILE_FIELDS
    - {"apprenticeship_start_date", "apprenticeship_end_date"}
)


class UserProfileFields(BaseModel):
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    gender: Optional[str] = None
    oreegami_edu_email: Optional[str] = None
    campus_region: Optional[str] = None
    session: Optional[str] = None
    rncp_title: Optional[str] = None
    apprenticeship_company: Optional[str] = None
    apprenticeship_start_date: Optional[date] = None
    apprenticeship_end_date: Optional[date] = None

    @field_validator(*USER_PROFILE_STRING_FIELDS, mode="before")
    @classmethod
    def normalize_optional_strings(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("oreegami_edu_email")
    @classmethod
    def normalize_oreegami_email(cls, value):
        return value.lower() if value else None

    @model_validator(mode="after")
    def validate_apprenticeship_dates(self):
        if (
            self.apprenticeship_start_date
            and self.apprenticeship_end_date
            and self.apprenticeship_end_date < self.apprenticeship_start_date
        ):
            raise ValueError(
                "apprenticeship_end_date must be on or after apprenticeship_start_date"
            )
        return self

    def profile_dump(self, *, exclude_unset: bool = False) -> dict:
        return self.model_dump(
            include=USER_PROFILE_FIELDS, exclude_unset=exclude_unset
        )


class UserModel(UserProfileFields):
    id: str
    name: str
    email: str
    role: str = "pending"
    profile_image_url: str

    last_active_at: int  # timestamp in epoch
    updated_at: int  # timestamp in epoch
    created_at: int  # timestamp in epoch

    api_key: Optional[str] = None
    settings: Optional[UserSettings] = None
    info: Optional[dict] = None

    oauth_sub: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


####################
# Forms
####################


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    profile_image_url: str


class UserNameResponse(BaseModel):
    id: str
    name: str
    role: str
    profile_image_url: str


class UserRoleUpdateForm(BaseModel):
    id: str
    role: str


class UserUpdateForm(UserProfileFields):
    name: str
    email: str
    profile_image_url: str
    password: Optional[str] = None


class UsersTable:
    USER_PROFILE_FIELDS = USER_PROFILE_FIELDS
    AIRTABLE_PROFILE_FIELDS = USER_PROFILE_FIELDS

    def insert_new_user(
        self,
        id: str,
        name: str,
        email: str,
        profile_image_url: str = "/user.png",
        role: str = "pending",
        oauth_sub: Optional[str] = None,
        profile: Optional[dict] = None,
    ) -> Optional[UserModel]:
        with get_db() as db:
            profile = UserProfileFields(**(profile or {})).profile_dump()
            user = UserModel(
                **{
                    "id": id,
                    "name": name,
                    "email": email,
                    "role": role,
                    "profile_image_url": profile_image_url,
                    "last_active_at": int(time.time()),
                    "created_at": int(time.time()),
                    "updated_at": int(time.time()),
                    "oauth_sub": oauth_sub,
                    **profile,
                }
            )
            result = User(**user.model_dump())
            db.add(result)
            db.commit()
            db.refresh(result)
            if result:
                return user
            else:
                return None

    def get_user_by_id(self, id: str) -> Optional[UserModel]:
        try:
            with get_db() as db:
                user = db.query(User).filter_by(id=id).first()
                return UserModel.model_validate(user)
        except Exception:
            return None

    def get_user_by_api_key(self, api_key: str) -> Optional[UserModel]:
        try:
            with get_db() as db:
                user = db.query(User).filter_by(api_key=api_key).first()
                return UserModel.model_validate(user)
        except Exception:
            return None

    def get_user_by_email(self, email: str) -> Optional[UserModel]:
        try:
            with get_db() as db:
                user = db.query(User).filter_by(email=email).first()
                return UserModel.model_validate(user)
        except Exception:
            return None

    def is_email_used_by_another_user(
        self, email: str, user_id: Optional[str] = None
    ) -> bool:
        normalized_email = email.strip().lower()
        if not normalized_email:
            return False

        with get_db() as db:
            query = db.query(User.id).filter(
                or_(
                    func.lower(User.email) == normalized_email,
                    func.lower(User.oreegami_edu_email) == normalized_email,
                )
            )
            if user_id:
                query = query.filter(User.id != user_id)
            return query.first() is not None

    def get_user_by_oauth_sub(self, sub: str) -> Optional[UserModel]:
        try:
            with get_db() as db:
                user = db.query(User).filter_by(oauth_sub=sub).first()
                return UserModel.model_validate(user)
        except Exception:
            return None

    def get_users(
        self, skip: Optional[int] = None, limit: Optional[int] = None
    ) -> list[UserModel]:
        with get_db() as db:

            query = db.query(User).order_by(User.created_at.desc())

            if skip:
                query = query.offset(skip)
            if limit:
                query = query.limit(limit)

            users = query.all()

            return [UserModel.model_validate(user) for user in users]

    def get_users_by_user_ids(self, user_ids: list[str]) -> list[UserModel]:
        with get_db() as db:
            users = db.query(User).filter(User.id.in_(user_ids)).all()
            return [UserModel.model_validate(user) for user in users]

    def get_num_users(self) -> Optional[int]:
        with get_db() as db:
            return db.query(User).count()

    def get_first_user(self) -> UserModel:
        try:
            with get_db() as db:
                user = db.query(User).order_by(User.created_at).first()
                return UserModel.model_validate(user)
        except Exception:
            return None

    def get_user_webhook_url_by_id(self, id: str) -> Optional[str]:
        try:
            with get_db() as db:
                user = db.query(User).filter_by(id=id).first()

                if user.settings is None:
                    return None
                else:
                    return (
                        user.settings.get("ui", {})
                        .get("notifications", {})
                        .get("webhook_url", None)
                    )
        except Exception:
            return None

    def update_user_role_by_id(self, id: str, role: str) -> Optional[UserModel]:
        try:
            with get_db() as db:
                db.query(User).filter_by(id=id).update({"role": role})
                db.commit()
                user = db.query(User).filter_by(id=id).first()
                return UserModel.model_validate(user)
        except Exception:
            return None

    def update_user_profile_image_url_by_id(
        self, id: str, profile_image_url: str
    ) -> Optional[UserModel]:
        try:
            with get_db() as db:
                db.query(User).filter_by(id=id).update(
                    {"profile_image_url": profile_image_url}
                )
                db.commit()

                user = db.query(User).filter_by(id=id).first()
                return UserModel.model_validate(user)
        except Exception:
            return None

    def update_user_last_active_by_id(self, id: str) -> Optional[UserModel]:
        try:
            with get_db() as db:
                db.query(User).filter_by(id=id).update(
                    {"last_active_at": int(time.time())}
                )
                db.commit()

                user = db.query(User).filter_by(id=id).first()
                return UserModel.model_validate(user)
        except Exception:
            return None

    def update_user_oauth_sub_by_id(
        self, id: str, oauth_sub: str
    ) -> Optional[UserModel]:
        try:
            with get_db() as db:
                db.query(User).filter_by(id=id).update({"oauth_sub": oauth_sub})
                db.commit()

                user = db.query(User).filter_by(id=id).first()
                return UserModel.model_validate(user)
        except Exception:
            return None

    def update_user_by_id(self, id: str, updated: dict) -> Optional[UserModel]:
        try:
            with get_db() as db:
                db.query(User).filter_by(id=id).update(updated)
                db.commit()

                user = db.query(User).filter_by(id=id).first()
                return UserModel.model_validate(user)
                # return UserModel(**user.dict())
        except Exception:
            return None

    def update_user_from_airtable_by_email(
        self, email: str, profile: dict
    ) -> tuple[Optional[UserModel], bool]:
        normalized_email = email.strip().lower()
        if not normalized_email:
            return None, False

        validated_profile = UserProfileFields(**profile).profile_dump()
        updated = {
            key: validated_profile[key]
            for key in profile
            if key in self.AIRTABLE_PROFILE_FIELDS
        }

        with get_db() as db:
            users = (
                db.query(User)
                .filter(
                    or_(
                        func.lower(User.email) == normalized_email,
                        func.lower(User.oreegami_edu_email) == normalized_email,
                    )
                )
                .limit(2)
                .all()
            )
            if len(users) != 1:
                return None, False

            user = users[0]
            changed = any(getattr(user, key) != value for key, value in updated.items())
            if changed:
                for key, value in updated.items():
                    setattr(user, key, value)
                user.updated_at = int(time.time())
                db.commit()
                db.refresh(user)

            return UserModel.model_validate(user), changed

    def update_user_settings_by_id(self, id: str, updated: dict) -> Optional[UserModel]:
        try:
            with get_db() as db:
                user_settings = db.query(User).filter_by(id=id).first().settings

                if user_settings is None:
                    user_settings = {}

                user_settings.update(updated)

                db.query(User).filter_by(id=id).update({"settings": user_settings})
                db.commit()

                user = db.query(User).filter_by(id=id).first()
                return UserModel.model_validate(user)
        except Exception:
            return None

    def delete_user_by_id(self, id: str) -> bool:
        try:
            # Remove User from Groups
            Groups.remove_user_from_all_groups(id)

            # Delete User Chats
            result = Chats.delete_chats_by_user_id(id)
            if result:
                with get_db() as db:
                    # Delete User
                    db.query(User).filter_by(id=id).delete()
                    db.commit()

                return True
            else:
                return False
        except Exception:
            return False

    def update_user_api_key_by_id(self, id: str, api_key: str) -> str:
        try:
            with get_db() as db:
                result = db.query(User).filter_by(id=id).update({"api_key": api_key})
                db.commit()
                return True if result == 1 else False
        except Exception:
            return False

    def get_user_api_key_by_id(self, id: str) -> Optional[str]:
        try:
            with get_db() as db:
                user = db.query(User).filter_by(id=id).first()
                return user.api_key
        except Exception:
            return None

    def get_valid_user_ids(self, user_ids: list[str]) -> list[str]:
        with get_db() as db:
            users = db.query(User).filter(User.id.in_(user_ids)).all()
            return [user.id for user in users]


Users = UsersTable()
