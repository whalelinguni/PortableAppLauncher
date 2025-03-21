import os
import sys
import time
import configparser
import subprocess
import ctypes
import shutil
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer

# Set a default value for debug_mode before reading the ini file
debug_mode = False

# Get script directory
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    script_dir = os.path.dirname(sys.executable)
else:
    # Running as script
    script_dir = os.path.dirname(os.path.abspath(__file__))

log_file = os.path.join(script_dir, "launcher_debug.log")  # Log file path
LOG_MAX_SIZE = 1 * 1024 * 1024  # 1MB

# Define paths
ini_path = os.path.join(script_dir, "App", "AppInfo", "Launcher", "launcher.ini")
splash_path = os.path.join(script_dir, "App", "AppInfo", "Launcher", "splash.jpg")

# Read ini file (disable interpolation to avoid issues)
config = configparser.ConfigParser(interpolation=None)
if os.path.exists(ini_path):
    config.read(ini_path)
    debug_mode = config.getboolean("Debug", "debug", fallback=False)  # ✅ Set before logging
else:
    ctypes.windll.user32.MessageBoxW(0, f"launcher.ini not found at {ini_path}", "Launcher Error", 0x10)
    sys.exit(1)  # ✅ Exit before anything else if ini is missing

# Function to print and log debug messages
def debug_print(message):
    """Prints debug messages only if debug mode is enabled and logs to a file."""
    global debug_mode  

    if not debug_mode:  # ✅ Don't print or log if debug is disabled
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)

    try:
        if os.path.exists(log_file) and os.path.getsize(log_file) > LOG_MAX_SIZE:
            archive_name = log_file.replace(".log", f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
            shutil.move(log_file, archive_name)
            print(f"Log file rotated: {archive_name}")

        with open(log_file, "a", encoding="utf-8") as log:
            log.write(log_message + "\n")

    except Exception as e:
        print(f"[Logging Error] {str(e)}")  # Only prints if debug mode is enabled

# Test logging behavior
debug_print(f"Found launcher.ini at {ini_path}")


# Function to show a Windows message box
def show_message_box(title, message):
    ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)  # 0x10 = MB_ICONERROR

# Function to log errors and show a GUI message box
def handle_error(message):
    """Logs an error and shows a GUI message box"""
    debug_print(f"[ERROR] {message}")
    show_message_box("Launcher Error", message)
    sys.exit(1)

