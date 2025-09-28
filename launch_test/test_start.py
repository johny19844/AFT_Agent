import os
import subprocess
import sys
import shutil

def is_executable_in_path(executable):
    """Check if an executable exists in PATH."""
    return shutil.which(executable) is not None

def clone_and_run_maven():
    repo_url = "https://github.com/johny19844/AFT.git"
    repo_dir = "AFT"

    # Check if git is available
    if not is_executable_in_path("git"):
        print("Error: 'git' is not found in your PATH. Please install Git and ensure it is available in your system PATH.")
        sys.exit(1)

    # Check if maven is available
    if not is_executable_in_path("mvn"):
        print("Error: 'mvn' (Maven) is not found in your PATH. Please install Maven and ensure it is available in your system PATH.")
        sys.exit(1)

    # Clone the repository if it does not exist
    if not os.path.exists(repo_dir):
        print(f"Cloning repository {repo_url}...")
        result = subprocess.run(["git", "clone", repo_url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print("Failed to clone repository:")
            print(result.stderr)
            sys.exit(1)
    else:
        print(f"Repository '{repo_dir}' already exists. Skipping clone.")

    # Run Maven build
    print("Running Maven build...")
    mvn_cmd = ["mvn", "test"]
    try:
        # On Windows, use shell=True to allow .bat/.cmd resolution
        shell_flag = os.name == "nt"
        result = subprocess.run(
            mvn_cmd,
            cwd=repo_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=shell_flag
        )
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure Maven is installed and 'mvn' is available in your PATH.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

    if result.returncode != 0:
        print("Maven build failed.")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)
    else:
        print("Maven build succeeded.")
        print(result.stdout)

if __name__ == "__main__":
    clone_and_run_maven()
