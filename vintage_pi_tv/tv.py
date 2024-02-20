import logging
from pathlib import Path
import queue
import threading
import time

from .config import Config
from .keyboard import KEYBOARD_AVAILABLE, Keyboard
from .mpv_wrapper import MPV
from .player import Player
from .utils import (
    get_vintage_pi_tv_version,
    init_logger,
    is_docker,
    is_raspberry_pi,
    resolve_config_tries,
    retry_thread_wrapper,
    set_log_level,
)
from .videos import VideosDB


logger = logging.getLogger(__name__)


class VintagePiTV:
    def __init__(
        self,
        websocket_updates_queue: queue.Queue,
        event_queue: queue.Queue,
        config_file: str | Path | None = None,
        config_wait: int = 0,
        extra_search_dirs: list | tuple = (),
        log_level_override: None | str = None,
    ):
        init_logger()
        logger.info(f"Starting Vintage Pi TV version: {get_vintage_pi_tv_version()}")

        self._event_queue: queue.Queue = event_queue
        self._websocket_updates_queue: queue.Queue = websocket_updates_queue
        self._log_level_override = log_level_override
        self._extra_search_dirs = extra_search_dirs
        self.init_config(config_file=config_file, config_wait=config_wait)

        set_log_level(self.config.log_level)
        logger.debug(f"Changed log level to {self.config.log_level}")

        logger.info("Loaded config")
        logger.debug(f"Running in mode: {is_docker()=}, {is_raspberry_pi()=}")

        self.keyboard: Keyboard | None = None
        if self.config.keyboard["enabled"]:
            if KEYBOARD_AVAILABLE:
                logger.info("Enabling keyboard")
                self.keyboard = Keyboard(config=self.config, event_queue=event_queue)
            elif is_docker():
                logger.info("Enabling keyboard in Docker mode")
            else:
                logger.warning("Can't enable keyboard since it's not available on this platform")
                self.config.keyboard["enabled"] = False

        if (not self.config.keyboard["enabled"] or is_docker()) and self.config.ir_remote["enabled"]:
            logger.warning("Can't enable IR remote if keyboard is disabled (or in Docker dev mode)!")
            self.config.ir_remote["enabled"] = False

        # Initialize videos first, since it may exit and no sense opening an MPV window
        self.videos: VideosDB = VideosDB(config=self.config, websocket_updates_queue=websocket_updates_queue)
        self.mpv: MPV = MPV(config=self.config, event_queue=event_queue)
        self.player: Player = Player(
            config=self.config,
            videos_db=self.videos,
            mpv=self.mpv,
            keyboard=self.keyboard,
            event_queue=event_queue,
            websocket_updates_queue=websocket_updates_queue,
        )

        self.mpv.done_loading()
        logger.debug("Done initializing objects")

    def init_config(
        self,
        config_file: str | Path | None = None,
        config_wait: int = 0,
    ):
        config_file_tries = resolve_config_tries(config_file=config_file)
        self.config: Config = None
        kwargs = {
            "websocket_updates_queue": self._websocket_updates_queue,
            "extra_search_dirs": self._extra_search_dirs,
            "log_level_override": self._log_level_override,
        }

        for config_file_try in config_file_tries:
            for i in range(config_wait + 1):
                if config_file_try.exists():
                    logger.info(f"Using config file: {config_file_try}")
                    self.config = Config(path=config_file_try, **kwargs)
                    break
                else:
                    if i < config_wait:
                        logger.info(f"Config file {config_file_try} not found! Waiting.. (Try {i + 1}/{config_wait})")
                        time.sleep(1)
            if self.config is None:
                logger.warning(f"Config file {config_file_try} not found!")
            else:
                break
        else:
            if config_file_tries:
                logger.warning(f"Using a default config, none found at: {', '.join(map(str, config_file_tries))}")
            else:
                logger.warning("Using a default config as was none specified")
            self.config = Config(path=None, **kwargs)

    def startup(self):
        threads = [
            (self.videos.watch_dirs_thread, {"kwargs": {"recursive": False}, "daemon": False}),
            (self.videos.watch_dirs_thread, {"name": "watch_dirs_rec", "kwargs": {"recursive": True}, "daemon": False}),
            self.videos.rebuild_channels_thread,
            self.player.osd.osd_thread,
            self.player.static.static_thread,
            (self.player.player_thread, {"exc_cleanup_func": self.player.player_thread_cleanup}),
        ]
        if self.keyboard:
            threads.append(self.keyboard.keyboard_thread)

        for thread in threads:
            target, kwargs = thread if isinstance(thread, tuple) else (thread, {})
            daemon = kwargs.pop("daemon", True)
            cleanup = kwargs.pop("exc_cleanup_func", None)
            name = kwargs.pop("name", target.__name__.removesuffix("_thread"))
            target = retry_thread_wrapper(target, exc_cleanup_func=cleanup)
            logger.info(f"Spawning {name} thread")
            thread = threading.Thread(target=target, name=name, daemon=daemon, **kwargs)
            thread.start()

        threads = list(threading.enumerate())
        logger.debug(f"{len(threads)} threads are running {', '.join(t.name for t in threads)}")

        logger.info("Loading complete!")

    def shutdown(self):
        # Using a threading.Event for watchfiles prevents weird "FATAL: exception not rethrown" log messages
        self.videos.watch_stop_event.set()
