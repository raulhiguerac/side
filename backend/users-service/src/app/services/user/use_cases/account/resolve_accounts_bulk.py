import time
import uuid

from app.core.logging.logger import get_logger
from app.services.shared.ports.account_reader import AccountReaderPort

logger = get_logger(__name__)


class ResolveAccountsBulkUseCase:
    def __init__(self, *, account_reader: AccountReaderPort) -> None:
        self.account_reader = account_reader

    async def execute(self, *, emails: list[str]) -> list[tuple[uuid.UUID, str]]:
        started = time.monotonic()
        resolved = await self.account_reader.get_accounts_bulk(emails=emails)

        # Callers treat a missing email as "no active account" and fail that row,
        # so the unmatched count is the number worth watching during a bulk import.
        logger.info(
            "resolve_accounts_bulk",
            extra={
                "extra": {
                    "requested": len(emails),
                    "resolved": len(resolved),
                    "unmatched": len(emails) - len(resolved),
                    "elapsed_s": round(time.monotonic() - started, 3),
                }
            },
        )
        return resolved
