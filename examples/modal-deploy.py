import os

from modal import App, Image, asgi_app

os.environ["WORK_DIR"] = "/root"

# Define the FastAPI app
app = App("arcade-ai-actor")


image = (
    Image.debian_slim()
    .copy_local_dir("./dist", "/root/dist")
    .pip_install("/root/dist/arcade_ai-0.1.0-py3-none-any.whl")
    .pip_install("/root/dist/arcade_gmail-0.1.0-py3-none-any.whl")
    .pip_install("/root/dist/arcade_websearch-0.1.0-py3-none-any.whl")
    .pip_install("/root/dist/arcade_slack-0.1.0-py3-none-any.whl")
    .pip_install("fastapi>=0.110.0")
    .pip_install("uvicorn>=0.24.0")
    .pip_install("pydantic>=2.7.0")
    .copy_local_file("./arcade.toml", "/root/arcade.toml")
)


@app.function(image=image)
@asgi_app()
def fastapi_app():
    from fastapi import FastAPI

    from arcade.actor.fastapi.actor import FastAPIActor
    from arcade.core.toolkit import Toolkit

    web_app = FastAPI()

    # Initialize app and Arcade FastAPIActor
    actor = FastAPIActor(web_app)

    # Register toolkits we've installed
    toolkits = Toolkit.find_all_arcade_toolkits()
    for toolkit in toolkits:
        actor.register_toolkit(toolkit)

    return web_app
