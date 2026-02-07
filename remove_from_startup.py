"""
Remove Qwen Server from Windows startup.
Author: Onkar Mundhe
"""

import os
import sys
from pathlib import Path

def get_startup_folder():
    return Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

def main():
    startup = get_startup_folder()
    shortcut_path = startup / "Qwen Server.lnk"
    if shortcut_path.exists():
        try:
            shortcut_path.unlink()
            print("Removed from startup.")
        except Exception as e:
            print("Error removing:", e)
            sys.exit(1)
    else:
        print("Qwen Server was not in startup.")

if __name__ == "__main__":
    main()
