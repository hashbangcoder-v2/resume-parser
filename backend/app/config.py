from omegaconf import OmegaConf, DictConfig
import os
import dotenv
from pathlib import Path
from app.logger import logger

dotenv.load_dotenv()

def get_config() -> DictConfig:
    # Load base configuration
    project_root = os.getenv("PROJECT_ROOT")
    if not project_root:
        raise ValueError("PROJECT_ROOT environment variable is not set. Please set it to the path of the project root.")
    # Determine environment and merge environment-specific config
    env = os.getenv("APP_ENV", "dev")
    logger.info(f"Loading configuration for environment: {env}")
    env_conf_path = Path(project_root) / 'config' / f'{env}.yaml'
    base_config_path = Path(project_root) / 'config' / 'config.yaml'
    if env_conf_path.exists() and base_config_path.exists():
        base_config = OmegaConf.load(base_config_path)
        env_conf = OmegaConf.load(env_conf_path)
        conf = OmegaConf.merge(base_config, env_conf)
    else:
        raise ValueError(f"Configuration files not found for environment: {env}")
    logger.info(f"Configuration loaded successfully.")
    return conf
