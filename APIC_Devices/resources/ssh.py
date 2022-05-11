import re
from datetime import datetime
from pathlib import Path

from flask_restful import reqparse
from flask_restful import Resource

from hpc_app.common.common import CommonResource
from hpc_app.common.no_setup_cisco_connect import NoSetupCiscoConnect

LOCAL_DEV_TESTING_ENABLED = False
LOCAL_DEV_TESTING_JUMP_HOST = "ens-sj1.cisco.com"
LOCAL_DEV_TESTING_JUMP_USER = "<add_your_test_username>"
LOCAL_DEV_TESTING_JUMP_PASS = "<add_your_test_password>"

CACHE_ROOT = Path("/tmp/ssh/")
NORMALISE_COMMAND_REGEX = re.compile("([&#$ |'\"\[\]\(\){}<>])")


class SSHResource(Resource):
    def __init__(self):
        self.args = None
        self.cache_file = None
        self.host_directory = None
        self.common = CommonResource()

    def get(self):
        """
        Issue a command on a device over ssh and return the response. If the
        command is found in the cache and the age of the cached command does
        not exceed max_cache_age then the cached response will be returned. A
        max_cache_age of 0 will ensure the cache is never used.
        {
            "hostname": "hostname.cisco.com",
            "commands": ["show version"],
            "max_cache_age": 0
        }
        """
        parser = reqparse.RequestParser(bundle_errors=True)
        parser.add_argument(
            "hostname",
            type=str,
            location="json",
            required=True,
            help="hostname is required",
        )
        parser.add_argument(
            "command",
            type=str,
            location="json",
            required=True,
            help="command is required",
        )
        parser.add_argument(
            "max_cache_age",
            type=int,
            location="json",
            required=True,
            help="max_cache_age is required",
        )
        self.args = parser.parse_args()
        return self.process(), 200

    @staticmethod
    def get_command_from_host(command, hostname, max_cache_age=0):
        """
        Entrypoint to load a command from a host from within the package in lieu
        over http
        Args:
            command (str): The command to be issued
            hostname (str): The host on which to issue the command
            max_cache_age (int): The maximum age for the cache to be considered
                                 fresh
        Returns:
            str: The response from the device
        """
        ssh = SSHResource()
        ssh.args = reqparse.Argument(name="")
        ssh.args.command = command
        ssh.args.hostname = hostname
        ssh.args.max_cache_age = max_cache_age
        return ssh.process()

    def process(self):
        """
        Process the host and command and return the response
        Returns:
            str: The response from the device
        """
        self.normalise_command()
        self.init_paths()
        return self.load_response_from_cache() or self.load_response_over_ssh()

    def init_paths(self):
        """
        Init the paths
        """
        self.host_directory = CACHE_ROOT / self.args.hostname
        self.cache_file = self.host_directory / self.args.normalised_command

    def load_response_from_cache(self):
        """
        Load a response from cache if it is available and if it hasn't exceeded
        the max cache age
        Returns:
            str|None: The previous cache or None if not found or aged out
        """
        if not self.cache_file.is_file():
            return

        data = self.cache_file.read_text().split("\n")

        if (
            datetime.now().timestamp()
            - datetime.fromtimestamp(float(data[0])).timestamp()
            > self.args.max_cache_age
        ):
            return

        return "\n".join(data[1:])

    def load_response_over_ssh(self):
        """
        Issue a command over SSH to the nominated device and return the response
        Returns:
            str: The response from the device
        """
        session = NoSetupCiscoConnect(
            hostname=self.args.hostname,
            username=self.common.webusername,
            password=self.common.webpassword,
        )

        if LOCAL_DEV_TESTING_ENABLED:
            session.login_with_jump_host(
                jump_host=LOCAL_DEV_TESTING_JUMP_HOST,
                jump_user=LOCAL_DEV_TESTING_JUMP_USER,
                jump_password=LOCAL_DEV_TESTING_JUMP_PASS,
            )
        else:
            session.login()

        response = session.run_cmd(self.args.command)

        session.logout()
        self.cache_response(response)
        return response

    def cache_response(self, response):
        """
        Cache a response from a device
        Args:
            response (str): The response from the device
        """
        self.host_directory.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(f"{datetime.now().timestamp()}\n{response}")

    def normalise_command(self):
        """
        Normalise a command so that it can be used for a filename
        """
        self.args.normalised_command = NORMALISE_COMMAND_REGEX.sub(
            "_", self.args.command
        )
