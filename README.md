# Distributed Source Control System

This is a Python-based distributed version control system inspired by Git. It allows users to initialize repositories, stage and commit files, create and manage branches, perform merges, and clone repositories, all through a command-line interface (CLI).

---

## Features

- **Repository Initialization**: Create a new repository with a `.repo` directory.
- **File Staging**: Add files to the staging area.
- **Committing**: Save staged changes to the repository.
- **Branch Management**: Create, list, and switch between branches.
- **Merging**: Merge branches, with conflict detection.
- **Difference Checking**: View differences between branches.
- **Cloning**: Clone repositories to a new directory.
- **Ignoring Files**: Define files or directories to exclude from version control.

---

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/distributed-vcs.git
   ```

2. Navigate to the project directory:
   ```bash
   cd distributed-vcs
   ```

3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

The tool is operated through the command-line interface (CLI). Below are the available commands and their usage.

### **1. Initialize a Repository**
Create a new repository in the current directory:
```bash
python main.py init
```

### **2. Add Files to the Staging Area**
Add files or directories to the staging area:
```bash
python main.py add <file_or_directory>
```
Example:
```bash
python main.py add file1.txt
```

### **3. Commit Changes**
Commit staged changes with a message:
```bash
python main.py commit -m "Your commit message"
```

### **4. View Commit History**
List all commits:
```bash
python main.py log
```

### **5. Create a New Branch**
Create a new branch:
```bash
python main.py branch <branch_name>
```

### **6. Switch Between Branches**
Switch to another branch:
```bash
python main.py checkout <branch_name>
```

### **7. Merge Branches**
Merge a branch into the current branch:
```bash
python main.py merge <branch_name>
```

### **8. View Differences Between Branches**
Check differences between branches:
```bash
python main.py diff <branch1> <branch2>
```

### **9. Clone a Repository**
Clone a repository to a new directory:
```bash
python main.py clone <target_path>
```

### **10. Define Ignored Files**
Specify files or directories to ignore by adding them to a `.ignore` file in the repository root.

---

## Example Workflow

1. Initialize a repository:
   ```bash
   python main.py init
   ```

2. Add a file to the staging area:
   ```bash
   python main.py add file1.txt
   ```

3. Commit the changes:
   ```bash
   python main.py commit -m "Initial commit"
   ```

4. Create a new branch and switch to it:
   ```bash
   python main.py branch feature
   python main.py checkout feature
   ```

5. Make changes, add, and commit:
   ```bash
   python main.py add file2.txt
   python main.py commit -m "Add file2.txt"
   ```

6. Merge the feature branch into the main branch:
   ```bash
   python main.py checkout main
   python main.py merge feature
   ```

---

## Error Handling

- **Conflicts**: If a merge conflict occurs, it will be reported. Resolve conflicts manually before proceeding.
- **Invalid Commands**: Ensure all commands and arguments are used correctly. Run `python main.py help` for assistance.

---

## Contributing

Contributions are welcome! Please fork the repository and create a pull request with your changes.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

