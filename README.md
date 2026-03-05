# NUB — The Personal Version Vault

NUB is a lightweight, local-first version control system designed for simplicity and speed. It keeps your project history safe without the complexity of traditional tools.

## Why NUB?
- **Zero Config:** Get started with `nub start` in seconds.
- **Local-First:** All snapshots ("snaps") are stored on your machine in the hidden `.vcs` folder.
- **Clean Concepts:** No staging area (index) — if it's in the folder, it's in the snap (unless blinded).
- **Time Travel:** Move back and forth in time using "flows" and "back" commands.

## Installation

To install NUB and make the `nub` command available globally:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/veda-de-coder/NUB.git
   cd NUB
   ```

2. **Install via pip:**
   ```bash
   pip install .
   ```
   *Note: On Windows, this will automatically install `windows-curses` for the interactive graph.*

## Deployment & Updates

To update NUB to the latest version or a specific release:

1. **Pull the latest changes:**
   ```bash
   git pull origin master
   ```

2. **Re-install:**
   ```bash
   pip install . --upgrade
   ```

## Getting Started

1. **Initialize a Repo:**
   ```bash
   nub start
   ```

2. **Set Your Identity:**
   ```bash
   nub auth --name "Your Name" --email you@example.com
   ```

3. **Take a Snapshot:**
   ```bash
   nub snap -m "Initial commit"
   ```

4. **View History:**
   ```bash
   nub past
   ```

## Vocabulary & Commands

| NUB Command | Description | Source File |
|-------------|-------------|-------------|
| `start`     | Initialize a new vault | `init.py` |
| `auth`      | Sign in with your name/email | `config.py` |
| `snap`      | Take a permanent snapshot | `commit.py` |
| `past`      | View timeline of snaps | `commit.py` |
| `now`       | Check current flow and status | `refs.py` |
| `flow`      | Manage work branches | `refs.py` |
| `back`      | Revert to a previous state | `rollback.py` |
| `map`       | See project structure | `tree.py` |
| `blind`     | Ignore files/folders | `tree.py` |
| `sight`     | Reveal ignored files | `tree.py` |
| `shift`     | Compare past vs now | `cli.py` |
| `peek`      | Quickly read a file | `cli.py` |
| `universe`  | List all NUB repos on this PC | `utils.py` |

## Safety Rules
1. **Append-Only:** History is never deleted. Even when you go "back," the old snaps remain in the vault.
2. **Surgical Rollback:** `nub back` only touches tracked files. Your untracked work stays safe.
3. **Identity Signatures:** Every snap is signed with your name, email, and a unique Hash Key.

## Running Tests
To ensure everything is working correctly:
```bash
python run_tests.py
python integration_test.py
```
