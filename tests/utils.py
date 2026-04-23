import random

from httpx import AsyncClient

from app import models  # noqa: F401


async def register_user(client: AsyncClient, username: str, password: str, role: str) -> dict:
    year = random.randint(2, 6)
    batch = random.randint(1, 25)
    number = random.randint(1, 200)
    register_number = f"21222{year}{batch:02d}{number:04d}"

    # Generate a unique mobile number to avoid UNIQUE constraint violations
    unique_suffix = random.randint(1000000, 9999999)
    mobile_number = f"90{unique_suffix:08d}"

    payload = {
        "username": username,
        "full_name": f"{username} Fullname",
        "password": password,
        "role": role,
        "mobile_number": mobile_number,
        "department": "CSE",
        "register_number": register_number,
        "email": f"{username}@example.com",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    return response.json()


async def login_user(client: AsyncClient, username: str, password: str) -> dict:
    payload = {
        "username": username,
        "password": password,
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    return response.json()


async def register_and_login(client: AsyncClient, username: str, password: str, role: str) -> dict:
    """Register a user and then login to get token."""
    reg_response = await register_user(client, username, password, role)
    # Only proceed with login if registration succeeded
    if isinstance(reg_response, dict) and "access_token" not in reg_response:
        return await login_user(client, username, password)
    return reg_response
