from unittest import TestCase
from unittest.mock import patch, PropertyMock

from hpc_app.resources.ssh import SSHResource

from flask_restful import reqparse

PATCH_MODULE = "hpc_app.resources.ssh"


class SSHTests(TestCase):
    @patch(
        f"{PATCH_MODULE}.LOCAL_DEV_TESTING_ENABLED",
        new_callable=PropertyMock(return_value=True),
    )
    @patch(
        f"{PATCH_MODULE}.LOCAL_DEV_TESTING_JUMP_USER",
        new_callable=PropertyMock(return_value="YOUR_ENS_SJ1_USERNAME"),
    )
    @patch(
        f"{PATCH_MODULE}.LOCAL_DEV_TESTING_JUMP_PASS",
        new_callable=PropertyMock(return_value="YOUR_ENS_SJ1_PASSWORD"),
    )
    @patch(f"{PATCH_MODULE}.CommonResource")
    def test_load_response_over_ssh(self, mock_common, *_):
        mock_common.return_value.ssh_username = "YOUR_WEB_USERNAME"
        mock_common.return_value.ssh_password = "YOUR_WEB_PASSWORD"

        ssh = SSHResource()
        ssh.args = reqparse.Argument(name="")
        ssh.args.hostname = "HOST_YOU_WANT_TO_TEST"
        ssh.args.command = "COMMAND_YOU_WANT_TO_ISSUE"
        ssh.args.max_cache_age = 0
        ssh.init_paths()
        ssh.normalise_command()
        ssh.load_response_over_ssh()
