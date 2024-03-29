import os
from abc import ABC
from typing import List

import boto3  # type: ignore

from environment import Environment
from utils import display_status_banner


class BackendServices:

    def __init__(self, env: Environment):
        self.env = env

        self.services: List[BackendService] = [
            NginxBackendService(self.env),
            RedisBackendService(self.env),
            PostgresBackendService(self.env),
            ElasticsearchBackendService(self.env),
            LocalstackBackendService(self.env)
        ]

    def provision_services(self) -> None:
        for service in self.services:
            service.provision()

    def initialise_services(self) -> None:
        for service in self.services:
            service.initialise()


class BackendService(ABC):

    def __init__(self, env: Environment):
        self.env = env

    def configure(self) -> None:
        pass

    def launch(self) -> None:
        pass

    def initialise(self) -> None:
        pass

    def provision(self) -> None:
        display_status_banner("Starting backend service: " + self.__class__.__name__)
        self.configure()
        self.launch()


class NginxBackendService(BackendService):
    def configure(self) -> None:
        self.env.run_safe_shell_command(f"cp {self.env.runner_directory}/config/nginx.conf /etc/nginx/")

    def launch(self) -> None:
        self.env.run_safe_shell_command("/etc/init.d/nginx start")


class RedisBackendService(BackendService):
    def launch(self) -> None:
        self.env.run_safe_shell_command("/etc/init.d/redis-server start")


class PostgresBackendService(BackendService):
    def configure(self) -> None:
        self.env.run_safe_shell_command("sed -i 's/peer/trust/g' /etc/postgresql/11/main/pg_hba.conf")
        self.env.run_safe_shell_command("sed -i 's/md5/trust/g' /etc/postgresql/11/main/pg_hba.conf")

    def launch(self) -> None:
        self.env.run_safe_shell_command("pg_ctlcluster 11 main restart")

    def initialise(self) -> None:
        self.env.run_safe_shell_command(
            f'psql --user {self.env.POSTGRES_USER} --command "CREATE DATABASE digitalmarketplace;"')
        self.env.run_safe_shell_command(
            f'psql --user {self.env.POSTGRES_USER} --command "CREATE DATABASE digitalmarketplace_test;"')

        # The api app will try to log in into the db with the user of the current shell (that is, 'root') rather than
        # 'postgres'
        # There may be a workaround to that, however, given than this project is not meant to run on production,
        # it is probably just easier to create a new superuser role 'root'.
        # TODO try to avoid to create a new user - shall we run the api as the postgres user, rather than root?
        self.env.run_safe_shell_command(
            f'psql --user {self.env.POSTGRES_USER} --command "CREATE ROLE root WITH LOGIN SUPERUSER;"')


class ElasticsearchBackendService(BackendService):
    def launch(self) -> None:
        self.env.run_safe_shell_command("service elasticsearch start")


class LocalstackBackendService(BackendService):

    def launch(self) -> None:
        # This service is currently launched in another container - see README file
        pass

    def initialise(self) -> None:

        localstack_port: int = 4566

        # see https://github.com/Crown-Commercial-Service/digitalmarketplace-admin-frontend/blob/main/config.py#L113
        dev_bucket_name: str = "digitalmarketplace-dev-uploads"

        # see https://github.com/Crown-Commercial-Service/digitalmarketplace-runner/blob/main/config/settings.yml#L17
        os.environ["AWS_ACCESS_KEY_ID"] = "test"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "test"
        os.environ["DM_S3_ENDPOINT_PORT"] = str(localstack_port)

        s3_region = "eu-west-1"
        s3_endpoint_url = f"http://localstack:{localstack_port}"
        s3 = boto3.resource("s3", region_name=s3_region, endpoint_url=s3_endpoint_url)
        try:
            s3.create_bucket(
                Bucket=dev_bucket_name, CreateBucketConfiguration={"LocationConstraint": s3_region}
            )
        except s3.meta.client.exceptions.BucketAlreadyExists:
            pass
