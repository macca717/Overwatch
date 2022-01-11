from pathlib import Path
import databases
from starlette.config import Config
from starlette.datastructures import CommaSeparatedStrings, Secret
from starlette.templating import Jinja2Templates
from .helpers import get_flash_messages


__all__ = [
    "BASE_DIR",
    "DEBUG",
    "SECRET_KEY",
    "ALLOWED_HOSTS",
    "TEMPLATES",
    "DATABASE",
    "DATABASE_URL",
    "VIDEO_DIR",
]

config = Config(".env")
BASE_DIR = Path(__file__).parent

DEBUG = config("DEBUG", cast=bool, default=False)
SECRET_KEY = config("SECRET_KEY", cast=Secret)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=CommaSeparatedStrings)
DATABASE_URL = config("DATABASE_URL")

VIDEO_DIR = Path("saves")
TEMPLATES = Jinja2Templates(directory=str(BASE_DIR / "templates"))
DATABASE = databases.Database(DATABASE_URL)

TEMPLATES.env.globals["get_flash_messages"] = get_flash_messages
