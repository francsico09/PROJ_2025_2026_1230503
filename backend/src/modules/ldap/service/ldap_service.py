"""
LDAPService — responsável por toda a comunicação com o servidor LDAP.
Usa ldap3 (pure Python, sem dependências de sistema).

Estrutura do LDAP do ISEP mock:
  - Utilizadores: uid=upXXXXXXXXX,ou=people,dc=isep,dc=ipp,dc=pt
  - Atributos: uid, cn, sn, mail
  - Grupos:    cn=students,ou=groups,dc=isep,dc=ipp,dc=pt
"""
import logging
from dataclasses import dataclass
from typing import Optional

from ldap3 import Server, Connection, ALL, SUBTREE
from ldap3.core.exceptions import LDAPException, LDAPBindError, LDAPInvalidCredentialsResult

from src.core.settings.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class LDAPUser:
    uid: str
    cn: str
    sn: str
    mail: str
    dn: str


class LDAPService:

    def __init__(self) -> None:
        self._server = Server(
            settings.LDAP_HOST,
            port=settings.LDAP_PORT,
            get_info=ALL,
        )

    def authenticate(self, uid: str, password: str) -> Optional[LDAPUser]:
        """
        Tenta autenticar um utilizador pelo uid (ex: up202012345) e password.

        Fluxo:
          1. Admin bind — para poder pesquisar o DN completo do utilizador
          2. Pesquisa o DN pelo uid
          3. User bind — valida a password com o DN encontrado
          4. Devolve LDAPUser com os atributos, ou None se falhar

        :param uid: identificador do utilizador (ex: up202012345)
        :param password: password em texto simples
        :return: LDAPUser ou None
        """
        user_dn = self._find_user_dn(uid)
        if not user_dn:
            logger.warning(f"[LDAP] User not found: {uid}")
            return None

        return self._bind_as_user(user_dn, password)

    def authenticate_by_email(self, email: str, password: str) -> Optional[LDAPUser]:
        """
        Alternativa ao authenticate() — pesquisa por email em vez de uid.
        Útil para o login do frontend onde o utilizador introduz o email.

        :param email: email do utilizador
        :param password: password em texto simples
        :return: LDAPUser ou None
        """
        user_dn, attrs = self._search_user(filter_=f"(mail={email})")
        if not user_dn:
            logger.warning(f"[LDAP] Email not found: {email}")
            return None

        ldap_user = self._bind_as_user(user_dn, password)
        return ldap_user

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _admin_connection(self) -> Connection:
        """Opens an authenticated session with admin"""
        conn = Connection(
            self._server,
            user=settings.LDAP_ADMIN_DN,
            password=settings.LDAP_ADMIN_PASSWORD,
            auto_bind=True,
        )
        return conn

    def _find_user_dn(self, uid: str) -> Optional[str]:
        """Search the complete DN to find user by uid"""
        dn, _ = self._search_user(filter_=f"(uid={uid})")
        return dn

    def _search_user(self, filter_: str) -> tuple[Optional[str], Optional[dict]]:
        """
        Executes one search on LDAP with the given filter.
        Returns information from the first result or None
        """
        try:
            with self._admin_connection() as conn:
                conn.search(
                    search_base=settings.LDAP_PEOPLE_OU,
                    search_filter=filter_,
                    search_scope=SUBTREE,
                    attributes=["uid", "cn", "sn", "mail"],
                )

                logger.info(conn.entries)

                if not conn.entries:
                    return None, None

                entry = conn.entries[0]
                attrs = {
                    "uid":  str(entry.uid),
                    "cn":   str(entry.cn),
                    "sn":   str(entry.sn),
                    "mail": str(entry.mail),
                }
                return entry.entry_dn, attrs

        except LDAPException as e:
            logger.error(f"[LDAP] Search error ({filter_}): {e}")
            return None, None

    def _bind_as_user(self, user_dn: str, password: str) -> Optional[LDAPUser]:
        """
        Tries to bind user with user dn and password.
        If successful returns the user.
        """
        try:
            with Connection(
                    self._server,
                    user=user_dn,
                    password=password,
                    auto_bind=True,
            ) as conn:
                conn.search(
                    search_base=user_dn,
                    search_filter="(objectClass=inetOrgPerson)",
                    search_scope=SUBTREE,
                    attributes=["uid", "cn", "sn", "mail"],
                )

                if not conn.entries:
                    return None

                entry = conn.entries[0]
                return LDAPUser(
                    uid=str(entry.uid),
                    cn=str(entry.cn),
                    sn=str(entry.sn),
                    mail=str(entry.mail),
                    dn=user_dn,
                )

        except LDAPBindError:
            logger.warning(f"[LDAP] Incorrect password for DN: {user_dn}")
            return None
        except LDAPInvalidCredentialsResult:
            logger.warning(f"[LDAP] Invalid Credentials for DN: {user_dn}")
            return None
        except LDAPException as e:
            logger.error(f"[LDAP] Bind error for {user_dn}: {e}")
            return None
