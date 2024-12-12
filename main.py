import os
import json
import hashlib
import time
from simple_vcs import SimpleVCS

# Constants for repository structure and files
REPO_DIR = ".repo"  # Main repository directory
COMMITS_DIR = os.path.join(REPO_DIR, "commits")  # Directory to store commits
BRANCHES_FILE = os.path.join(REPO_DIR, "branches.json")  # Tracks branches
INDEX_FILE = os.path.join(REPO_DIR, "index.json")  # Tracks staged files
HEAD_FILE = os.path.join(REPO_DIR, "HEAD")  # Tracks current branch

# Repository path
REPO_PATH = "my_repo"

# Initialize the SimpleVCS system
vcs = SimpleVCS(REPO_PATH)

if __name__ == "__main__":
    import argparse



#vcs = SimpleVCS(".")

# Set up command-line argument parsing
import argparse

# Main parser
parser = argparse.ArgumentParser(description="Mini Source Control System")
subparsers = parser.add_subparsers(dest="command", required=True, help="Main commands")

# Init command
subparsers.add_parser("init", help="Initialize a repository")

# Add command
add_parser = subparsers.add_parser("add", help="Add files to the repository")
add_parser.add_argument("--file", required=True, help="File to add")

# Commit command
commit_parser = subparsers.add_parser("commit", help="Commit changes to the repository")
commit_parser.add_argument("--message", required=True, help="Commit message")

# History command
subparsers.add_parser("history", help="View commit history")

# Branch management
branch_parser = subparsers.add_parser("branch", help="Branch management commands")
branch_subparsers = branch_parser.add_subparsers(dest="branch_command", required=True)

# Create branch
create_branch_parser = branch_subparsers.add_parser("create", help="Create a new branch")
create_branch_parser.add_argument("--name", required=True, help="Name of the new branch")

# List branches
branch_subparsers.add_parser("list", help="List all branches")

# Switch branch
switch_branch_parser = branch_subparsers.add_parser("switch", help="Switch to a branch")
switch_branch_parser.add_argument("--name", required=True, help="Branch name to switch to")

# Clone command
clone_parser = subparsers.add_parser("clone", help="Clone the repository")
clone_parser.add_argument("target_path", help="Target path for cloning")

# Add ignore patterns
add_ignore_parser = subparsers.add_parser("add_ignore", help="Add ignore patterns")
add_ignore_parser.add_argument("patterns", nargs="+", help="Patterns to ignore")

# List files
subparsers.add_parser("list_files", help="List files in the repository")

# Diff command
diff_parser = subparsers.add_parser("diff", help="Show differences between branches")
diff_parser.add_argument("branch1", help="First branch for comparison")
diff_parser.add_argument("branch2", help="Second branch for comparison")

# Merge command
merge_parser = subparsers.add_parser("merge", help="Merge branches")
merge_parser.add_argument("source_branch", help="Source branch to merge from")
merge_parser.add_argument("target_branch", help="Target branch to merge into")

# Parse arguments
args = parser.parse_args()
print(args)

# Parse arguments
args = parser.parse_args()

# Route commands to their respective functions
if args.command == "init":
    vcs.init()
elif args.command == "add":
    if args.file:
        vcs.add(args.file)
    else:
        print("Specify a file to add using --file.")
elif args.command == "commit":
    if args.message:
        vcs.commit(args.message)
    else:
        print("Specify a commit message using --message.")
elif args.command == "history":
    vcs.history()
elif args.command == "branch":
    if args.branch_command == "create":
        vcs.create_branch(args.name)
    elif args.branch_command == "list":
        vcs.list_branches()
    elif args.branch_command == "switch":
        vcs.switch_branch(args.name)
elif args.command == "clone":
    vcs.clone(args.target_path)
elif args.command == "add_ignore":
    vcs.add_ignore(args.patterns)
elif args.command == "list_files":
    for file in vcs.list_files():
        print(file)
elif args.command == "diff":
    vcs.diff(args.branch1, args.branch2)
elif args.command == "merge":
    vcs.merge(args.source_branch, args.target_branch)
else:
    parser.print_help()
