import asyncio

from app.database import SessionLocal
from app.services.resource_sync_service import (
    sync_ec2_resources,
)


SYNC_INTERVAL_SECONDS = 120


async def automatic_resource_sync():
    """
    Har 2 minute AWS aur MySQL resources sync karega.
    """

    while True:
        db = SessionLocal()

        try:
            await asyncio.to_thread(
                sync_ec2_resources,
                db,
            )

            print(
                "Automatic AWS resource sync completed."
            )

        except Exception as error:
            print(
                "Automatic AWS resource sync failed:",
                error,
            )

        finally:
            db.close()

        await asyncio.sleep(
            SYNC_INTERVAL_SECONDS
        )