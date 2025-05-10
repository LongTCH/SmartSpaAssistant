import asyncio
import atexit
import logging
from functools import wraps
from typing import Any, Coroutine, List, Set, TypeVar

# Type variable cho generic functions
T = TypeVar("T")

# Logging
logger = logging.getLogger("asyncio_utils")

# Global event loop và task registry
_LOOP = None
_BACKGROUND_TASKS: Set[asyncio.Task] = set()


def get_event_loop() -> asyncio.AbstractEventLoop:
    """Lấy hoặc tạo event loop chung"""
    global _LOOP

    try:
        # Thử lấy event loop hiện tại
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        # Không có event loop trong thread hiện tại
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    _LOOP = loop
    return loop


def run_async(coro: Coroutine) -> Any:
    """Chạy một coroutine từ code đồng bộ và đợi kết quả"""
    loop = get_event_loop()

    if loop.is_running():
        # Nếu loop đang chạy, chạy coro trong loop hiện tại
        return asyncio.run_coroutine_threadsafe(coro, loop).result()
    else:
        # Nếu loop chưa chạy, chạy coro trong loop mới
        return loop.run_until_complete(coro)


def async_to_sync(func):
    """Decorator chuyển async function thành sync function"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        return run_async(func(*args, **kwargs))

    return wrapper


def create_task(coro, name=None) -> asyncio.Task:
    """Tạo task trong background và theo dõi nó"""
    if not asyncio.iscoroutine(coro):
        raise TypeError(f"Expected a coroutine, got {coro!r}")

    async def _wrapped():
        try:
            return await coro
        except asyncio.CancelledError:
            logger.info(f"Task {name or 'unnamed'} was cancelled")
            raise
        except Exception as e:
            logger.exception(f"Error in task {name or 'unnamed'}: {e}")
            raise

    get_event_loop()
    task = asyncio.create_task(_wrapped(), name=name)
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(
        lambda t: _BACKGROUND_TASKS.remove(t) if t in _BACKGROUND_TASKS else None
    )
    return task


def run_background(func, *args, **kwargs):
    """
    Chạy một hàm (async hoặc sync) trong background

    Ví dụ:
        # Hàm async
        run_background(process_data, user_id=123)

        # Hàm sync
        run_background(lambda: time.sleep(10))
    """
    if asyncio.iscoroutinefunction(func):
        # Nếu là async function, tạo coroutine
        coro = func(*args, **kwargs)
        return create_task(coro, name=func.__name__)
    else:
        # Nếu là sync function, chạy trong executor
        loop = get_event_loop()
        future = loop.run_in_executor(None, lambda: func(*args, **kwargs))
        return create_task(future, name=func.__name__)


class BackgroundTasks:
    """
    Class quản lý nhiều background tasks, giống FastAPI

    Ví dụ:
        bg = BackgroundTasks()
        bg.add_task(send_email, to="user@example.com")
        bg.add_task(process_data, user_id=123)
        bg.run_all()  # Chạy tất cả tasks
    """

    def __init__(self):
        self.tasks = []

    def add_task(self, func, *args, **kwargs):
        """Thêm task vào queue"""
        self.tasks.append((func, args, kwargs))

    def run_all(self) -> List[asyncio.Task]:
        """Chạy tất cả tasks đã thêm và trả về danh sách tasks"""
        started_tasks = []
        for func, args, kwargs in self.tasks:
            task = run_background(func, *args, **kwargs)
            started_tasks.append(task)
        self.tasks.clear()
        return started_tasks


@atexit.register
def cleanup():
    """Dọn dẹp khi chương trình kết thúc"""
    logger.info("Performing server cleanup...")

    # Hủy tất cả background tasks
    if _BACKGROUND_TASKS:
        logger.info(f"Cancelling {len(_BACKGROUND_TASKS)} pending tasks...")
        for task in list(_BACKGROUND_TASKS):
            if not task.done():
                task.cancel()

        # Đợi tất cả tasks hủy hoàn tất
        if _BACKGROUND_TASKS:
            loop = get_event_loop()
            if not loop.is_closed() and loop.is_running():
                try:
                    # Đợi các task cancel hoàn tất trong 5 giây
                    pending = asyncio.all_tasks(loop)
                    if pending:
                        loop.run_until_complete(asyncio.wait(pending, timeout=5))
                except Exception as e:
                    logger.error(f"Error while waiting for tasks to cancel: {e}")

    # Đóng event loop
    global _LOOP
    if _LOOP and not _LOOP.is_closed():
        try:
            # Đóng các executor nếu có
            _LOOP.run_until_complete(_LOOP.shutdown_asyncgens())
            _LOOP.run_until_complete(_LOOP.shutdown_default_executor())
        except Exception as e:
            logger.error(f"Error during event loop cleanup: {e}")
        finally:
            _LOOP.close()
            logger.info("Event loop closed")

    logger.info("Server cleanup completed")
