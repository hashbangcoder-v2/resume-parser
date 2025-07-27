from omegaconf import OmegaConf
import os

def get_config():
    # Load base configuration
    conf_path = os.getenv("CONFIG_PATH")
    if not conf_path:
        raise ValueError("CONFIG_PATH environment variable is not set. Please set it to the path of the config file.")
    
    conf = OmegaConf.load(conf_path)

    # Determine environment and merge environment-specific config
    env = os.getenv("APP_ENV", "dev")
    env_conf_path = os.path.join(os.path.dirname(conf_path), f'{env}.yaml')
    
    if os.path.exists(env_conf_path):
        env_conf = OmegaConf.load(env_conf_path)
        conf = OmegaConf.merge(conf, env_conf)
    
    return conf
