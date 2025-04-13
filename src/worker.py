# from pydantic import BaseModel, create_model

# from fastapi import FastAPI, Request
# from fastapi_mcp import FastApiMCP

############## NORMAL ##############

# from js import Response

# async def on_fetch(request, env):
#     return Response.new("Hello")

####################################

############## FASTMCP ##############
from exceptions import HTTPException, http_exception
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Demo")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

@mcp.tool()
def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """Calculate BMI given weight in kg and height in meters"""
    return weight_kg / (height_m**2)

@mcp.prompt()
def echo_prompt(message: str) -> str:
    """Create an echo prompt"""
    return f"Please process this message: {message}"

# mcp depends on uvicorn and imports it at the top scope that we have to patch that to move the 
# import into the function that uses it.
# TODO(now): Change uvicorn to optional in mcp
app = mcp.sse_app()
# Starlette default http exception handler is sync which starlette tries to run in threadpool
# in https://github.com/encode/starlette/blob/master/starlette/_exception_handler.py#L61.
# Since we don't support threads we need to override it with the same function but async.
# TODO(now): change starlette's http_exception to be async, it is strictly slower to spawn a new
#            thread
app.add_exception_handler(HTTPException, http_exception)
async def on_fetch(request, env):
    import asgi
    return await asgi.fetch(app, request, env)

#####################################

############## FASTAPI ##############
# from fastapi import FastAPI, Request

# app = FastAPI()


# @app.get("/")
# async def root():
#     message = "This is an example of FastAPI"
#     return {"message": message}


# @app.get("/env")
# async def env(req: Request):
#     env = req.scope["env"]
#     return {
#         "message": "Here is an example of getting an environment variable: "
#         + env.MESSAGE
#     }

# async def on_fetch(request, env):
#     import asgi
#     return await asgi.fetch(app, request, env)

#####################################
