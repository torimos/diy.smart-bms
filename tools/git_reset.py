import subprocess

# GitHub repository details
OWNER = 'torimos'
REPO = 'diy.smart-bms'

# Run a shell command and return the output
def run_command(command):
    result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise Exception(f"Command failed: {command}\nError: {result.stderr}")
    return result.stdout.strip()

run_command("rm -rf .git")
run_command("git init --initial-branch=main")
run_command("git init -b main")
run_command("git add .")
run_command("git commit -m initial")
run_command(f"git remote add origin git@github.com:{OWNER}/{REPO}.git")
run_command("git push -u --force origin main")
print("Git repo has been reinitialized")

r = run_command("gh release list 2>/dev/null | awk '{print $1}'")
for num in r.splitlines():
    run_command(f"gh release delete {num} -y")
    print(f"✓ Deleted release {num}")

r = run_command(f"gh api repos/{OWNER}/{REPO}/tags | jq -r '.[].name'")
for num in r.splitlines():
    run_command(f"gh api repos/{OWNER}/{REPO}/git/refs/tags/{num} -X DELETE")
    print(f"✓ Deleted tag {num}")

print("All releases and tags have been deleted.")