from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    def __init__(self, max_workers: int = 5):
        """Initialize the thread pool with the given number of workers."""
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def run_task(
        self,
        func: Callable[..., Any],
        args: List[Any] = None,
        kwargs: dict = None,
        callbacks: List[Optional[Callable[[Any], None]]] = None,
        error_callbacks: List[Optional[Callable[[Any], None]]] = None,
        context={},
    ) -> None:
        """Execute a function in the background and optionally run a callback after it finishes."""
        args = args or []
        kwargs = kwargs or {}

        def task_wrapper():
            """Wrapper to execute the function and call the callback if provided."""
            try:
                logger.debug(f"Starting background task: {func.__name__}")
                result = func(*args, **kwargs)
                context["task_result"] = result
                if callbacks:
                    logger.debug(
                        f"Executing callback after task: {[callback.__name__ for callback in callbacks if hasattr(callback, '__name__')]}"
                    )
                    for callback in callbacks:
                        try:
                            result = callback(context)
                            logger.info(f"Callback result: {result}")
                        except Exception as e:
                            logger.error(f"Failed to execute callback:{callback} {e} ")
            except Exception as error:
                logger.error(f"Error in background task: {error}")
                if error_callbacks:
                    context["error"] = error
                    for error_callback in error_callbacks:
                        error_callback(context)

        # Submit the task wrapper to the thread pool (fire-and-forget)
        self.executor.submit(task_wrapper)

    def shutdown(self, wait: bool = True):
        """Gracefully shut down the executor."""
        logger.debug("Shutting down thread pool executor.")
        self.executor.shutdown(wait=wait)


singleton_task_manager = BackgroundTaskManager(max_workers=10)


def get_task_manager():
    return singleton_task_manager