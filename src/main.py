import logging
import sys

from .app import App
from .utils import get_app_path

logging.basicConfig(
    filename=str(get_app_path() / "hackablock.log"),
    filemode="a",
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO
)

if sys.platform == "win32":
    import ctypes
    app_id = "Hackablock.App"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

if __name__ == "__main__":
    app = App()
    app.run()