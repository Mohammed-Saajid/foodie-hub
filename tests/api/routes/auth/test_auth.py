from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.core.exceptions import (
    ConflictException,
    ForbiddenException,
    ResourceNotFoundException,
    UnauthorizedException,
)


class TestAuthRoutes:
    @pytest.mark.asyncio
    async def test_register_user_success(self, client: AsyncClient):
        payload = {
            "username": "testuser",
            "password": "TestPass123",
            "full_name": "Test User",
            "role": "consumer",
            "mobile_number": "8870413657",
            "department": "CSE",
            "register_number": "212223240065",
            "email": "testuser@example.com",
        }
        with patch(
            "app.services.auth.service.AuthService.register_user", new_callable=AsyncMock
        ) as mock_register:
            mock_register.return_value = AsyncMock(
                id=1,
                username=payload["username"],
                full_name=payload["full_name"],
                role=payload["role"],
                mobile_number=payload["mobile_number"],
                department=payload["department"],
                register_number=payload["register_number"],
                email=payload["email"],
                terms_accepted=False,
            )
            response = await client.post("/auth/register", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == payload["username"]
        assert data["full_name"] == payload["full_name"]
        assert data["role"] == payload["role"]

    @pytest.mark.asyncio
    async def test_register_user_validation_error(self, client: AsyncClient):
        payload = {
            "username": "tu",
            "password": "TestPass123",
            "full_name": "Test User",
            "role": "consumer",
            "mobile_number": "8870413657",
            "department": "ARTS",
            "register_number": "212223240065",
            "email": "testuser@example.com",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "username" in data["details"][0]["loc"]

    @pytest.mark.asyncio
    async def test_duplicate_user_registration(self, client: AsyncClient):
        payload = {
            "username": "existinguser",
            "password": "TestPass123",
            "full_name": "Existing User",
            "role": "consumer",
            "mobile_number": "8870413657",
            "department": "CSE",
            "register_number": "212223240065",
            "email": "existinguser@example.com",
        }
        with patch(
            "app.services.auth.service.AuthService.register_user", new_callable=AsyncMock
        ) as mock_register:
            mock_register.side_effect = ConflictException("Username already exists")
            response = await client.post("/auth/register", json=payload)
        assert response.status_code == 409
        data = response.json()
        assert data["message"] == "Username already exists"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("role", ["invalid_role", "123", "", None])
    async def test_register_user_invalid_role(self, client: AsyncClient, role: str):
        payload = {
            "username": "testuser2",
            "password": "TestPass123",
            "full_name": "Test User",
            "role": role,
            "mobile_number": "8870413657",
            "department": "CSE",
            "register_number": "212223240065",
            "email": "testuser2@example.com",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "role" in data["details"][0]["loc"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "email", ["invalid-email", "user@.com", "user@com", "user.com", "", None]
    )
    async def test_register_user_invalid_email(self, client: AsyncClient, email: str):
        payload = {
            "username": "testuser3",
            "password": "TestPass123",
            "full_name": "Test User",
            "role": "consumer",
            "mobile_number": "8870413657",
            "department": "CSE",
            "register_number": "212223240065",
            "email": email,
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "email" in data["details"][0]["loc"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("mobile_number", ["12345", "invalid-mobile", "abcdefghij", "", None])
    async def test_register_user_invalid_mobile_number(
        self, client: AsyncClient, mobile_number: str
    ):
        payload = {
            "username": "testuser4",
            "password": "TestPass123",
            "full_name": "Test User",
            "role": "consumer",
            "mobile_number": mobile_number,
            "department": "CSE",
            "register_number": "212223240065",
            "email": "testuser4@example.com",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "mobile_number" in data["details"][0]["loc"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("department", ["INVALID_DEPT", "123", "", None])
    async def test_register_user_invalid_department(self, client: AsyncClient, department: str):
        payload = {
            "username": "testuser5",
            "password": "TestPass123",
            "full_name": "Test User",
            "role": "consumer",
            "mobile_number": "8870413657",
            "department": department,
            "register_number": "212223240065",
            "email": "testuser5@example.com",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "department" in data["details"][0]["loc"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("register_number", ["1", "invalid-reg", "abcdefghij", "", None])
    async def test_register_user_invalid_register_number(
        self, client: AsyncClient, register_number: str
    ):
        payload = {
            "username": "testuser6",
            "password": "TestPass123",
            "full_name": "Test User",
            "role": "consumer",
            "mobile_number": "8870413657",
            "department": "CSE",
            "register_number": register_number,
            "email": "testuser6@example.com",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "register_number" in data["details"][0]["loc"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("password", ["short", "1234567", "", None])
    async def test_register_user_invalid_password(self, client: AsyncClient, password: str):
        payload = {
            "username": "testuser7",
            "password": password,
            "full_name": "Test User",
            "role": "consumer",
            "mobile_number": "8870413657",
            "department": "CSE",
            "register_number": "212223240065",
            "email": "testuser7@example.com",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "password" in data["details"][0]["loc"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "username", ["invalid username", "user!", "user@name", "", None, "Fuck", "Sex", "Asshole"]
    )
    async def test_register_user_invalid_username(self, client: AsyncClient, username: str):
        payload = {
            "username": username,
            "password": "TestPass123",
            "full_name": "Test User",
            "role": "consumer",
            "mobile_number": "8870413657",
            "department": "CSE",
            "register_number": "212223240065",
            "email": "testuser8@example.com",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "username" in data["details"][0]["loc"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "full_name", ["invalid ful8l name", "John Doe!", "John D5oe@name", "", None]
    )
    async def test_register_user_invalid_full_name(self, client: AsyncClient, full_name: str):
        payload = {
            "username": "testuser9",
            "password": "TestPass123",
            "full_name": full_name,
            "role": "consumer",
            "mobile_number": "8870413657",
            "department": "CSE",
            "register_number": "212223240065",
            "email": "testuser9@example.com",
        }
        response = await client.post("/auth/register", json=payload)
        assert response.status_code == 422
        data = response.json()
        assert "full_name" in data["details"][0]["loc"]

    @pytest.mark.asyncio
    async def test_login_user_success(self, client: AsyncClient):
        payload = {"username": "testuser", "password": "TestPass123"}
        with patch(
            "app.services.auth.service.AuthService.authenticate_user", new_callable=AsyncMock
        ) as mock_authenticate:
            mock_authenticate.return_value = (
                AsyncMock(
                    id=1,
                    username=payload["username"],
                    full_name="Test User",
                    role="consumer",
                    mobile_number="8870413657",
                    department="CSE",
                    register_number="212223240065",
                    email="testuser@example.com",
                    terms_accepted=False,
                ),
                "fake-jwt-token",
            )
            response = await client.post("/auth/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "fake-jwt-token"
        assert data["user"]["username"] == payload["username"]
        assert data["user"]["full_name"] == "Test User"
        assert data["user"]["role"] == "consumer"
        assert data["user"]["mobile_number"] == "8870413657"
        assert data["user"]["department"] == "CSE"
        assert data["user"]["register_number"] == "212223240065"
        assert data["user"]["email"] == "testuser@example.com"
        assert not data["user"]["terms_accepted"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("username", "password"),
        [
            ("ab1245456451", "TestPass123"),
            ("testuser", "s44545hort"),
            ("ab44", "shor454545t"),
        ],
    )
    async def test_login_user_invalid_credentials(
        self, client: AsyncClient, username: str, password: str
    ):
        payload = {"username": username, "password": password}
        with patch(
            "app.services.auth.service.AuthService.authenticate_user", new_callable=AsyncMock
        ) as mock_authenticate:
            mock_authenticate.side_effect = UnauthorizedException(
                message="Invalid username or password"
            )
            response = await client.post("/auth/login", json=payload)
        assert response.status_code == 401
        data = response.json()
        assert data["message"] == "Invalid username or password"

    @pytest.mark.asyncio
    async def test_login_banned_user(self, client: AsyncClient):
        payload = {"username": "banneduser", "password": "TestPass123"}
        with patch(
            "app.services.auth.service.AuthService.authenticate_user", new_callable=AsyncMock
        ) as mock_authenticate:
            mock_authenticate.side_effect = ForbiddenException(
                message="User is blocked", details={"username": "banneduser"}
            )
            response = await client.post("/auth/login", json=payload)
        assert response.status_code == 403
        data = response.json()
        assert data["message"] == "User is blocked"

    # Tests for forgot password and reset password has to be implemented here.

    # Get terms tests
    @pytest.mark.asyncio
    async def test_get_terms_success(self, client: AsyncClient):
        with patch(
            "app.services.terms.service.TermsService.get_terms_and_conditions",
            new_callable=AsyncMock,
        ) as mock_get_terms:
            mock_get_terms.return_value = {"version": "1.0", "content": "Terms content"}
            response = await client.get("/auth/terms")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "1.0"
        assert data["content"] == "Terms content"

    @pytest.mark.asyncio
    async def test_get_terms_not_found(self, client: AsyncClient):
        with patch(
            "app.services.terms.service.TermsService.get_terms_and_conditions",
            new_callable=AsyncMock,
        ) as mock_get_terms:
            mock_get_terms.side_effect = ResourceNotFoundException(message="Terms not found")
            response = await client.get("/auth/terms")
        assert response.status_code == 404
        data = response.json()
        assert data["message"] == "Terms not found"

    # Accept terms tests
    @pytest.mark.asyncio
    async def test_accept_terms_success(
        self,
        client: AsyncClient,
        user_factory,
        service_factory,
        override_dependencies,
    ):
        user = user_factory(id=10)

        user_service = service_factory(accept_terms=AsyncMock(return_value=None))
        cache_service = service_factory(delete=AsyncMock(return_value=None))

        override_dependencies(
            user=user,
            user_service=user_service,
            cache=cache_service,
        )
        print(client)

        response = await client.post("/auth/accept-terms")

        assert response.status_code == 200
        assert response.json()["message"] == "Terms and conditions accepted"

    @pytest.mark.asyncio
    async def test_accept_terms_user_not_found(
        self,
        client: AsyncClient,
        user_factory: callable,
        service_factory,
        override_dependencies,
    ):

        user = user_factory(id=20)
        user_service = service_factory(
            accept_terms=AsyncMock(side_effect=ResourceNotFoundException(message="User not found"))
        )
        cache_service = service_factory(delete=AsyncMock(return_value=None))

        override_dependencies(
            user=user,
            user_service=user_service,
            cache=cache_service,
        )

        response = await client.post("/auth/accept-terms")

        assert response.status_code == 404
        assert response.json()["message"] == "User not found"
