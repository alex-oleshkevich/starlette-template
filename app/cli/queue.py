import multiprocessing

import anyio
import click
from saq.worker import start

from app.config import settings
from app.config.queues import debug_task, task_queue
from redis.exceptions import ConnectionError

queue_group = click.Group(name="queue", help="Worker queue.")


@queue_group.command("worker")
@click.option("--workers", "-w", default=1, help="Number of workers.")
@click.option("--web", is_flag=True, help="Start the web server.")
@click.option("--web-port", default=5001, type=int, help="Port for the web server.")
def start_queue_command(web: bool, workers: int, web_port: int) -> None:
    settings_attr = "{package}.config.queues.queue_settings".format(package=settings.package_name)
    if workers > 1:
        for _ in range(workers - 1):
            p = multiprocessing.Process(target=start, args=(settings_attr,))
            p.start()
    try:
        start(
            settings_attr,
            web=web,
            port=web_port,
            extra_web_settings=[],
        )
    except (KeyboardInterrupt, ConnectionError):
        pass


@queue_group.command("test")
def test_queue_command() -> None:
    async def main() -> None:
        job = await task_queue.enqueue(debug_task.__qualname__)
        await task_queue.disconnect()
        assert job
        click.echo(f"Task enqueued: {job.id}")

    anyio.run(main)
