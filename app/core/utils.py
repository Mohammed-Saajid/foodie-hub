from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth.auth import CurrentUser


def build_current_user(user: User) -> CurrentUser:
    return CurrentUser(
        id=user.id,
        role=user.role,
        is_active=user.is_active,
        is_banned=user.is_banned,
        terms_accepted=user.terms_accepted,
        full_name=user.full_name,
    )


async def fetch_user_from_db(db: AsyncSession, user_id: int) -> User | None:
    result = await db.scalars(select(User).where(User.id == user_id))
    return result.first()
