import os
import sys
import shutil
import contextlib
import PyInstaller.__main__

OUTPUT_FOLDER = "Completed Build"
TEMP_MAIN = "main_build.py"

def create_main_copy(main_script):
    with open(main_script, 'r', encoding='utf-8') as f:
        original_code = f.read()

    patched_code = f"""
import sys, os
import builtins

def resource_path(path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, path)

builtins.resource_path = resource_path
{original_code}
"""

    with open(TEMP_MAIN, 'w', encoding='utf-8') as f:
        f.write(patched_code)

def collect_data_files():
    data_files = []
    include_exts = (".json", ".ttf", ".jpg", ".jpeg", ".png")
    exclude_folders = {"__pycache__", ".git", ".idea", "venv", "dist", "build", OUTPUT_FOLDER}
    exclude_files = {TEMP_MAIN, "build.py"}

    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in exclude_folders]
        for file in files:
            if file in exclude_files:
                continue
            if file.lower().endswith(include_exts):
                full_path = os.path.join(root, file)
                rel_path = os.path.dirname(full_path)
                arg = f"{full_path}{os.pathsep}{rel_path}"
                data_files.append("--add-data")
                data_files.append(arg)
    return data_files

if __name__ == "__main__":
    while True:
        exe_name = input("Enter Project Name: ")
        main_script = input("Enter your main Python script (e.g., main.py): ")
        if os.path.exists(main_script) and main_script.endswith(".py"):
            break
        print(f"File '{main_script}' not found or invalid. Try again.")

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    print("[1/3] Creating temporary main_build.py...")
    create_main_copy(main_script)

    print("[2/3] Collecting project files...")
    data_files = collect_data_files()

    print("[3/3] Building executable...")
    pyinstaller_args = [
        TEMP_MAIN,
        "--onefile",
        "--windowed",
        "--name", exe_name,
        "--distpath", OUTPUT_FOLDER,
        "--noconfirm"
    ] + data_files

    with open(os.devnull, "w") as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            PyInstaller.__main__.run(pyinstaller_args)

    if os.path.exists(TEMP_MAIN):
        os.remove(TEMP_MAIN)
    if os.path.exists("build"):
        shutil.rmtree("build")
    spec_file = f"{exe_name}.spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)

    print(f"Build complete! Executable is in '{OUTPUT_FOLDER}/{exe_name}.exe'")
