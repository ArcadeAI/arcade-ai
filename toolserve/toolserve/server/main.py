import uvicorn

from pathlib import Path
import asyncio
from toolserve.server.common.log import log
from toolserve.server.core.conf import settings
from toolserve.server.core.registrar import register_app


app = register_app()

if __name__ == '__main__':
    try:
        log.info(
            "Arcade AI Toolserve is starting..."
        )
        uvicorn.run(
            app=f'{Path(__file__).stem}:app',
            host=settings.UVICORN_HOST,
            port=settings.UVICORN_PORT,
            reload=settings.UVICORN_RELOAD,
        )
    except Exception as e:
        log.error(f'❌ FastAPI start filed: {e}')