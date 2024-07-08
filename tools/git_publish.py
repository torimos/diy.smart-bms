import subprocess
import shutil
import os
import datetime
DIST_DIR = "dist"
RELEASE_DIR = "release"
RELEASE_FILE_NAME = "release.tar.gz"
VERSION_FILE = "version"

def run_command(command):
    """Run a shell command and return the output."""
    result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise Exception(f"Command failed: {command}\nError: {result.stderr}")
    return result.stdout.strip()

def add_all_changes():
    """Add all changed files to the git staging area."""
    run_command("git add .")

def commit_changes(message):
    """Commit changes with the provided commit message."""
    run_command(f"git commit -m \"{message}\"")

def create_tag(version):
    """Create a git tag with the specified version."""
    run_command(f"git tag -a {version} -m \"Release {version}\"")

def push_changes():
    """Push commits and tags to the remote repository."""
    run_command("git push")
    run_command("git push --tags")

def create_release(version, binary_path):
    """Create a release on GitHub and attach the release binary."""
    # Adjust the following GitHub CLI command to match your repository and binary path
    run_command(f"gh release create {version} {binary_path} -t {version} -n \"Release {version}\"")

# Function to read the current version, increment it, and save the new version
def get_next_version(version_file):
    if os.path.exists(version_file):
        with open(version_file, "r") as file:
            version = file.read().strip()
        major, minor = map(int, version.split('.'))
        minor += 1
    else:
        major, minor = 0, 1
    
    next_version = f"{major}.{minor}"
    
    with open(version_file, "w") as file:
        file.write(next_version)
    return f"v{next_version}"
    

# Get the current date and next version
next_version = get_next_version(VERSION_FILE)
#current_date = datetime.datetime.now().strftime("%Y%m%d")
#released_file_name = f"smartbms_{current_date}_v{next_version}.tar.gz"

# Ensure the release binary exists
release_binary_path = os.path.join(RELEASE_DIR, RELEASE_FILE_NAME)
if not os.path.exists(release_binary_path):
    raise FileNotFoundError(f"Release binary not found: {release_binary_path}")

# Add, commit, tag, and push changes
add_all_changes()
commit_changes(f"Published new version {next_version}")
#create_tag(next_version)
push_changes()
create_release(next_version, release_binary_path)
