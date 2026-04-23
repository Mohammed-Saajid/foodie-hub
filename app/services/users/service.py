from app.core.exceptions import ConflictException, ResourceNotFoundException
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def ban_user(self, user_id: int) -> None:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User not found", details={"user_id": user_id})
        if user.is_banned:
            return  # User is already banned, no action needed
        user.is_banned = True
        await self.user_repository.save_user(user)

    async def list_users(
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
        results, total = await self.user_repository.list_all(
            limit=limit,
            offset=offset,
            username=username,
            full_name=full_name,
            role=role,
            mobile_number=mobile_number,
            department=department,
            register_number=register_number,
            email=email,
            is_active=is_active,
            is_banned=is_banned,
            terms_accepted=terms_accepted,
            sort_desc=sort_desc,
        )
        return results, total

    async def accept_terms(self, user_id: int) -> None:
        await self.user_repository.accept_terms(user_id)

    async def update_user_profile(
        self,
        user_id: int,
        name: str | None = None,
        email: str | None = None,
        phone_number: str | None = None,
        about_me: str | None = None,
        profile_picture_url: str | None = None,
        upi_screenshot_url: str | None = None,
    ) -> User:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User not found", details={"user_id": user_id})
        if name is not None:
            user.full_name = name
        if email is not None:
            user.email = email
        if phone_number is not None:
            user.mobile_number = phone_number
        if about_me is not None:
            user.about_me = about_me
        if profile_picture_url is not None:
            user.profile_picture_url = profile_picture_url
        if upi_screenshot_url is not None:
            user.upi_screenshot_url = upi_screenshot_url
        try:
            await self.user_repository.save_user(user)
        except ConflictException as e:
            raise ConflictException(
                "Email or phone number already in use", details={"user_id": user_id}
            ) from e
        return user

    async def get_user_by_id(self, user_id: int) -> User:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User not found", details={"user_id": user_id})
        return user
