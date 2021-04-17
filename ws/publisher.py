import asyncio
import logging
import random
from asyncio.tasks import sleep

from broadcaster import Broadcast

from ws.model.thing import Thing

logger = logging.getLogger("res-ws")


def demo_publisher(thing_ids):
    broadcast = Broadcast("redis://localhost:6379")

    async def init():
        await broadcast.connect()

        logger.info("Publisher Connected")
        loop = asyncio.get_event_loop()
        for thing_id in thing_ids:
            loop.create_task(publish(thing_id))

    async def publish(id):
        logger.debug(f"Publish {id}")

        new_obj = Thing.new_random(id)
        redis_conn = broadcast._backend._pub_conn

        thing_str = new_obj.json()
        await redis_conn.set(id, thing_str)

        await broadcast.publish(id, thing_str)
        await broadcast.publish("$all", thing_str)
        await sleep(random.random() * 10 + 5)
        loop = asyncio.get_event_loop()
        loop.create_task(publish(id))

    loop = asyncio.new_event_loop()
    loop.create_task(init())
    loop.run_forever()
