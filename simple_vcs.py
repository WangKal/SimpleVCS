import os
import json
import hashlib
import time
import shutil
import logging
from pathlib import Path
from unittest.mock import patch

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
        self.commits_dir.mkdir()
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

        with self.index_file.open("r+") as index:
            staging_area = json.load(index)
            staging_area[file_path] = full_path.stat().st_mtime
            index.seek(0)
            json.dump(staging_area, index)
            index.truncate()

        print(f"Added '{file_path}' to staging area.")

    def commit(self, message):
        """
        Commit the staged changes to the repository.

        Args:
            message (str): Commit message describing the changes.
        """
        if not self.repo_dir.exists():
            print("Repository not initialized. Run 'init' first.")
            return

        with self.index_file.open("r") as index:
            staging_area = json.load(index)

        if not staging_area:
            print("No changes to commit.")
            return

        commit_hash = hashlib.sha1(f"{time.time()}".encode()).hexdigest()

        commit_data = {
            "message": message,
            "files": staging_area,
            "timestamp": time.time(),
        }

        with (self.commits_dir / commit_hash).open("w") as commit_file:
            json.dump(commit_data, commit_file)

        with self.head_file.open("r") as head_file:
            current_branch = head_file.read().strip()

        with self.branches_file.open("r+") as branches_file:
            branches = json.load(branches_file)
            branches[current_branch] = commit_hash
            branches_file.seek(0)
            json.dump(branches, branches_file)
            branches_file.truncate()

        with self.index_file.open("w") as index:
            json.dump({}, index)

        print(f"Committed changes with hash {commit_hash}. Message: '{message}'")

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

        # Here you could load the files from the commit into the working directory
        # For simplicity, this function doesn't handle file restoration, but you can implement it.
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

    def diff(self, branch1, branch2):
        branch1_path = self.repo_path / branch1
        branch2_path = self.repo_path / branch2

        if not branch1_path.exists() or not branch2_path.exists():
            print("One or both branches do not exist.")
            return

        branch1_files = {str(file.relative_to(branch1_path)) for file in branch1_path.rglob('*') if file.is_file()}
        branch2_files = {str(file.relative_to(branch2_path)) for file in branch2_path.rglob('*') if file.is_file()}

        added = branch2_files - branch1_files
        removed = branch1_files - branch2_files
        modified = {file for file in branch1_files & branch2_files
                    if (branch1_path / file).read_bytes() != (branch2_path / file).read_bytes()}

        print("Files added:", added)
        print("Files modified:", modified)

    def merge(self, source_branch, target_branch):
        source_path = self.repo_path / source_branch
        target_path = self.repo_path / target_branch

        if not source_path.exists() or not target_path.exists():
            print("One or both branches do not exist.")
            return

        conflicts = []

        for file in source_path.rglob('*'):
            if file.is_file():
                rel_path = file.relative_to(source_path)
                target_file = target_path / rel_path

                if target_file.exists() and file.read_bytes() != target_file.read_bytes():
                    conflicts.append(str(rel_path))  # Convert Path to string
                else:
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file, target_file)

        if conflicts:
            print(f"Conflicts detected: {conflicts}")  # Log conflicts as a string list
        else:
            logger.info("Merge completed without conflicts.")
