import unittest
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch
from simple_vcs import SimpleVCS

@patch('builtins.print')  # Mock print
@patch('logging.error')  # Mock logger.error

class TestSimpleVCS(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.vcs = SimpleVCS(self.test_dir)

    def tearDown(self):
        # Remove the temporary directory after the test
        shutil.rmtree(self.test_dir)

    def test_init(self):
        """Test repository initialization."""
        self.vcs.init()
        
        repo_dir = Path(self.test_dir) / '.repo'
        
        # Ensure that the .repo directory exists
        self.assertTrue(repo_dir.exists())
        
        # Ensure the necessary files and directories exist
        self.assertTrue((repo_dir / 'commits').exists())
        self.assertTrue((repo_dir / 'branches.json').exists())
        self.assertTrue((repo_dir / 'index.json').exists())
        self.assertTrue((repo_dir / 'HEAD').exists())


    def test_add_file(self):
        """Test adding a file to the staging area."""
        self.vcs.init()
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("Hello, World!")
        
        self.vcs.add("test.txt")
        
        with open(self.vcs.index_file, "r") as f:
            staging_area = json.load(f)
        self.assertIn("test.txt", staging_area)

    def test_commit(self):
        """Test committing changes."""
        self.vcs.init()
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("Hello, World!")
        
        self.vcs.add("test.txt")
        self.vcs.commit("Initial commit")
        
        # Check if commit was added
        with open(self.vcs.branches_file, "r") as f:
            branches = json.load(f)
        
        current_branch = Path(self.test_dir) / ".repo" / "HEAD"
        with open(current_branch, "r") as f:
            branch_name = f.read().strip()
        
        commit_hash = branches.get(branch_name)
        self.assertIsNotNone(commit_hash)
        self.assertTrue((self.vcs.commits_dir / commit_hash).exists())

    def test_create_branch(self):
        """Test creating a new branch."""
        self.vcs.init()
        self.vcs.create_branch("feature")
        
        with open(self.vcs.branches_file, "r") as f:
            branches = json.load(f)
        
        self.assertIn("feature", branches)

    def test_switch_branch(self):
        """Test switching between branches."""
        self.vcs.init()
        self.vcs.create_branch("feature")
        
        self.vcs.switch_branch("feature")
        
        with open(self.vcs.head_file, "r") as f:
            current_branch = f.read().strip()
        
        self.assertEqual(current_branch, "feature")

    def test_list_branches(self):
        """Test listing branches."""
        self.vcs.init()  # Initialize the repository
        self.vcs.create_branch("feature")  # Create a 'feature' branch
        
        # Capture the logs generated during the call to list_branches()
        with self.assertLogs('SimpleVCS', level='INFO') as log:
            self.vcs.list_branches()  # Call the method that lists branches
        
        # Assert that the main branch and feature branch are logged
        self.assertIn("main", log.output[0])  # Verify 'main' branch is listed

    def test_status(self):
        """Test the status of the repository."""
        self.vcs.init()
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("Hello, World!")

        self.vcs.add("test.txt")

        with self.assertLogs('SimpleVCS', level='INFO') as log:
            self.vcs.status()

        # Check for the 'Changes not staged for commit' message
        self.assertIn("Changes not staged for commit:", log.output[0])

        # Optionally check for 'Changes staged for commit' as well
        self.assertIn("Changes staged for commit:", log.output[1])  # Adjusted to match order if needed


    def test_clone(self):
        """Test cloning a repository."""
        # Prepare the test repository
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("Hello, World!")

        # Ensure the repository is initialized
        self.vcs.init()  # Ensure `init` is called to create `.repo`
        self.vcs.add("test.txt")
        self.vcs.commit("Initial commit")

        # Create a temporary directory for the clone
        clone_dir = Path(tempfile.mkdtemp())
        repo_dir = Path(self.test_dir) / ".repo"
        assert repo_dir.exists(), f"Repository directory '{repo_dir}' does not exist."

        branches_file = repo_dir / "branches.json"
        assert branches_file.exists(), f"Branches file '{branches_file}' is missing in the source repository."

        try:
            # Ensure the directory is clean
            if clone_dir.exists():
                shutil.rmtree(clone_dir)

            # Clone the repository
            self.vcs.clone(clone_dir)

            # Verify the cloned repository
            clone_vcs = SimpleVCS(clone_dir)

            # Check if branches file exists in the cloned repository
            branches_file = clone_vcs.repo_dir / "branches.json"
            self.assertTrue(branches_file.exists(), "Branches file missing in cloned repository.")
            

            # Verify branch content
            with open(branches_file, "r") as f:
                branches = json.load(f)
            self.assertIn("main", branches, "Branch 'main' not found in cloned repository.")
            
        finally:
            with open(branches_file, "r") as f:
                branches = json.load(f)
        
            self.assertIn("main", branches)

    def test_get_ignored_files(self):
        """Test get_ignored_files function."""
        # Create a sample .gitignore file
        self.vcs.ignore_file.write_text("# Comment\n*.log\n*.tmp\n")
        
        ignored_files = self.vcs.get_ignored_files()
        
        self.assertIn("*.log", ignored_files)
        self.assertIn("*.tmp", ignored_files)
        self.assertNotIn("# Comment", ignored_files)

    def test_list_files(self):
        """Test list_files function."""
        # Simulate files in the repository
        repo_file = self.vcs.repo_path / "file1.txt"
        repo_file.touch()
        
        ignored_file = self.vcs.repo_path / "file2.log"
        ignored_file.touch()

        # Add ignored patterns to the .gitignore
        self.vcs.ignore_file.write_text("*.log\n")
        
        # Mock the get_ignored_files method to simulate ignoring files
        with patch.object(self.vcs, 'get_ignored_files', return_value=["*.log"]):
            files = list(self.vcs.list_files())

        self.assertIn("file1.txt", files)
        self.assertNotIn("file2.log", files)

    @patch("builtins.print")
    def test_diff(self, mock_print):
        """Test diff function for comparing two branches."""
        branch1_path = self.vcs.repo_path / "branch1"
        branch2_path = self.vcs.repo_path / "branch2"
        
        # Create directories for the branches
        branch1_path.mkdir(parents=True, exist_ok=True)
        branch2_path.mkdir(parents=True, exist_ok=True)
        
        # Create some files in branch1 and branch2
        (branch1_path / "file1.txt").write_text("Hello from branch 1")
        (branch2_path / "file1.txt").write_text("Hello from branch 2")
        (branch2_path / "file2.txt").write_text("New file in branch 2")
        
        # Call diff function
        self.vcs.diff("branch1", "branch2")
        
        # Check that print was called with the correct arguments
        mock_print.assert_any_call("Files added:", {"file2.txt"})
        mock_print.assert_any_call("Files modified:", {"file1.txt"})


    def test_merge(self):
        """Test merge function for merging branches."""
        source_branch = self.vcs.repo_path / "branch1"
        target_branch = self.vcs.repo_path / "branch2"
        
        # Create directories for the branches
        source_branch.mkdir(parents=True, exist_ok=True)
        target_branch.mkdir(parents=True, exist_ok=True)
        
        # Create some files in source_branch and target_branch
        (source_branch / "file1.txt").write_text("Hello from source branch")
        (target_branch / "file1.txt").write_text("Hello from target branch")
        
        # Mock print function to capture output
        with patch("builtins.print") as mock_print:
            self.vcs.merge("branch1", "branch2")
            
            # Check that conflicts were detected
            print(mock_print.call_args_list) 
            mock_print.assert_any_call("Conflicts detected:", {"file1.txt"})

            # Simulate no conflict after copying content from source to target
            (target_branch / "file1.txt").write_text("Hello from source branch")
            self.vcs.merge("branch1", "branch2")
            
            # Check that merge completed without conflicts
            mock_print.assert_any_call("Merge completed without conflicts.")


if __name__ == '__main__':
    unittest.main()

