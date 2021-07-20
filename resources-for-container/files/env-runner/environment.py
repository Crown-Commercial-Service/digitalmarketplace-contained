import os
import subprocess
import yaml
from colored import fg, bg, attr  # type: ignore

from utils import display_status_banner, exit_with_error_message
from repos_updater import ReposUpdater


class Environment:

    POSTGRES_USER = "postgres"

    def __init__(self, dry_run: bool):
        self.dry_run = dry_run
        self._construct_common_directory_paths()

    def configuration(self) -> dict:
        try:
            with open(f"{self.runner_directory}/config/config.yml", 'r') as stream:
                try:
                    configuration: dict = yaml.safe_load(stream)
                    return configuration
                except yaml.YAMLError as yaml_exception:
                    exit_with_error_message(yaml_exception)
        except FileNotFoundError as file_exception:
            exit_with_error_message(file_exception)

    def prepare_scripts(self) -> None:
        display_status_banner("Preparing scripts")
        reposUpdater = ReposUpdater(self)
        reposUpdater.update_local_scripts_repo()
        self.run_safe_shell_command(
            "invoke requirements-dev", f"{self.local_repos_directory}/{reposUpdater.SCRIPTS_REPO_NAME}")

    def run_safe_shell_command(self, command: str, working_directory: str = None) -> None:
        if working_directory is None:
            working_directory = os.getcwd()
        if not os.path.isdir(working_directory):
            raise OSError(f"Working directory {working_directory} not found; unable to run shell command.")
        print(f"{fg('white')}{bg('green')} > Running command: {command} {attr(0)}")
        if not self.dry_run:
            # TODO command should be a list to prevent command injection attacks
            try:
                subprocess.run(command, cwd=working_directory, shell=True, check=True)
            except Exception as exception:
                exit_with_error_message(exception)

    def _construct_common_directory_paths(self) -> None:
        this_script_directory = os.path.abspath(os.path.dirname(__file__))
        self.mount_directory: str = f"{this_script_directory}/../../mount"
        self.local_repos_directory: str = f"{self.mount_directory}/local-repos"
        self.runner_directory: str = this_script_directory
        # TODO raise error if directories don't exist
