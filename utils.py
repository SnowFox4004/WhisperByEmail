import json
from loguru import logger
import sys


def load_settings(setting_names: list) -> tuple:

    try:
        settings = json.load(open("./SETTINGS.json", 'r', encoding='utf-8'))
        result = tuple(settings[i.upper()] for i in setting_names)
    except FileNotFoundError:
        logger.error("无配置文件，请在目录下配置 SETTINGS.json")
        sys.exit(-1)
    except Exception as err:
        result = tuple(None for i in setting_names)
        logger.error(f"读取设置项时出错 {err}")
        sys.exit(-1)

    return result