# Function to rotate log file if it exceeds size limit
def rotate_log():
    """Rotates log file if it exceeds size limit"""
    if os.path.exists(log_file) and os.path.getsize(log_file) > LOG_MAX_SIZE:
        archive_name = log_file.replace(".log", f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        shutil.move(log_file, archive_name)
        debug_print(f"Log file archived as: {archive_name}")

# Function to check if the script is running as admin
def is_admin():
    return ctypes.windll.shell32.IsUserAnAdmin() != 0

# Function to relaunch the script as admin
def relaunch_as_adminOLD():
    """ Relaunch the script with admin privileges """
    debug_print("Relaunching script as admin...")
    #subprocess.run(["powershell", "-Command", f"Start-Process '{sys.executable}' -ArgumentList '{sys.argv[0]}' -Verb RunAs"])
    subprocess.run(["powershell", "-Command", f"Start-Process '{sys.executable}' -ArgumentList '\"{sys.argv[0]}\"' -Verb RunAs"])
    sys.exit(0)

def relaunch_as_admin():
    """ Relaunch the script with admin privileges while preserving arguments """
    debug_print("Relaunching script as admin...")

    # Prepare the argument list, preserving all original arguments
    args = " ".join([f'"{arg}"' for arg in sys.argv])

    # Relaunch using PowerShell to request elevation
    subprocess.run([
        "powershell", 
        "-Command", 
        f"Start-Process '{sys.executable}' -ArgumentList '{args}' -Verb RunAs"
    ], shell=True)

    sys.exit(0)


# Read ini file (disable interpolation to avoid issues)
config = configparser.ConfigParser(interpolation=None)
if os.path.exists(ini_path):
    config.read(ini_path)
    debug_mode = config.getboolean("Debug", "debug", fallback=False)
    debug_print(f"Found launcher.ini at {ini_path}")
else:
    handle_error(f"launcher.ini not found at {ini_path}")

# Get values from launcher.ini
program_exe = os.path.join(script_dir, "App", config.get("Launch", "ProgramExecutable", fallback=""))
run_as_admin = config.get("Launch", "runasadmin", fallback="normal").lower()

debug_print(f"ProgramExecutable: {program_exe}")
debug_print(f"runasadmin: {run_as_admin}")

# Prevent infinite relaunch loop by checking if ini exists first
if run_as_admin == "force" and os.path.exists(ini_path):
    if not is_admin():
        relaunch_as_admin()

# Ensure the executable exists
if not os.path.exists(program_exe):
    handle_error(f"Executable not found at {program_exe}")

# Function to show splash screen
def show_splash():
    """Displays a splash screen centered on the screen for 3 seconds."""
    if os.path.exists(splash_path):
        debug_print("Showing splash screen...")

        app = QApplication(sys.argv)  # Must be in the main thread
        pixmap = QPixmap(splash_path)
        
        splash = QSplashScreen(pixmap, Qt.WindowType.FramelessWindowHint)
        splash.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.WindowStaysOnTopHint)
        splash.show()

        # Center the splash screen
        screen = app.primaryScreen().geometry()
        splash.move((screen.width() - splash.width()) // 2, (screen.height() - splash.height()) // 2)

        # Keep splash for 3 seconds before quitting
        QTimer.singleShot(3000, app.quit)
        app.exec()

        debug_print("Splash screen closed.")

# Function to import registry files
def import_registry_files():
    """Scans the Data\Reg directory and imports any .reg files found."""
    reg_dir = os.path.join(script_dir, "Data", "Reg")

    if not os.path.exists(reg_dir):
        debug_print(f"Registry directory not found: {reg_dir}")
        return

    reg_files = [f for f in os.listdir(reg_dir) if f.endswith(".reg")]

    if not reg_files:
        debug_print("No registry files found to import.")
        return

    debug_print(f"Importing {len(reg_files)} registry file(s)...")

    for reg_file in reg_files:
        reg_path = os.path.join(reg_dir, reg_file)
        debug_print(f"Importing registry file: {reg_file}")

        try:
            result = subprocess.run(["reg", "import", reg_path], capture_output=True, text=True, shell=True)

            if result.returncode == 0:
                debug_print(f"Successfully imported: {reg_file}")
            else:
                debug_print(f"Failed to import: {reg_file} - {result.stderr.strip()}")

        except Exception as e:
            debug_print(f"Exception while importing {reg_file}: {str(e)}")

    debug_print("Registry import process completed.")

def prepare_previous_registry_data():
    """Moves existing .reg files to the PreviousData directory before exporting new registry data."""
    reg_dir = os.path.join(script_dir, "Data", "Reg")
    previous_data_dir = os.path.join(reg_dir, "PreviousData")

    # Ensure PreviousData directory exists
    os.makedirs(previous_data_dir, exist_ok=True)

    # Remove old files in PreviousData
    for file in os.listdir(previous_data_dir):
        if file.endswith(".reg"):
            old_file_path = os.path.join(previous_data_dir, file)
            try:
                os.remove(old_file_path)
                debug_print(f"Deleted old backup registry file: {file}")
            except Exception as e:
                debug_print(f"Error deleting old backup registry file {file}: {str(e)}")

    # Move existing .reg files to PreviousData before exporting new ones
    for file in os.listdir(reg_dir):
        if file.endswith(".reg"):
            old_path = os.path.join(reg_dir, file)
            new_path = os.path.join(previous_data_dir, file)

            try:
                os.rename(old_path, new_path)
                debug_print(f"Moved {file} to PreviousData")
            except Exception as e:
                debug_print(f"Error moving {file} to PreviousData: {str(e)}")

def cleanup_registry_keys():
    """Exports and then deletes registry keys specified in [RegCleanup] from launcher.ini."""
    debug_print("Starting registry cleanup process...")

    if not config.has_section("RegCleanup"):
        debug_print("No registry cleanup keys defined. Skipping cleanup.")
        return

    reg_keys = {key: value for key, value in config["RegCleanup"].items()}
    reg_dir = os.path.join(script_dir, "Data", "Reg")
    os.makedirs(reg_dir, exist_ok=True)

    # Move existing registry files to PreviousData before exporting new ones, but only if needed
    if reg_keys:
        prepare_previous_registry_data()

    for reg_filename, reg_key in reg_keys.items():
        reg_path = os.path.join(reg_dir, f"{reg_filename}.reg")

        debug_print(f"Exporting registry key: {reg_key} to {reg_path}")

        try:
            subprocess.run(f'reg export "{reg_key}" "{reg_path}" /y', capture_output=True, text=True, shell=True)
            subprocess.run(f'reg delete "{reg_key}" /f', capture_output=True, text=True, shell=True)
            debug_print(f"Successfully cleaned up registry key: {reg_key}")

        except Exception as e:
            debug_print(f"Exception during registry cleanup for {reg_key}: {str(e)}")

    debug_print("Registry cleanup process completed.")


def merge_data():
    """Copies files from Data\Files to their respective Windows locations as defined in [DataFiles] of launcher.ini, ignoring PreviousData."""
    if not config.has_section("DataFiles"):
        debug_print("[ERROR] No [DataFiles] section found in launcher.ini. Skipping file merge.")
        return

    debug_print(f"Found [DataFiles] section with {len(config['DataFiles'])} entries.")

    for key, mapping in config["DataFiles"].items():
        try:
            src, dest = mapping.split("|")  # Split the defined source & destination
            src_path = os.path.join(script_dir, src)
            dest_path = os.path.expandvars(dest)  # Expand environment variables

            debug_print(f"Processing entry {key}: {src_path} -> {dest_path}")

            # Ignore PreviousData directory
            if "PreviousData" in os.path.normpath(src_path).split(os.sep):
                debug_print(f"Skipping PreviousData directory: {src_path}")
                continue

            if not os.path.exists(src_path):
                debug_print(f"[WARNING] Skipping missing source file: {src_path}")
                continue

            os.makedirs(os.path.dirname(dest_path), exist_ok=True)  # Ensure target dir exists
            shutil.copy2(src_path, dest_path)
            debug_print(f"[SUCCESS] Copied {src_path} -> {dest_path}")

        except ValueError:
            debug_print(f"[ERROR] Invalid format in [DataFiles] for key: {key}. Expected 'source|destination'.")
        except Exception as e:
            debug_print(f"[ERROR] Error copying {src} to {dest}: {str(e)}")

    debug_print("[INFO] File merge process completed.")

def save_data():
    """Copies files from Windows locations back to Data\Files as defined in [DataFiles] of launcher.ini."""
    files_dir = os.path.join(script_dir, "Data", "Files")
    previous_data_dir = os.path.join(files_dir, "PreviousData")

    # Ensure PreviousData directory exists
    os.makedirs(previous_data_dir, exist_ok=True)

    if not config.has_section("DataFiles"):
        debug_print("No DataFiles section found in launcher.ini. Skipping file saving.")
        return

    for key, mapping in config["DataFiles"].items():
        try:
            src, dest = mapping.split("|")  # Reverse the source/destination
            src_path = os.path.expandvars(dest)  # Now, source is the system path
            dest_path = os.path.join(script_dir, src)

            if not os.path.exists(src_path):
                debug_print(f"Skipping missing system file: {src_path}")
                continue

            os.makedirs(os.path.dirname(dest_path), exist_ok=True)  # Ensure target dir exists

            # Move existing files to PreviousData before copying
            if os.path.exists(dest_path):
                backup_path = os.path.join(previous_data_dir, os.path.basename(dest_path))
                if os.path.exists(backup_path):
                    backup_path = f"{backup_path}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.move(dest_path, backup_path)
                debug_print(f"Backed up old file: {dest_path} -> {backup_path}")

            shutil.copy2(src_path, dest_path)
            debug_print(f"Saved {src_path} -> {dest_path}")

        except Exception as e:
            debug_print(f"Error saving {src} from {dest}: {str(e)}")

    debug_print("File saving process completed.")


def cleanup_files():
    """Deletes files and directories specified in [DataCleanup] from launcher.ini."""
    debug_print("Starting file cleanup process...")

    if not config.has_section("DataCleanup"):
        debug_print("No file cleanup entries defined. Skipping cleanup.")
        return

    cleanup_paths = [value for key, value in config["DataCleanup"].items()]

    for path in cleanup_paths:
        resolved_path = os.path.expandvars(path)  # Resolve environment variables

        if not os.path.exists(resolved_path):
            debug_print(f"[WARNING] Path does not exist: {resolved_path}")
            continue

        if os.path.isfile(resolved_path):
            # If it's a file, delete it
            try:
                os.remove(resolved_path)
                debug_print(f"Deleted file: {resolved_path}")
            except Exception as e:
                debug_print(f"Error deleting file {resolved_path}: {str(e)}")

        elif os.path.isdir(resolved_path):
            # If it's a directory, delete it and its contents
            try:
                shutil.rmtree(resolved_path)
                debug_print(f"Deleted directory: {resolved_path}")
            except Exception as e:
                debug_print(f"Error deleting directory {resolved_path}: {str(e)}")

        else:
            debug_print(f"Skipping missing or unknown path: {resolved_path}")

    debug_print("File cleanup process completed.")


# Function to run the program
def run_program():
    """Runs the target program and waits for it to exit"""
    debug_print("Importing Registry Keys...")
    import_registry_files()

    #debug_print("Capturing file snapshot...")
    #global file_snapshot
    #file_snapshot = capture_file_snapshot()

    debug_print("Merging data...")
    merge_data()

    debug_print(f"Launching: {program_exe}")
    process = subprocess.Popen(program_exe, cwd=os.path.dirname(program_exe))
    debug_print(f"{program_exe} is now running...")

    process.wait()
    debug_print(f"{program_exe} has exited.")

    # Perform registry cleanup
    cleanup_registry_keys()

    # Save new data back to Data\Files
    save_data()

# Run the launcher
show_splash()
run_program()
cleanup_files()

debug_print("Launcher exiting.")
