import sys
from pathlib import Path
from loguru import logger
from omegaconf import DictConfig

def setup_logging(cfg: DictConfig):
    """
    Set up Loguru logger with console and file sinks.
    """
    log_file_path = Path(cfg.logging.file)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    logger.remove()

    # Console logger
    logger.add(
        sys.stderr,
        level=cfg.logging.level.upper(),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # File logger
    logger.add(
        log_file_path,
        level=cfg.logging.level.upper(),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    logger.info("Logger setup complete.") 