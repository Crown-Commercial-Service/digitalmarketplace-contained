from environment import Environment


class AppsProvision:

    def __init__(self, env: Environment, clear_venv_and_node_modules: bool):
        self.env = env
        self.clear_venv_and_node_modules = clear_venv_and_node_modules

    def provision_all_apps(self):
        for app_name, app_configuration in self.env.configuration()['apps'].items():
            self._provision_app(app_name, app_configuration)

    def _provision_app(self, app_name: str, app_configuration: dict):
        bootstrap_command: str = app_configuration.get('bootstrap')

        Environment.display_status_banner(f"Preparing app: {app_name}")

        app_code_directory: str = f"{self.env.apps_code_directory}/{app_name}"

        if self.clear_venv_and_node_modules:
            self.env.run_safe_shell_command("rm -rf venv", app_code_directory)
            self.env.run_safe_shell_command("rm -rf node_modules/", app_code_directory)

        # TODO change the following line so that we don't run a command coming from config.yml
        # to minimise risk of shell/command injection
        self.env.run_safe_shell_command(bootstrap_command, app_code_directory)

        Environment.display_status_banner(f"Launching app: {app_name}")

        # We need to launch the next command in the background (by appending &) as it runs "forever",
        # otherwise the setup process would be blocked by it
        self.env.run_safe_shell_command("invoke run-app &", app_code_directory)