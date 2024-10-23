import subprocess
from pathlib import Path
from typing import Any

from cleo.application import Application
from cleo.helpers import argument
from poetry.console.commands.env_command import EnvCommand
from poetry.plugins.application_plugin import ApplicationPlugin
from tomlkit.items import Table

SECTION_DESCRIPTOR: str = "poetry-clone-local"


class ClonePackages(EnvCommand):
    """
    Command to clone repositories from a specified group in pyproject.toml to a target directory.
    """

    name: str = "clone-packages"
    description: str = "Clone repositories from a specified group in pyproject.toml to a target directory."

    arguments = [
        argument(
            "path",
            "The target directory where the repositories will be cloned.",
            multiple=False,
            optional=False,
        ),
    ]

    def handle(self) -> Any:
        """
        Handles the main logic of the command: reading pyproject.toml, filtering repositories, and cloning them.
        """

        pyproject_data: dict[str, Any] = self.poetry.pyproject.data
        clone_base_dir = Path(self.argument("path"))

        try:
            repositories: Table = pyproject_data["tool"][SECTION_DESCRIPTOR]
        except KeyError:
            self.line_error(
                f"\nError: Could not find any git dependencies under '[tool.{SECTION_DESCRIPTOR}]' "
                f"within your pyproject.toml. Please ensure that the descriptor name is correct.",
                style="error",
            )
            return 1

        unique_repos = self.filter_unique_repositories(repositories)
        if not unique_repos:
            return 0

        cloned_repos = self.clone_repositories(unique_repos, clone_base_dir)

        self.line(
            f"\nFinished: Cloned {len(cloned_repos)} of {len(unique_repos)} repositories successfully.",
            style="info",
        )
        return 0

    def filter_unique_repositories(self, repositories: Table) -> dict[Any, Any]:
        """
        Filters unique repositories based on git link and returns them.
        """

        unique_data = {}
        seen_git_links = set()

        for key, value in repositories.items():
            if not isinstance(value, dict) or not value.get("git"):
                self.line_error(
                    f"\nError: Unable to locate a git dependency for {key} {value} under "
                    f"[tool.{SECTION_DESCRIPTOR}]. Ensure that you have used a git-compatible dependency.",
                    style="error",
                )
                return {}

            git_link = value["git"]
            new_key = git_link.split("/")[-1].replace(".git", "")

            if git_link not in seen_git_links:
                seen_git_links.add(git_link)
                unique_data[new_key] = value

        return unique_data

    def clone_repositories(self, unique_data: dict[str, dict[str, str]], clone_base_dir: Path) -> list[dict[Any, Any]]:
        """
        Clones the repositories from the unique data set.
        """

        cloned_repos = []
        for repo_name, repo_info in unique_data.items():
            if self.clone_repo(repo_name, repo_info, clone_base_dir):
                cloned_repos.append(repo_info)
        return cloned_repos

    def clone_repo(self, name: str, repo_info: dict[str, str], clone_base_dir: Path) -> bool:
        """
        Clones a Git repository into a specified directory.
        """

        clone_dir = clone_base_dir / name

        if clone_dir.exists():  # Check if the clone directory already exists
            self.line_error(
                f"\nError: The directory '{clone_dir}' already exists. Skipping clone operation.",
                style="error",
            )
            return False

        clone_dir.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
        clone_cmd = ["git", "clone", repo_info["git"], str(clone_dir)]  # Construct the git clone command

        # Add branch or tag if specified
        if branch_or_tag := repo_info.get("branch") or repo_info.get("tag"):
            clone_cmd.extend(["-b", branch_or_tag])

        try:
            self.line(f"\nExec: {' '.join(clone_cmd)}", style="info")  # Log the git clone command
            subprocess.run(clone_cmd, check=True)  # Execute the git clone command
        except subprocess.CalledProcessError as e:
            self.line_error(f"\nError: Failed to clone repository '{name}'. {e}", style="error")
            raise RuntimeError(
                f"Cloning of repository '{name}' failed. Please check the repository URL and your network connection."
            )
        return True


class ClonePlugin(ApplicationPlugin):
    """
    Plugin to activate the ClonePackages command within the application.
    """

    def activate(self, application: Application, *args: Any, **kwargs: Any) -> None:
        application.add(ClonePackages())
