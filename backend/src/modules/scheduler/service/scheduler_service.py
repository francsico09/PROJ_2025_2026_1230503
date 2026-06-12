"""
SchedulerService — divide os investigadores em 7 grupos e extrai um grupo por dia.

Lógica de divisão:
  - Ordena os utilizadores por researcher_profile.id (UUID — estável entre execuções)
  - Divide em 7 grupos iguais
  - Hoje (weekday 0=Segunda … 6=Domingo) determina qual grupo processar
  - Se a extracção de um utilizador falhar, é marcado para retry no dia seguinte
    através de um ficheiro JSON de estado simples

Logs em ficheiro: logs/scheduler.log
Retries: ficheiro JSON em logs/retry_queue.json
"""
import json
import logging
import logging.handlers
import os
from datetime import datetime, date
from pathlib import Path
from uuid import UUID

from src.core.repositories.repositories import Repositories
from src.modules.extraction.service.pipeline_service import PipelineService

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger("scheduler")
logger.setLevel(logging.INFO)

_handler = logging.handlers.RotatingFileHandler(
    LOG_DIR / "scheduler.log",
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=3,
    encoding="utf-8",
    )
_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
))
logger.addHandler(_handler)

RETRY_FILE = LOG_DIR / "retry_queue.json"


def _load_retry_queue() -> list[str]:
    """Carrega a lista de researcher_profile_ids que falharam ontem."""
    if not RETRY_FILE.exists():
        return []
    try:
        return json.loads(RETRY_FILE.read_text())
    except Exception:
        return []


def _save_retry_queue(ids: list[str]) -> None:
    RETRY_FILE.write_text(json.dumps(ids, indent=2))


def _clear_retry_queue() -> None:
    if RETRY_FILE.exists():
        RETRY_FILE.unlink()


def _divide_into_groups(items: list, n: int) -> list[list]:
    """Divide uma lista em n grupos o mais iguais possível."""
    if not items:
        return [[] for _ in range(n)]
    size = max(1, len(items) // n)
    groups = []
    for i in range(n):
        start = i * size
        end = start + size if i < n - 1 else len(items)
        groups.append(items[start:end])
    return groups


class SchedulerService:

    def __init__(self, pipeline_service: PipelineService) -> None:
        self._pipeline = pipeline_service

    async def run_daily_extraction(self) -> None:
        """
        Job principal — corre às 03:00 todos os dias.

        1. Carrega todos os utilizadores activos com perfil de investigador
        2. Ordena por researcher_profile.id para divisão estável
        3. Determina o grupo do dia (weekday 0-6)
        4. Processa o grupo de hoje + retries do dia anterior
        5. Falhas são guardadas para retry amanhã
        """
        today = date.today()
        day_of_week = datetime.now().weekday()  # 0=Segunda, 6=Domingo

        logger.info(f"=== Daily extraction started — {today} (group {day_of_week}) ===")

        # 1. Carregar utilizadores com perfil
        users_with_profile = await self._load_users_with_profile()
        if not users_with_profile:
            logger.warning("No active researchers with profiles found. Skipping.")
            return

        # 2. Ordenar por profile id para divisão estável
        sorted_users = sorted(users_with_profile, key=lambda u: str(u["profile_id"]))

        # 3. Dividir em 7 grupos e seleccionar o de hoje
        groups = _divide_into_groups(sorted_users, 7)
        todays_group = groups[day_of_week]

        logger.info(
            f"Total researchers: {len(sorted_users)} | "
            f"Group {day_of_week}: {len(todays_group)} researchers"
        )

        # 4. Retries do dia anterior
        retry_ids = _load_retry_queue()
        retry_users = [u for u in sorted_users if str(u["profile_id"]) in retry_ids]
        _clear_retry_queue()

        if retry_users:
            logger.info(f"Retry queue: {len(retry_users)} researchers from previous day")

        # 5. Processar: retries primeiro, depois grupo de hoje
        failed: list[str] = []

        for user in retry_users:
            success = await self._extract_for_user(user, is_retry=True)
            if not success:
                failed.append(str(user["profile_id"]))

        for user in todays_group:
            success = await self._extract_for_user(user)
            if not success:
                failed.append(str(user["profile_id"]))

        # 6. Guardar falhas para amanhã
        if failed:
            _save_retry_queue(failed)
            logger.warning(f"{len(failed)} researchers queued for retry tomorrow: {failed}")

        logger.info(
            f"=== Extraction complete — "
            f"{len(todays_group) + len(retry_users) - len(failed)} succeeded, "
            f"{len(failed)} failed ==="
        )

    async def _extract_for_user(self, user: dict, is_retry: bool = False) -> bool:
        """
        Corre o pipeline de extracção para um único utilizador.
        Devolve True se bem-sucedido, False se falhou.
        """
        prefix = "[RETRY]" if is_retry else "[EXTRACT]"
        user_id = user["user_id"]
        name    = user["name"]

        try:
            logger.info(f"{prefix} Starting: {name} (user_id={user_id})")
            result = await self._pipeline.run_for_user(user_id)

            if result.errors:
                logger.warning(f"{prefix} Partial: {name} — {result.errors}")
            else:
                logger.info(
                    f"{prefix} OK: {name} — "
                    f"metric_created={result.metric_created}, "
                    f"profile_updated={result.profile_updated}"
                )
            return True

        except Exception as e:
            logger.error(f"{prefix} FAILED: {name} (user_id={user_id}) — {e}", exc_info=True)
            return False

    async def _load_users_with_profile(self) -> list[dict]:
        """
        Devolve lista de dicts com user_id, profile_id e name
        para todos os utilizadores activos com perfil de investigador.
        """
        async with Repositories() as repos:
            users = await repos.users.get_all()

        result = []
        for user in users:
            if not user.active:
                continue
            if not user.researcherProfile:
                continue
            result.append({
                "user_id":    user.id,
                "profile_id": user.researcherProfile.id,
                "name":       user.name,
            })

        return result