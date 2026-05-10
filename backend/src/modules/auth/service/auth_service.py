"""
AuthService — orquestra o login:
  1. Valida credenciais via LDAP
  2. Cria ou actualiza o User no sistema (sync)
  3. Devolve um JWT

Desta forma o sistema tem sempre um registo local do utilizador
(necessário para associar métricas, perfis, etc.) mas a autenticação
é sempre delegada ao LDAP — nunca guardamos passwords.
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from jose import jwt
from starlette import status

from src.core.repositories.repositories import Repositories
from src.core.settings.settings import settings
from src.modules.auth.schemas.auth_schemas import LoginRequest, TokenResponse
from src.modules.ldap.service.ldap_service import LDAPService, LDAPUser
from src.modules.user.model.role.user_role import UserRole
from src.modules.user.model.user_model import User

logger = logging.getLogger(__name__)


class AuthService:

    def __init__(self, repos: Repositories, ldap_service: LDAPService) -> None:
        self._repos = repos
        self._ldap = ldap_service

    async def login(self, credentials: LoginRequest) -> TokenResponse:
        """
        Autentica um utilizador via LDAP e devolve um JWT.

        :param credentials: email e password
        :return: TokenResponse com JWT e dados do utilizador
        :raises HTTPException 401: se as credenciais forem inválidas
        """
        # 1. Validar no LDAP
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

        # 2. Sync com a base de dados local
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

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    async def _sync_user(self, ldap_user: LDAPUser) -> User:
        """
        Garante que existe um registo local para o utilizador LDAP.
        - Se não existir → cria
        - Se existir → actualiza nome (pode ter mudado no LDAP)

        O role é determinado aqui — por defeito 'researcher'.
        Para promover a admin, alterar manualmente na DB ou via manage users.
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

    def _create_token(self, user: User) -> str:
        """Cria um JWT com os dados do utilizador."""
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
