import PyInstaller.__main__
import os
import shutil
import sys
import contextlib

def get_data_files():
    data_files = []
    excluded_folders = {'__pycache__', '.git', '.idea', 'venv', 'dist', 'build', 'Completed Build', 'build .exe'}
    excluded_files = {'build.py'}

    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in excluded_folders]
        for file in files:
            if file in excluded_files:
                continue
            full_path = os.path.join(root, file)
            relative_path = os.path.dirname(full_path)
            arg = f"{full_path}{os.pathsep}{relative_path}"
            data_files.append('--add-data')
            data_files.append(arg)
    return data_files


if __name__ == '__main__':
    output_folder = 'Completed Build'
    project_name = os.path.basename(os.getcwd())

    main_script_name = ""
    while True:
        script_input = input("Enter the name of your main Python script (e.g., app.py): ")
        if os.path.exists(script_input) and script_input.endswith('.py'):
            main_script_name = script_input
            break
        else:
            print(f"Error: '{script_input}' not found or is not a .py file. Please try again.")

    base_exe_name = project_name
    output_exe_name = base_exe_name
    counter = 2
    os.makedirs(output_folder, exist_ok=True)
    while os.path.exists(os.path.join(output_folder, f"{output_exe_name}.exe")):
        output_exe_name = f"{base_exe_name} ({counter})"
        counter += 1

    print("[1/3] Collecting project files...")
    data_to_include = get_data_files()

    print("[2/3] Building executable...")
    pyinstaller_args = [
        main_script_name,
        '--onefile',
        '--windowed',
        '--name', output_exe_name,
        '--distpath', output_folder,
        '--noconfirm'
    ] + data_to_include

    with open(os.devnull, 'w') as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            PyInstaller.__main__.run(pyinstaller_args)

    print("[3/3] Cleaning up temporary files...")
    if os.path.exists('build'):
        shutil.rmtree('build')
    spec_file = f'{output_exe_name}.spec'
    if os.path.exists(spec_file):
        os.remove(spec_file)

    print("Build complete.")