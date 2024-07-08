import os
import shutil
import subprocess
import tarfile
import datetime

SRC_DIRS = ["src"]
DIST_DIR = "dist"
FROZEN_DIR = "frozen"
RELEASE_DIR = "release"
RELEASE_FILE_NAME = "release.tar.gz"
MPY_CROSS_PATH = "/usr/bin/mpy-cross"  # Update this path to where mpy-cross is located
VERSION_FILE = "version"

# Function to clean up a directory
def clean_directory(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                os.unlink(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            try:
                shutil.rmtree(dir_path)
            except Exception as e:
                print(f'Failed to delete {dir_path}. Reason: {e}')

# Clean up the DIST_DIR before starting
if os.path.exists(DIST_DIR):
    clean_directory(DIST_DIR)
else:
    os.makedirs(DIST_DIR)

# Clean up the DIST_DIR before starting
if os.path.exists(RELEASE_DIR):
    clean_directory(RELEASE_DIR)
else:
    os.makedirs(RELEASE_DIR)

def compile_and_move(src_dir):
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py"):
                base_name = os.path.splitext(file)[0]

                file_path = os.path.join(root, file)

                # Skip main.py and boot.py, and copy them directly
                if base_name in ["main", "boot"]:
                    shutil.copy(file_path, DIST_DIR)
                else:
                    mpy_file = os.path.join(root, base_name + ".mpy")

                    # Compile the .py file to .mpy
                    subprocess.run([MPY_CROSS_PATH, file_path], check=True)

                    # Create the corresponding directory structure in the frozen directory
                    relative_path = os.path.relpath(root, src_dir)
                    target_dir = os.path.join(FROZEN_DIR, relative_path)
                    os.makedirs(target_dir, exist_ok=True)

                    # Move the resulting .mpy file to the corresponding directory in the frozen folder
                    shutil.move(mpy_file, target_dir)
            else:
                shutil.copy(os.path.join(root, file), DIST_DIR)
                

# Function to copy files while preserving the directory structure
def copy_files(src_dir, dist_dir):
    for root, _, files in os.walk(src_dir):
        for file in files:
            src_file_path = os.path.join(root, file)
            relative_path = os.path.relpath(root, src_dir)
            target_dir = os.path.join(dist_dir, relative_path)
            os.makedirs(target_dir, exist_ok=True)
            shutil.copy(src_file_path, target_dir)

# Copy files from source to output dist folder
for src_dir in SRC_DIRS:
    copy_files(src_dir, DIST_DIR)

# Function to compile .py files to .mpy in the frozen directory
def compile_frozen_files(dist_dir):
    frozen_dir = os.path.join(dist_dir, FROZEN_DIR)
    for root, _, files in os.walk(frozen_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                subprocess.run([MPY_CROSS_PATH, file_path], check=True)
                # Remove the original .py file after compiling
                os.remove(file_path)

# Compile .py files in the frozen directory if it exists
if os.path.exists(os.path.join(DIST_DIR, FROZEN_DIR)):
    compile_frozen_files(DIST_DIR)

# Function to create a tar.gz archive
def create_tar_gz(source_dir, output_filename):
    with tarfile.open(output_filename, "w:gz") as tar:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                tar.add(file_path, arcname=arcname)

# Create the tar.gz archive from the dist directory with the desired filename format
create_tar_gz(DIST_DIR, os.path.join(RELEASE_DIR, RELEASE_FILE_NAME))

print("Build is done")
print()
