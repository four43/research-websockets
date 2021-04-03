import asyncio
import json
import logging
import multiprocessing
import random
from asyncio import sleep
from datetime import datetime
from multiprocessing.process import BaseProcess as Process
from typing import Optional

from broadcaster import Broadcast
from fastapi import FastAPI, WebSocket
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger("res-ws")
logging.basicConfig(level=logging.INFO)

app = FastAPI()
app.mount("/demo", StaticFiles(directory="public", html=True), name="demo_files")

broadcast = Broadcast("redis://localhost:6379")

demo_publisher_proc: Optional[Process] = None

thing_ids = ["a", "b", "c"]


class ExampleObj:
    colors = [
        "red",
        "green",
        "blue",
        "yellow",
        "black",
        "orange",
        "purple"
    ]
    things = [
        "car",
        "dog",
        "house",
        "sign",
        "bike"
    ]

    def __init__(self, id):
        self.id = id
        self.color = random.choice(ExampleObj.colors)
        self.thing = random.choice(ExampleObj.things)

    def __json__(self):
        return self.__dict__

    def __str__(self):
        return f"{self.color} {self.thing}"


def demo_publisher():
    broadcast = Broadcast("redis://localhost:6379")

    async def init():
        await broadcast.connect()

        logger.info("Publisher Connected")
        loop = asyncio.get_event_loop()
        for thing_id in thing_ids:
            loop.create_task(publish(thing_id))

    async def publish(id):
        logger.info(f"Publish {id}")

        new_obj = ExampleObj(id)
        redis_conn = broadcast._backend._pub_conn

        thing_str = json.dumps(new_obj.__json__())
        await redis_conn.set(id, thing_str)

        await broadcast.publish(id, thing_str)
        await broadcast.publish("$all", thing_str)
        await sleep(random.random() * 10 + 5)
        loop = asyncio.get_event_loop()
        loop.create_task(publish(id))

    loop = asyncio.new_event_loop()
    loop.create_task(init())
    loop.run_forever()


@app.on_event("startup")
async def startup_event():
    global demo_publisher_proc
    await broadcast.connect()
    demo_publisher_proc = multiprocessing.Process(target=demo_publisher,
                                                  args=())
    demo_publisher_proc.start()


@app.on_event("shutdown")
async def shutdown_event():
    global demo_publisher_proc
    await broadcast.disconnect()
    if demo_publisher_proc:
        demo_publisher_proc.terminate()


@app.get("/thing/")
async def get():
    redis_conn = broadcast._backend._pub_conn

    things = []
    for thing_id in thing_ids:
        things.append(json.loads(await redis_conn.get(thing_id)))
    return things


@app.websocket("/thing/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    async with broadcast.subscribe(channel="$all") as subscriber:
        async for event in subscriber:
            try:
                await websocket.send_text(event.message)
            except Exception as err:
                logger.exception(err)


@app.get("/thing/{id}")
async def get_id(id):
    redis_conn = broadcast._backend._pub_conn
    data = await redis_conn.get(id)
    if data is None:
        return Response(content=json.dumps({"error": "Invalid Id"}), status_code=404)
    return json.loads(data)


@app.websocket("/thing/{id}")
async def websocket_endpoint(id, websocket: WebSocket):
    await websocket.accept()
    async with broadcast.subscribe(channel=id) as subscriber:
        async for event in subscriber:
            try:
                await websocket.send_text(event.message)
            except Exception as err:
                logger.exception(err)


if __name__ == '__main__':
    import uvicorn

    uvicorn.run("main:app", log_level="info")
