"""Git repository management for Bootstrap documentation."""

import logging
import os
from pathlib import Path
from typing import Optional

try:
    from git import Repo
    from git.exc import GitCommandError, InvalidGitRepositoryError
except ImportError:
    raise ImportError("GitPython is required. Install with: pip install GitPython")

logger = logging.getLogger(__name__)

# Bootstrap repository configuration
BOOTSTRAP_REPO_URL = "https://github.com/twbs/bootstrap.git"
DOCS_PATH = "site/content/docs"
DEFAULT_BRANCH = "main"


class GitManager:
    """Manages the Bootstrap Git repository."""

    def __init__(self, repo_path: str, repo_url: str = BOOTSTRAP_REPO_URL):
        """
        Initialize the Git manager.

        Args:
            repo_path: Local path where the repository should be cloned
            repo_url: URL of the Bootstrap Git repository
        """
        self.repo_path = Path(repo_path)
        self.repo_url = repo_url
        self.docs_path = self.repo_path / DOCS_PATH
        self.repo: Optional[Repo] = None

    def clone_or_update_repo(self) -> bool:
        """
        Clone the repository if it doesn't exist, or update it if it does.

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.repo_path.exists() and (self.repo_path / ".git").exists():
                logger.info(f"Repository exists at {self.repo_path}, updating...")
                return self._update_repo()
            else:
                logger.info(f"Cloning Bootstrap repository to {self.repo_path}...")
                return self._clone_repo()
        except Exception as e:
            logger.error(f"Error managing repository: {e}")
            return False

    def _clone_repo(self) -> bool:
        """
        Clone the Bootstrap repository.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.repo_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Cloning from {self.repo_url}...")
            self.repo = Repo.clone_from(
                self.repo_url,
                self.repo_path,
                branch=DEFAULT_BRANCH,
                depth=1  # Shallow clone for faster downloads
            )
            logger.info("Repository cloned successfully")
            return True
        except GitCommandError as e:
            logger.error(f"Git command error during clone: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during clone: {e}")
            return False

    def _update_repo(self) -> bool:
        """
        Update the existing repository.

        Returns:
            True if successful, False otherwise
        """
        try:
            self.repo = Repo(self.repo_path)
            origin = self.repo.remotes.origin
            logger.info("Fetching updates from remote...")
            origin.fetch()

            # Reset to the latest version
            logger.info(f"Resetting to origin/{DEFAULT_BRANCH}...")
            self.repo.git.reset("--hard", f"origin/{DEFAULT_BRANCH}")
            logger.info("Repository updated successfully")
            return True
        except InvalidGitRepositoryError:
            logger.error(f"Invalid Git repository at {self.repo_path}")
            return False
        except GitCommandError as e:
            logger.error(f"Git command error during update: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during update: {e}")
            return False

    def is_repo_ready(self) -> bool:
        """
        Check if the repository is cloned and the docs path exists.

        Returns:
            True if ready, False otherwise
        """
        repo_exists = self.repo_path.exists() and (self.repo_path / ".git").exists()
        docs_exists = self.docs_path.exists()

        if not repo_exists:
            logger.warning(f"Repository not found at {self.repo_path}")
        if not docs_exists:
            logger.warning(f"Documentation path not found at {self.docs_path}")

        return repo_exists and docs_exists

    def get_docs_path(self) -> Path:
        """
        Get the path to the documentation directory.

        Returns:
            Path to the docs directory
        """
        return self.docs_path

    def get_commit_info(self) -> dict:
        """
        Get information about the current commit.

        Returns:
            Dictionary with commit information
        """
        try:
            if not self.repo:
                self.repo = Repo(self.repo_path)

            commit = self.repo.head.commit
            return {
                "sha": commit.hexsha[:7],
                "message": commit.message.strip(),
                "author": str(commit.author),
                "date": commit.committed_datetime.isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting commit info: {e}")
            return {}


def clone_or_update_bootstrap(data_dir: str) -> tuple[bool, Path]:
    """
    Convenience function to clone or update the Bootstrap repository.

    Args:
        data_dir: Directory where data should be stored

    Returns:
        Tuple of (success: bool, docs_path: Path)
    """
    repo_path = os.path.join(data_dir, "bootstrap-repo")
    manager = GitManager(repo_path)

    success = manager.clone_or_update_repo()
    if success and manager.is_repo_ready():
        return True, manager.get_docs_path()

    return False, Path()
