import functools
import json
import logging
import multiprocessing
from asyncio import iscoroutinefunction
from multiprocessing.process import BaseProcess as Process
from typing import Optional, List

from broadcaster import Broadcast
from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi_utils.openapi import simplify_operation_ids
from starlette.responses import PlainTextResponse
from websockets import ConnectionClosedOK

from router import ContentAwareRouter
from ws.content_type.text_html import HttpContentTextHtml
from ws.content_type.text_plain import HttpContentTextPlain
from ws.model.thing import ThingColor, ThingType, Thing
from ws.publisher import demo_publisher

logger = logging.getLogger("res-ws")
logging.basicConfig(level=logging.INFO)

app = FastAPI()
router = ContentAwareRouter(
    content_type_mappings={
        "text/plain": HttpContentTextPlain,
        "text/html": HttpContentTextHtml,
    }
)

app.mount("/demo", StaticFiles(directory="public", html=True), name="demo_files")

broadcast = Broadcast("redis://localhost:6379")

demo_publisher_proc: Optional[Process] = None

thing_ids = ["a", "b", "c", "d", "e", "f", "g"]


@app.on_event("startup")
async def startup_event():
    global demo_publisher_proc
    await broadcast.connect()
    demo_publisher_proc = multiprocessing.Process(target=demo_publisher,
                                                  args=(thing_ids,))
    demo_publisher_proc.start()


@app.on_event("shutdown")
async def shutdown_event():
    global demo_publisher_proc
    await broadcast.disconnect()
    if demo_publisher_proc:
        demo_publisher_proc.terminate()


@router.get("/thing/")
async def get(type: ThingType = None, color: ThingColor = None) -> List[Thing]:
    redis_conn = broadcast._backend._pub_conn

    things = []
    for thing_id in thing_ids:
        data = json.loads(await redis_conn.get(thing_id))
        thing = Thing(**data)
        if type is not None and thing.type != type:
            continue
        if color is not None and thing.color != color:
            continue
        things.append(thing)
    return things


@router.websocket("/thing/")
async def get_ws(websocket: WebSocket):
    await websocket.accept()
    async with broadcast.subscribe(channel="$all") as subscriber:
        async for event in subscriber:
            try:
                await websocket.send_text(event.message)
            except ConnectionClosedOK:
                return
            except Exception as err:
                logger.exception(err)
                raise err


@router.get("/thing/{id}", status_code=201)
async def get_id(id: str) -> Thing:
    """
    Fetches a Thing by it's identifier
    """
    redis_conn = broadcast._backend._pub_conn
    data = await redis_conn.get(id)
    if data is None:
        return Response(content=json.dumps({"error": "Invalid Id"}), status_code=404)
    return Thing(**json.loads(data))


@router.websocket("/thing/{id}")
async def websocket_endpoint(id, websocket: WebSocket):
    await websocket.accept()
    async with broadcast.subscribe(channel=id) as subscriber:
        async for event in subscriber:
            try:
                await websocket.send_text(event.message)
            except ConnectionClosedOK:
                return
            except Exception as err:
                logger.exception(err)
                raise err


app.include_router(router)
simplify_operation_ids(app)

if __name__ == '__main__':
    import uvicorn

    uvicorn.run("main:app", log_level="info")
