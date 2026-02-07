"""
Add Qwen Server to Windows startup so it runs when the user logs in.
Author: Onkar Mundhe
"""

import os
import sys
from pathlib import Path

def get_startup_folder():
    return Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

def main():
    project_dir = Path(__file__).resolve().parent
    bat_path = project_dir / "Start_Qwen_Server.bat"
    if not bat_path.exists():
        print("Start_Qwen_Server.bat not found in project folder.")
        sys.exit(1)

    startup = get_startup_folder()
    if not startup.exists():
        print("Startup folder not found:", startup)
        sys.exit(1)

    # Create shortcut that runs the batch with "silent" so launcher closes after opening browser
    try:
        import win32com.client
    except ImportError:
        print("Installing pywin32 for shortcut creation...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
        import win32com.client

    shortcut_path = startup / "Qwen Server.lnk"
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(shortcut_path))
    shortcut.TargetPath = "cmd.exe"
    shortcut.Arguments = '/c "{}" silent'.format(bat_path)
    shortcut.WorkingDirectory = str(project_dir)
    shortcut.WindowStyle = 0
    shortcut.save()
    print("Done. Qwen Server will start when you log in to Windows.")
    print("Startup shortcut:", shortcut_path)
    print("To remove: run remove_from_startup.py")
    return

if __name__ == "__main__":
    main()
