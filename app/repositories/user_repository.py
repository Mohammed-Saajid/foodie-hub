import datetime
from typing import Any

from sqlalchemy import func, select

from app.core.exceptions import ResourceNotFoundException
from app.models.enums import UserRole
from app.models.user import PasswordResetToken, User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.scalars(select(User).where(User.id == user_id))
        return result.first()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.scalars(select(User).where(User.username == username))
        return result.first()

    async def get_by_unique_fields(
        self,
        username: str | None = None,
        email: str | None = None,
        register_number: str | None = None,
        mobile_number: str | None = None,
    ) -> User | None:
        query = select(User)
        if username:
            query = query.where(User.username == username)
        if email:
            query = query.where(User.email == email)
        if register_number:
            query = query.where(User.register_number == register_number)
        if mobile_number:
            query = query.where(User.mobile_number == mobile_number)

        result = await self.db.scalars(query)
        return result.first()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.scalars(select(User).where(User.email == email))
        return result.first()

    async def list_all(
        self,
        limit: int = 100,
        offset: int = 0,
        username: str | None = None,
        full_name: str | None = None,
        role: UserRole | None = None,
        mobile_number: str | None = None,
        department: str | None = None,
        register_number: str | None = None,
        email: str | None = None,
        is_active: bool | None = None,
        is_banned: bool | None = None,
        terms_accepted: bool | None = None,
        sort_desc: bool = True,
    ) -> tuple[list[User], int]:
        # Initialize base query
        query = select(User)

        # Dynamically apply filters
        if username is not None:
            query = query.where(User.username.ilike(f"%{username}%"))
        if full_name is not None:
            query = query.where(User.full_name.ilike(f"%{full_name}%"))
        if role is not None:
            query = query.where(User.role == role)
        if mobile_number is not None:
            query = query.where(User.mobile_number.ilike(f"%{mobile_number}%"))
        if department is not None:
            query = query.where(User.department == department)
        if register_number is not None:
            query = query.where(User.register_number.ilike(f"%{register_number}%"))
        if email is not None:
            query = query.where(User.email.ilike(f"%{email}%"))
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        if is_banned is not None:
            query = query.where(User.is_banned == is_banned)
        if terms_accepted is not None:
            query = query.where(User.terms_accepted == terms_accepted)

        if sort_desc:
            query = query.order_by(User.created_at.desc())
        else:
            query = query.order_by(User.created_at.asc())

        # Calculate total count for pagination
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0

        query = query.offset(offset).limit(limit)
        result = await self.db.scalars(query)
        users = list(result.all())
        return users, total

    async def save_user(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def create_user(self, **kwargs: Any) -> User:
        user = User(**kwargs)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def accept_terms(self, user_id: int) -> None:
        user = await self.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User not found", details={"user_id": user_id})
        if user.terms_accepted:
            return  # Terms already accepted, no action needed
        user.terms_accepted = True
        user.terms_accepted_at = datetime.datetime.now()
        await self.save_user(user)

    # Later We can define these methods in a different repository.
    async def create_reset_token(
        self, user_id: int, token_hash: str, expires_at: datetime.datetime
    ) -> None:
        reset_record = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_used=False,
        )
        self.db.add(reset_record)

    async def get_password_reset_token(self, token_hash: str) -> PasswordResetToken | None:
        result = await self.db.scalars(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        )
        return result.first()

    async def mark_token_as_used(self, token: PasswordResetToken) -> None:
        token.is_used = True
        self.db.add(token)
