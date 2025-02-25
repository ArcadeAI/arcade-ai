import os

from modal import App, Image, asgi_app

# Define the FastAPI app
app = App("arcade-worker")

toolkits = ["arcade_google", "arcade_slack"]

image = Image.debian_slim().pip_install("arcade-ai[fastapi]").pip_install(toolkits)


@app.function(image=image)
@asgi_app()
def fastapi_app():
    from fastapi import FastAPI

    from arcade.sdk import Toolkit
    from arcade.worker.fastapi.worker import FastAPIWorker

    web_app = FastAPI()

    # Initialize app and Arcade FastAPIWorker
    worker_secret = os.environ.get("ARCADE_WORKER_SECRET", "dev")
    worker = FastAPIWorker(web_app, secret=worker_secret)

    # Register toolkits we've installed
    installed_toolkits = Toolkit.find_all_arcade_toolkits()
    for toolkit in installed_toolkits:
        print(toolkit.package_name)
        if toolkit.package_name in toolkits:
            worker.register_toolkit(toolkit)

    return web_app
