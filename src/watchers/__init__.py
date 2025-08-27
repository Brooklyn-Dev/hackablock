import sys

if sys.platform == "win32":
    from .windows import watch_processes
elif sys.platform.startswith("linux"):
    from .linux import watch_processes
elif sys.platform ==  "darwin":
    from .macos import watch_processes
else:
    watch_processes = None