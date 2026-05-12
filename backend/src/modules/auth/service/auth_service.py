import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from jose import jwt
from starlette import status

from src.core.repositories.repositories import Repositories
from src.core.settings.settings import settings
from src.modules.ldap.service.ldap_service import LDAPService, LDAPUser
from src.core.domain.auth.auth_schema.auth_schemas import LoginRequest, TokenResponse

from src.core.domain.user.user_model.user_model import User
from src.core.domain.user.user_model.user_role import UserRole

logger = logging.getLogger(__name__)


class AuthService:

    def __init__(self, repos: Repositories, ldap_service: LDAPService) -> None:
        self._repos = repos
        self._ldap = ldap_service

    async def login(self, credentials: LoginRequest) -> TokenResponse:
        """
        Authenticates a user via LDAP and returns a JWT token if successful.
        If the user doesn't exist in the local database, it creates it with
        the role of researcher.

        :param credentials: email e password

        :return: TokenResponse com JWT e dados do utilizador

        :raises HTTPException 401: se as credenciais forem inválidas
        """
        ldap_user = self._ldap.authenticate_by_email(
            credentials.email,
            credentials.password,
        )

        if not ldap_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = await self._sync_user(ldap_user)

        token = self._create_token(user)

        logger.info(f"Login successful: {user.email} (role={user.role.value}, id={user.id})")

        return TokenResponse(
            access_token=token,
            user_id=str(user.id),
            user_name=user.name,
            user_email=user.email,
            user_role=str(user.role.value)
        )

    async def _sync_user(self, ldap_user: LDAPUser) -> User:
        """
        Guarantees there is no local record for the LDAP user.
        If there isn't, creates it, if there is, updates the name.
        The userRole is given here, researcher by default.

        :param ldap_user: LDAPUser

        :return: User
        """
        async with self._repos as repos:
            user = await repos.users.get_by_email(ldap_user.mail)

            if not user:
                user = User(
                    id=uuid.uuid4(),
                    name=ldap_user.cn,
                    email=ldap_user.mail,
                    active=True,
                    role=UserRole.researcher,
                    researcherProfile=None,
                )
                await repos.users.save(user)
                logger.info(f"New user created for LDAP: {ldap_user.mail}")
            else:
                if user.name != ldap_user.cn:
                    user.name = ldap_user.cn
                    await repos.users.save(user)

            await repos.commit()
            return user

    @staticmethod
    def _create_token(user: User) -> str:
        """Creates a JWT Token for the user"""
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_EXPIRE_MINUTES
        )

        payload = {
            "sub":   str(user.id),
            "email": user.email,
            "name":  user.name,
            "role":  str(user.role.value),
            "exp":   expire,
        }

        return jwt.encode(
            payload,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
