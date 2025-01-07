import os
import json
import hashlib
import time
import shutil
import logging
from pathlib import Path
from unittest.mock import patch
from difflib import unified_diff

# Set up a logger for SimpleVCS
logger = logging.getLogger("SimpleVCS")
logger.setLevel(logging.INFO)  # Set the level to INFO
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)

class SimpleVCS:
    def __init__(self, repo_path):
        self.repo_path = Path(repo_path)
        self.repo_dir = self.repo_path / ".repo"
        self.remote_dir = self.repo_path / ".remote"
        self.commits_dir = self.repo_dir / "commits"
        self.branches_file = self.repo_dir / "branches.json"
        self.index_file = self.repo_dir / "index.json"
        self.head_file = self.repo_dir / "HEAD"
        self.ignore_file = self.repo_path / ".ignore"

   
    
    def init(self):
        """
        Initialize the repository by creating the directory structure and files.
        """
        if self.repo_dir.exists():
            print("Repository already initialized.")
            return

        self.repo_dir.mkdir(parents=True)
        self.remote_dir.mkdir(parents=True)
        self.commits_dir.mkdir()
        self.main_folder = self.commits_dir / "main"
        self.main_folder.mkdir()
        self.branches_file.write_text(json.dumps({"main": None}))
        self.index_file.write_text(json.dumps({}))
        self.head_file.write_text("main")
        
    
        print("Repository initialized.")

    def add(self, file_path):
        """
        Add a file to the staging area.

        Args:
            file_path (str): Path to the file to be added.
        """
        if not self.repo_dir.exists():
            print("Repository not initialized. Run 'init' first.")
            return

        full_path = self.repo_path / file_path
        if not full_path.exists():
            print(f"File '{file_path}' does not exist.")
            return

        staging_area = self.repo_dir / "staging"
        os.makedirs(staging_area, exist_ok=True)
    
        shutil.copy(full_path, staging_area)
        print(f"File '{file_path}' added to staging area.")
        


    def commit(self, message):
        """
        Commit the staged changes to the repository.

        Args:
            message (str): Commit message describing the changes.
        """
        if not self.repo_dir.exists():
            print("Repository not initialized. Run 'init' first.")
            return
        
        with self.head_file.open("r") as head_file:
            current_branch = head_file.read().strip()

        branch_dir = self.repo_dir / "commits" / current_branch
        staging_area = self.repo_dir / "staging"

        if not os.listdir(staging_area):
            print("No changes to commit.")
            return

        commit_id = len(os.listdir(branch_dir))
        commit_dir = os.path.join(branch_dir, f"commit_{commit_id}")
        os.makedirs(commit_dir)

        for file_name in os.listdir(staging_area):
            shutil.move(os.path.join(staging_area, file_name), commit_dir)

        with open(os.path.join(commit_dir, "message.txt"), "w") as f:
            f.write(message)

        print(f"Committed changes to {current_branch} with message: {message}")



    # Push changes to the remote repository
    def push(self):
        with self.head_file.open("r") as head_file:
            current_branch = head_file.read().strip()

        local_branch = self.repo_dir / "commits" / current_branch
        remote_branch = self.remote_dir / "commits" / current_branch

        if not os.path.exists(local_branch):
            print(f"No commits to push for branch '{current_branch}'.")
            return

        if not os.path.exists(remote_branch):
            os.makedirs(remote_branch)

        for commit in os.listdir(local_branch):
            local_commit = os.path.join(local_branch, commit)
            remote_commit = os.path.join(remote_branch, commit)
            if not os.path.exists(remote_commit):
                shutil.copytree(local_commit, remote_commit)

        print(f"Pushed changes from branch '{current_branch}' to remote.")


    def history(self):
        """
        Display the commit history of the current branch.
        """
        if not self.repo_dir.exists():
            print("Repository not initialized. Run 'init' first.")
            return

        with self.head_file.open("r") as head_file:
            current_branch = head_file.read().strip()

        with self.branches_file.open("r") as branches_file:
            branches = json.load(branches_file)

        commit_hash = branches.get(current_branch)
        if not commit_hash:
            print(f"No commits in branch '{current_branch}'.")
            return

        print(f"Commit history for branch '{current_branch}':")

        while commit_hash:
            commit_path = self.commits_dir / commit_hash
            if not commit_path.exists():
                break

            with commit_path.open("r") as commit_file:
                commit_data = json.load(commit_file)
                timestamp = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(commit_data["timestamp"])
                )
                print(f"- {commit_hash[:7]} | {timestamp} | {commit_data['message']}")

            commit_hash = commit_data.get("parent")

    def create_branch(self, branch_name):
        """
        Create a new branch starting from the current commit of the active branch.
        """
        if not self.repo_dir.exists():
            print("Repository not initialized. Run 'init' first.")
            return

        with self.head_file.open("r") as head_file:
            current_branch = head_file.read().strip()

        with self.branches_file.open("r+") as branches_file:
            branches = json.load(branches_file)
            if branch_name in branches:
                print(f"Branch '{branch_name}' already exists.")
                return

            branches[branch_name] = branches[current_branch]
            branches_file.seek(0)
            json.dump(branches, branches_file)
            branches_file.truncate()

            
            new_branch_path = self.repo_dir / "commits" / branch_name

            os.makedirs(new_branch_path)

            print(f"Branch '{branch_name}' created.")

    def list_branches(self):
        """
        List all branches and highlight the active branch.
        """
        if not self.repo_dir.exists():
            print("Repository not initialized. Run 'init' first.")
            return

        with self.head_file.open("r") as head_file:
            current_branch = head_file.read().strip()

        with self.branches_file.open("r") as branches_file:
            branches = json.load(branches_file)

        print("Branches:")
        for branch, commit in branches.items():
            marker = "*" if branch == current_branch else " "
            commit_display = commit[:7] if commit else "None"
            logger.info(f"{marker} {branch} ({commit_display})")


    def switch_branch(self, branch_name):
        """
        Switch to a different branch.
        """
        if not self.repo_dir.exists():
            print("Repository not initialized. Run 'init' first.")
            return

        with self.branches_file.open("r") as branches_file:
            branches = json.load(branches_file)
            if branch_name not in branches:
                print(f"Error: Branch '{branch_name}' does not exist.")
                return

        with self.head_file.open("w") as head_file:
            head_file.write(branch_name)

        print(f"Switched to branch '{branch_name}'.")

    def switch_workspace(self, branch_name):
        """
        Switch the workspace to match the given branch.
        This includes clearing the staging area and updating the workspace with the files from the branch's commit.
        """
        if not self.repo_dir.exists():
            print("Repository not initialized. Run 'init' first.")
            return

        if not branch_name:
            print("Error: Branch name is required.")
            return

        with self.branches_file.open("r") as branches_file:
            branches = json.load(branches_file)

        if branch_name not in branches:
            print(f"Error: Branch '{branch_name}' does not exist.")
            return

        # Get the commit hash for the selected branch
        commit_hash = branches[branch_name]

        # Clear the staging area (index) when switching branches
        with self.index_file.open("w") as index:
            json.dump({}, index)

        print(f"Workspace switched to branch '{branch_name}'. Staging area cleared.")

    def clone(self, target_path):
        """Clone the repository to the target path."""
        target = Path(target_path)
        if target.exists():
            raise FileExistsError(f"Target path '{target}' already exists. Aborting.")

        # Create the target directory
        target.mkdir(parents=True)

        # Ensure .repo directory exists
        if not self.repo_dir.exists() or not (self.repo_dir / "branches.json").exists():
            raise FileNotFoundError(f"Source repository is missing required files.'{self.repo_dir}'")

        # Copy the `.repo` directory to the target
        shutil.copytree(self.repo_dir, target / ".repo")

        # Copy all non-hidden files and directories to the target
        for item in self.repo_path.iterdir():
            if item.name == ".repo" or item.name.startswith("."):
                continue
            target_item = target / item.name
            if item.is_dir():
                shutil.copytree(item, target_item)
            else:
                shutil.copy2(item, target_item)

        print(f"Repository cloned successfully to {target}")

    def add_ignore(self, patterns):
        with self.ignore_file.open('a') as f:
            f.writelines(f"{pattern}\n" for pattern in patterns)
        print("Ignore patterns added.")


    def status(self):
        """
        Display the status of the working directory compared to the staging area.
        """
        if not self.repo_dir.exists():
            logger.warning("Repository not initialized. Run 'init' first.")
            return

        ignored = self.get_ignored_files()

        with self.index_file.open("r") as index:
            staging_area = json.load(index)

        working_dir_files = {}
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if ".repo" in root or any(Path(file).match(pattern) for pattern in ignored):
                    continue
                full_path = Path(root) / file
                working_dir_files[str(full_path.relative_to(self.repo_path))] = full_path.stat().st_mtime

        logger.info("Changes not staged for commit:")
        for file, mtime in working_dir_files.items():
            if file not in staging_area or staging_area[file] != mtime:
                logger.info(f"  modified: {file}")

        logger.info("\nChanges staged for commit:")
        for file in staging_area.keys():
            if file not in working_dir_files:
                logger.info(f"  deleted: {file}")

    def get_ignored_files(self):
        ignored = []
        if self.ignore_file.exists():
            with self.ignore_file.open() as f:
                ignored = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return ignored

    def list_files(self):
        """List all files in the repository that are not ignored."""
        ignored = self.get_ignored_files()  # Assuming this function retrieves the ignored patterns
        
        # Iterate over files in the repository path
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                # Check if the file matches any ignored pattern
                if not any(Path(file).match(pattern) for pattern in ignored):
                    # Log the file that will be yielded
                    logger.info(f"File: {file}")
                    yield file

    def get_files_in_directory(self,directory):
        """Recursively get all files in a directory and its subdirectories."""
        files = []
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                files.append(os.path.relpath(os.path.join(root, filename), directory))
        return files

    def diff(self,branch1, branch2):
        """
        Compares the contents of all files in two branches (folders) and prints the differences.
        """
        branch1 = self.repo_dir / "commits" / branch1
        branch2 = self.repo_dir / "commits" / branch2

        if not os.path.isdir(branch1):
            print(f"Error: Branch 1 not found: {branch1}")
            return
        if not os.path.isdir(branch2):
            print(f"Error: Branch 2 not found: {branch2}")
            return

        try:
            # Get all files (including subdirectories) in both branches
            branch1_files = set(self.get_files_in_directory(branch1))
            branch2_files = set(self.get_files_in_directory(branch2))

            print(f"Files in Branch 1: {branch1_files}")
            print(f"Files in Branch 2: {branch2_files}")

            # Find common files, added files, and removed files
            common_files = branch1_files & branch2_files
            added_files = branch2_files - branch1_files
            removed_files = branch1_files - branch2_files

            print(f"Common files: {common_files}")
            print(f"Added files in Branch 2: {added_files}")
            print(f"Removed files from Branch 1: {removed_files}")

            # Compare common files
            for file in common_files:
                path1 = os.path.join(branch1, file)
                path2 = os.path.join(branch2, file)

                if os.path.isfile(path1) and os.path.isfile(path2):
                    with open(path1, 'r') as f1, open(path2, 'r') as f2:
                        content1 = f1.readlines()
                        content2 = f2.readlines()

                    file_diff = list(unified_diff(content1, content2, 
                                                  fromfile=f"Branch 1: {file}", 
                                                  tofile=f"Branch 2: {file}"))

                    if file_diff:
                        print(f"Differences in file: {file}")
                        print(''.join(file_diff))
                    else:
                        print(f"No differences in file: {file}")

            # Handle added files
            for file in added_files:
                print(f"File added in Branch 2: {file}")

            # Handle removed files
            for file in removed_files:
                print(f"File removed in Branch 1: {file}")

        except PermissionError as e:
            print(f"Permission denied: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")

    def merge(self, source_branch, target_branch):
        source_path = self.repo_dir / "commits" / source_branch
        target_path = self.repo_dir / "commits" /target_branch

        if not source_path.exists() or not target_path.exists():
            print("One or both branches do not exist.")
            return

        conflicts = []

        for file in source_path.rglob('*'):
            if file.is_file():
                rel_path = file.relative_to(source_path)
                target_file = target_path / rel_path
                file_name = os.path.basename(file)
                if target_file.exists() and file_name != "message.txt" and file.read_bytes() != target_file.read_bytes():
                    conflicts.append(file)  # Convert Path to string
                else:
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file, target_file)

        if conflicts:
            print(f"Conflicts detected: {conflicts}")  # Log conflicts as a string list
        else:
            logger.info("Merge completed without conflicts.")
