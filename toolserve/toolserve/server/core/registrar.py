#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from toolserve.server.routes import v1
from toolserve.server.core.conf import settings
from toolserve.common.serializers import MsgSpecJSONResponse

def register_app():
    # FastAPI
    app = FastAPI(
        title=settings.TITLE,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        docs_url=settings.DOCS_URL,
        redoc_url=settings.REDOCS_URL,
        openapi_url=settings.OPENAPI_URL,
        default_response_class=MsgSpecJSONResponse,
    )

    register_static_file(app)

    register_middleware(app)

    register_router(app)

    #register_exception(app)

    generate_actions_routers(app)

    return app


def register_static_file(app: FastAPI):
    """

    :param app:
    :return:
    """
    if settings.STATIC_FILES:
        import os

        from fastapi.staticfiles import StaticFiles

        if not os.path.exists('./static'):
            os.mkdir('./static')
        app.mount('/static', StaticFiles(directory='static'), name='static')


def register_middleware(app: FastAPI):
    """

    :param app:
    :return:
    """
    # Gzip: Always at the top
    if settings.MIDDLEWARE_GZIP:
        from fastapi.middleware.gzip import GZipMiddleware

        app.add_middleware(GZipMiddleware)

    # CORS: Always at the end
    if settings.MIDDLEWARE_CORS:
        from fastapi.middleware.cors import CORSMiddleware

        app.add_middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )


def register_router(app: FastAPI):
    """
    路由

    :param app: FastAPI
    :return:
    """
    dependencies = None

    # API
    app.include_router(v1, dependencies=dependencies)


def generate_actions_routers(app: FastAPI):
    """

    :param app: FastAPI
    :return:
    """
    from toolserve.server.core.generate import generate_endpoint
    from toolserve.server.core.catalog import ToolCatalog

    catalog = ToolCatalog()
    router = generate_endpoint(catalog.tools.values())
    app.include_router(router)
    app.state.catalog = catalog