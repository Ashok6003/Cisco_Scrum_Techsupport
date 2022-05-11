from unittest import TestCase
from unittest.mock import patch, Mock

with patch(f"hpc_app.common.log.setup_logger"):
    from hpc_app.resources.aci_tree import ACITreeResource
from hpc_app.common.data_structure import Tree
from requests.models import Response
import json


class Testapi(TestCase):
    @patch("hpc_app.resources.aci_tree.reqparse")
    @patch("hpc_app.resources.aci_tree.ACITreeResource.collect_info")
    @patch("hpc_app.resources.aci_tree.abort_with_message")
    @patch("hpc_app.resources.aci_tree.CommonResource.apic_login")
    def test_get(self, mock_apic_login, mock_awm, mock_collect_info, mock_reqparse):
        mock_parser = Mock()
        mock_parser.add_args.return_value = None
        mock_parser.parse_args.return_value = {"host": "host"}
        mock_reqparse.RequestParser.return_value = mock_parser
        with open("tests/sample_responses/aci_tree/response_json.json") as json_file:
            data = json.load(json_file)
        mock_collect_info.return_value = data, 200

        session = mock_apic_login("rcdn9-fab1-apic2.cisco.com", "username", "password")
        obj = ACITreeResource()
        obj.session = session
        obj.get()
        mock_awm.assert_called_with(
            "/aci_tree", {"hostname": "host"}, data, 200, obj.session
        )

    @patch("hpc_app.resources.aci_tree.PinPointHostResource.collect_info")
    @patch("hpc_app.resources.aci_tree.ACITreeResource.get_lldpadjep_output_from_api")
    @patch("hpc_app.resources.aci_tree.ACITreeResource.get_cdpadjep_output_from_api")
    @patch("hpc_app.resources.aci_tree.ACITreeResource.get_ethpm_phys_output_from_api")
    @patch("hpc_app.resources.aci_tree.ACITreeResource.get_node_id")
    @patch("hpc_app.resources.aci_tree.ACITreeResource.find_nodes_and_interfaces")
    @patch("hpc_app.resources.aci_tree.ACITreeResource.add_dcc_interface_stats")
    @patch("hpc_app.resources.aci_tree.CommonResource.apic_login")
    @patch("hpc_app.resources.aci_tree.CommonResource.webusername")
    @patch("hpc_app.resources.aci_tree.CommonResource.webpassword")
    @patch("hpc_app.resources.aci_tree.abort_with_message")
    def test_collect_info(
        self,
        mock_awm,
        mock_pass,
        mock_user,
        mock_apic_login,
        mock_adis,
        mock_fnai,
        mock_gni,
        mock_gepofa,
        mock_gcofa,
        mock_glofa,
        mock_pph_info,
    ):

        mock_pph_info.side_effect = [
            (("ACI", "rtp1-fab1-apic2.cisco.com", "64.101.6.4"), 200),
            (("Traditional", "gw", "ip"), 200),
        ]

        mock_gepofa.return_val = None
        mock_gcofa.return_val = None
        mock_glofa.return_val = None
        mock_gni.return_val = None

        with open("tests/sample_responses/aci_tree/response_json.json") as json_file:
            response_json = json.load(json_file)
        expected_output = response_json, 200

        mock_fnai.side_effect = [
            response_json["switch_to_ucs"],
            response_json["switch_to_spine"],
            response_json["spine_to_border"],
            response_json["border_to_dcc"],
        ]
        mock_adis.return_value = None

        obj = ACITreeResource()
        obj.apic = "rcdn9-fab1-apic2.cisco.com"
        mock_user.return_value = "username"
        mock_pass.return_value = "password"
        mock_apic_login.return_value = Mock()
        out = obj.collect_info("host")
        self.assertEqual((out, 200), (expected_output, 200))

        # Traditional  Case
        obj.collect_info("host")
        mock_awm.asser_called_with("Host {} is in Traditional".format("host"), 200)

    @patch("hpc_app.resources.aci_tree.CommonResource.apic_login")
    def test_get_lldpadjep_output_from_api(self, mock_apic_login):
        session = mock_apic_login("rcdn9-fab1-apic2.cisco.com", "username", "password")
        obj = ACITreeResource()
        obj.session = session
        the_response = Response()
        the_response.status_code = 200
        with open(
            "tests/sample_responses/aci_tree/lldpadjep_outputs/lldp_query_response.txt"
        ) as file:
            the_response._content = bytes(file.read(), "utf-8")

        obj.session.get.return_value = the_response
        out = obj.get_lldpadjep_output_from_api()

        with open(
            "tests/sample_responses/aci_tree/lldpadjep_outputs/get_lldpadjep_output_from_api.json"
        ) as json_file:
            expected_output = json.load(json_file)
        self.assertEqual(len(out), 410)
        self.assertEqual(expected_output, out)

    @patch("hpc_app.resources.aci_tree.CommonResource.apic_login")
    @patch("hpc_app.resources.aci_tree.abort_with_message")
    def test_get_lldpadjep_output_from_api_abort_case(self, mock_awm, mock_apic_login):
        session = mock_apic_login("rcdn9-fab1-apic2.cisco.com", "username", "password")
        obj = ACITreeResource()
        obj.session = session
        the_response = Response()
        the_response.status_code = 404

        obj.get_lldpadjep_output_from_api()
        mock_awm.assert_called_with(
            "/aci_tree",
            {"hostname": ""},
            "Error while getting lldpadjep info",
            404,
            obj.session,
        )

    def test_get_filtered_lldpadjep_output(self):
        obj = ACITreeResource()

        with open(
            "tests/sample_responses/aci_tree/lldpadjep_outputs/get_lldpadjep_output_from_api.json"
        ) as json_file:
            obj.lldp_output = json.load(json_file)

        with open(
            "tests/sample_responses/aci_tree/lldpadjep_outputs/get_filtered_lldpadjep_output.json"
        ) as json_file:
            expected_output = json.load(json_file)

        out = obj.get_filtered_lldpadjep_output(["3812", "3811"])

        for el in out:
            self.assertIn(el, expected_output)

    @patch("hpc_app.resources.aci_tree.CommonResource.apic_login")
    def test_get_ethpm_phys_output_from_api(self, mock_apic_login):
        session = mock_apic_login("rcdn9-fab1-apic2.cisco.com", "username", "password")
        obj = ACITreeResource()
        obj.session = session
        the_response = Response()
        the_response.status_code = 200
        with open(
            "tests/sample_responses/aci_tree/eth_phys_outputs/ethpmPhysIf_query_response.txt"
        ) as file:
            the_response._content = bytes(file.read(), "utf-8")
        obj.session.get.return_value = the_response
        expected_output = [
            {
                "rmonIfOut": {
                    "attributes": {
                        "broadcastPkts": "1128671",
                        "childAction": "",
                        "clearTs": "2019-02-05T12:05:49.000-06:00",
                        "discards": "0",
                        "dn": "topology/pod-1/node-1291/sys/phys-[eth1/5]/dbgIfIn",
                        "errors": "0",
                        "modTs": "never",
                        "multicastPkts": "925091",
                        "nUcastPkts": "2053762",
                        "octets": "64409428287130",
                        "status": "",
                        "ucastPkts": "66812926090",
                        "unknownProtos": "0",
                    }
                }
            }
        ]
        out = obj.get_ethpm_phys_output_from_api()
        self.assertEqual(out, expected_output)

    @patch("hpc_app.resources.aci_tree.CommonResource.apic_login")
    @patch("hpc_app.resources.aci_tree.abort_with_message")
    def test_get_ethpm_phys_output_from_api_abort_case(self, mock_awm, mock_apic_login):
        session = mock_apic_login("rcdn9-fab1-apic2.cisco.com", "username", "password")
        obj = ACITreeResource()
        obj.session = session
        the_response = Response()
        the_response.status_code = 404
        obj.session.get.return_value = the_response
        obj.get_ethpm_phys_output_from_api()
        mock_awm.assert_called_with(
            "/aci_tree",
            {"hostname": ""},
            "Error while getting port channel info",
            404,
            obj.session,
        )

    @patch("hpc_app.resources.aci_tree.CommonResource.apic_login")
    def test_get_cdpadjep_output_from_api(self, mock_apic_login):
        session = mock_apic_login("rcdn9-fab1-apic2.cisco.com", "username", "password")
        obj = ACITreeResource()
        obj.session = session
        the_response = Response()
        the_response.status_code = 200
        with open(
            "tests/sample_responses/aci_tree/cdpadjep_outputs/cdp_query_response.txt"
        ) as file:
            the_response._content = bytes(file.read(), "utf-8")

        obj.session.get.return_value = the_response
        out = obj.get_cdpadjep_output_from_api()

        with open(
            "tests/sample_responses/aci_tree/cdpadjep_outputs/get_cdpadjep_output_from_api.json"
        ) as json_file:
            expected_output = json.load(json_file)
        self.assertEqual(len(out), 410)
        self.assertEqual(expected_output, out)

    @patch("hpc_app.resources.aci_tree.CommonResource.apic_login")
    @patch("hpc_app.resources.aci_tree.abort_with_message")
    def test_get_cdpadjep_output_from_api_abort_case(self, mock_awm, mock_apic_login):
        session = mock_apic_login("rcdn9-fab1-apic2.cisco.com", "username", "password")
        obj = ACITreeResource()
        obj.session = session
        the_response = Response()
        the_response.status_code = 404

        obj.get_cdpadjep_output_from_api()
        mock_awm.assert_called_with(
            "/aci_tree",
            {"hostname": ""},
            "Error while getting cdpAdjEp info",
            404,
            obj.session,
        )

    def test_get_filtered_cdpadjep_output(self):
        obj = ACITreeResource()

        with open(
            "tests/sample_responses/aci_tree/cdpadjep_outputs/get_cdpadjep_output_from_api.json"
        ) as json_file:
            obj.cdp_output = json.load(json_file)

        with open(
            "tests/sample_responses/aci_tree/cdpadjep_outputs/get_filtered_cdpadjep_output.json"
        ) as json_file:
            expected_output = json.load(json_file)

        out = obj.get_filtered_cdpadjep_output(["dcc"])

        for el in out:
            self.assertIn(el, expected_output)

    @patch("hpc_app.resources.aci_tree.CommonResource.apic_login")
    @patch("hpc_app.resources.aci_tree.abort_with_message")
    def test_get_node_id(self, mock_awm, mock_apic_login):
        session = mock_apic_login("rcdn9-fab1-apic2.cisco.com", "username", "password")
        aci_graph_obj = ACITreeResource()
        aci_graph_obj.session = session
        the_response = Response()
        the_response.status_code = 200
        with open("tests/sample_responses/aci_tree/fvIp_query_response.txt") as file:
            the_response._content = bytes(file.read(), "utf-8")

        the_response_fail = Response()
        the_response_fail.status_code = 404
        the_response_fail._content = b'{"status":"error"}'

        aci_graph_obj.session.get.side_effect = [the_response, the_response_fail]
        expected_output = aci_graph_obj.get_node_id()
        self.assertEqual(expected_output, {"1182", "1181"})

        # abort case
        aci_graph_obj.get_node_id()
        mock_awm.assert_called_with(
            "/aci_tree",
            {"hostname": ""},
            "Error in api call to get fvIp info in get_node_id function : 404",
            404,
            aci_graph_obj.session,
        )

    @patch("hpc_app.resources.aci_tree.CommonResource.apic_login")
    def test_get_interface_errors_discards_input(self, mock_apic_login):
        session = mock_apic_login("rcdn9-fab1-apic2.cisco.com", "username", "password")
        obj = ACITreeResource()
        obj.session = session
        the_response = Response()
        the_response.status_code = 200
        with open(
            "tests/sample_responses/aci_tree/get_interface_errors_discards_input_case_response.txt"
        ) as file:
            the_response._content = bytes(file.read(), "utf-8")

        obj.session.get.return_value = the_response
        errors, discards = obj.get_interface_errors_discards(
            "node-1291", "Eth1/5", "input"
        )
        self.assertEqual(errors, "0")
        self.assertEqual(discards, "0")

    @patch("hpc_app.resources.aci_tree.CommonResource.apic_login")
    @patch("hpc_app.resources.aci_tree.abort_with_message")
    def test_get_interface_errors_discards_output(self, mock_awm, mock_apic_login):
        session = mock_apic_login("rcdn9-fab1-apic2.cisco.com", "username", "password")
        obj = ACITreeResource()
        obj.session = session
        the_response = Response()
        the_response.status_code = 200
        with open(
            "tests/sample_responses/aci_tree/get_interface_errors_discards_output_case_response.txt"
        ) as file:
            the_response._content = bytes(file.read(), "utf-8")

        obj.session.get.return_value = the_response
        errors, discards = obj.get_interface_errors_discards(
            "node-1291", "Eth1/5", "output"
        )
        self.assertEqual(errors, "0")
        self.assertEqual(discards, "0")

        # improper interface case
        errors, discards = obj.get_interface_errors_discards(
            "node-1291", "wrong interface", "output"
        )
        self.assertEqual([errors, discards], [None, None])

        # abort case
        obj.get_interface_errors_discards("node-1291", "Eth1/5", "key")
        mock_awm.assert_called_with(
            "/aci_tree",
            {"hostname": ""},
            "key should be input or output only",
            404,
            obj.session,
        )

    @patch("hpc_app.resources.aci_tree.CommonResource.apic_login")
    def test_get_interface_errors_discards_utilOut(self, mock_apic_login):
        session = mock_apic_login("rcdn9-fab1-apic2.cisco.com", "username", "password")
        obj = ACITreeResource()
        obj.session = session
        the_response = Response()
        the_response.status_code = 200
        with open("tests/sample_responses/aci_tree/get_interface_util_out.txt") as file:
            the_response._content = bytes(file.read(), "utf-8")

        obj.session.get.return_value = the_response
        util_out = obj.get_interface_errors_discards("node-1291", "Eth1/5", "utilOut")
        self.assertEqual(util_out, 1.0)

    @patch("hpc_app.resources.aci_tree.CommonResource.apic_login")
    def test_get_interface_errors_discards_utilIn(self, mock_apic_login):
        session = mock_apic_login("rcdn9-fab1-apic2.cisco.com", "username", "password")
        obj = ACITreeResource()
        obj.session = session
        the_response = Response()
        the_response.status_code = 200
        with open("tests/sample_responses/aci_tree/get_interface_util_in.txt") as file:
            the_response._content = bytes(file.read(), "utf-8")

        obj.session.get.return_value = the_response
        util_in = obj.get_interface_errors_discards("node-1291", "Eth1/5", "utilIn")
        self.assertEqual(util_in, 4.0)

    def test_get_port_channel_unspecified(self):
        obj = ACITreeResource()
        with open(
            "tests/sample_responses/aci_tree/eth_phys_outputs/eth_phys_output.json"
        ) as json_file:
            obj.ethpm_phys_output = json.load(json_file)
        port_channel = obj.get_port_channel_name("node-1011", "eth1/34")
        self.assertEqual(port_channel, "unspecified")

    def test_get_port_channel_found_case(self):
        obj = ACITreeResource()
        with open(
            "tests/sample_responses/aci_tree/eth_phys_outputs/eth_phys_output.json"
        ) as json_file:
            obj.ethpm_phys_output = json.load(json_file)
        port_channel = obj.get_port_channel_name("node-1011", "eth1/33")
        self.assertEqual(port_channel, "po12")

    def test_get_port_channel_None_case(self):
        obj = ACITreeResource()
        with open(
            "tests/sample_responses/aci_tree/eth_phys_outputs/eth_phys_output.json"
        ) as json_file:
            obj.ethpm_phys_output = json.load(json_file)
        port_channel = obj.get_port_channel_name("node-1011", "eth1/35")
        self.assertIsNone(port_channel)

    def test_get_aci_node_name(self):
        obj = ACITreeResource()
        self.assertEqual(obj.get_aci_node_name("rtp1-fab1-sw1181"), "node-1181")

    @patch("hpc_app.resources.aci_tree.ACITreeResource.get_interface_errors_discards")
    def test_get_input_output_interface_errors(self, mock_gioie):
        obj = ACITreeResource()
        mock_gioie.side_effect = [("0", "0"), ("0", "0"), "0", "0"]
        data = dict(
            {
                "APIC": {
                    "input_error": "0",
                    "output_error": "0",
                    "input_discard": "0",
                    "output_discard": "0",
                    "output_util": "0",
                    "input_util": "0",
                }
            }
        )
        self.assertEqual(
            obj.get_input_output_interface_errors("node-1291", "Eth1/5"), data
        )

    @patch("hpc_app.resources.aci_tree.ACITreeResource.get_interface_data")
    def test_find_nodes_and_interfaces_switch_ucs(self, mock_get_interface_data):
        mapping_type = "switch_ucs"

        with open(
            "tests/sample_responses/aci_tree/get_interface_data_ouputs/switch_ucs.json"
        ) as file:
            mock_get_interface_data.side_effect = json.load(file)

        with open("tests/sample_responses/aci_tree/response_json.json") as file:
            expected_output = json.load(file)["switch_to_ucs"]

        obj = ACITreeResource()
        obj.nodes = {"1312", "1311"}

        with open(
            "tests/sample_responses/aci_tree/cdpadjep_outputs/cdp_output.json"
        ) as file:
            obj.json_to_be_parsed[mapping_type] = json.load(file)

        obj.json_type_to_be_parsed[mapping_type] = "cdpAdjEp"
        obj.key_to_find_interface[mapping_type] = "portId"

        output = obj.find_nodes_and_interfaces(obj.nodes, obj.ucs, mapping_type)

        expected_ucs = {"rcdn9-fab1-ucs01-131-A", "rcdn9-fab1-ucs01-131-B"}

        self.assertEqual(output, expected_output)
        self.assertEqual(obj.ucs, expected_ucs)

    @patch("hpc_app.resources.aci_tree.ACITreeResource.get_interface_data")
    def test_find_nodes_and_interfaces_switch_spine(self, mock_get_interface_data):
        mapping_type = "switch_spine"

        with open(
            "tests/sample_responses/aci_tree/get_interface_data_ouputs/switch_spine.json"
        ) as file:
            mock_get_interface_data.side_effect = json.load(file)

        with open("tests/sample_responses/aci_tree/response_json.json") as file:
            expected_output = json.load(file)["switch_to_spine"]

        obj = ACITreeResource()
        obj.nodes = {"1312", "1311"}

        with open(
            "tests/sample_responses/aci_tree/lldpadjep_outputs/lldp_output.json"
        ) as file:
            obj.json_to_be_parsed[mapping_type] = json.load(file)

        obj.json_type_to_be_parsed[mapping_type] = "lldpAdjEp"
        obj.key_to_find_interface[mapping_type] = "portIdV"

        output = obj.find_nodes_and_interfaces(
            obj.nodes, obj.spine_leaves, mapping_type
        )

        expected_spine_leaves = {
            "rcdn9-bb07-fab1-sw3923",
            "rcdn9-br07-fab1-sw3924",
            "rcdn9-br07-fab1-sw3922",
            "rcdn9-bb07-fab1-sw3921",
        }

        self.assertEqual(output, expected_output)
        self.assertEqual(obj.spine_leaves, expected_spine_leaves)

    @patch("hpc_app.resources.aci_tree.ACITreeResource.get_interface_data")
    def test_find_nodes_and_interfaces_spine_border(self, mock_get_interface_data):
        mapping_type = "spine_border"

        with open(
            "tests/sample_responses/aci_tree/get_interface_data_ouputs/spine_border.json"
        ) as file:
            mock_get_interface_data.side_effect = json.load(file)

        with open("tests/sample_responses/aci_tree/response_json.json") as file:
            expected_output = json.load(file)["spine_to_border"]

        obj = ACITreeResource()
        obj.spine_leaves = {
            "rcdn9-bb07-fab1-sw3923",
            "rcdn9-br07-fab1-sw3924",
            "rcdn9-br07-fab1-sw3922",
            "rcdn9-bb07-fab1-sw3921",
        }

        with open(
            "tests/sample_responses/aci_tree/lldpadjep_outputs/filtered_lldp_output.json"
        ) as file:
            obj.json_to_be_parsed[mapping_type] = json.load(file)

        obj.json_type_to_be_parsed[mapping_type] = "lldpAdjEp"
        obj.key_to_find_interface[mapping_type] = "portIdV"

        output = obj.find_nodes_and_interfaces(
            obj.spine_leaves, obj.border_leaves, mapping_type
        )

        expected_border_leaves = {"rcdn9-br07-fab1-sw3812", "rcdn9-bb07-fab1-sw3811"}

        self.assertEqual(output, expected_output)
        self.assertEqual(obj.border_leaves, expected_border_leaves)

    @patch("hpc_app.resources.aci_tree.ACITreeResource.get_interface_data")
    def test_find_nodes_and_interfaces_border_dcc(self, mock_get_interface_data):
        mapping_type = "border_dcc"

        with open(
            "tests/sample_responses/aci_tree/get_interface_data_ouputs/border_dcc.json"
        ) as file:
            mock_get_interface_data.side_effect = json.load(file)

        with open("tests/sample_responses/aci_tree/response_json.json") as file:
            expected_output = json.load(file)["border_to_dcc"]

        obj = ACITreeResource()
        obj.border_leaves = {"rcdn9-br07-fab1-sw3812", "rcdn9-bb07-fab1-sw3811"}

        with open(
            "tests/sample_responses/aci_tree/cdpadjep_outputs/filtered_cdp_output.json"
        ) as file:
            obj.json_to_be_parsed[mapping_type] = json.load(file)

        obj.json_type_to_be_parsed[mapping_type] = "cdpAdjEp"
        obj.key_to_find_interface[mapping_type] = "portId"

        output = obj.find_nodes_and_interfaces(
            obj.border_leaves, obj.dcc_gws, mapping_type
        )

        expected_dcc_gws = {
            "rcdn9-cd1-dmzdcc-gw1",
            "rcdn9-cd1-dcc-gw3",
            "rcdn9-cd2-dmzdcc-gw2",
            "rcdn9-cd2-dcc-gw4",
        }

        self.assertEqual(output, expected_output)
        self.assertEqual(obj.dcc_gws, expected_dcc_gws)

    @patch("hpc_app.resources.aci_tree.ACITreeResource.get_aci_node_name")
    @patch(
        "hpc_app.resources.aci_tree.ACITreeResource.get_input_output_interface_errors"
    )
    @patch("hpc_app.resources.aci_tree.ACITreeResource.get_port_channel_name")
    def test_get_interface_data(self, mock_gpcn, mock_gioie, mock_gann):
        mock_gann.return_value = "node-1311"
        mock_gioie.return_value = {
            "input_error": "0",
            "output_error": "0",
            "input_discard": "0",
            "output_discard": "0",
        }
        mock_gpcn.return_value = "po5"

        expected_output = {
            "switch_name": "rcdn9-fab1-sw1311",
            "switch_interface": "Eth1/1",
            "switch_interface_errors": {
                "input_error": "0",
                "output_error": "0",
                "input_discard": "0",
                "output_discard": "0",
            },
            "switch_port_channel": "po5",
        }
        obj = ACITreeResource()
        output = obj.get_interface_data("rcdn9-fab1-sw1311", "Eth1/1", "switch")

        self.assertEqual(output, expected_output)

    @patch("hpc_app.resources.aci_tree.create_connection_and_get_device_type")
    @patch("hpc_app.resources.aci_tree.get_port_channel_multiple_interfaces")
    @patch("hpc_app.resources.aci_tree.InterfaceStatResource.collect_info")
    @patch("hpc_app.resources.aci_tree.CommonResource.um_password")
    @patch("hpc_app.resources.aci_tree.CommonResource.um_username")
    def test_add_dcc_interface_stats(
        self,
        mock_umuser,
        mock_umpass,
        mock_scilogic_collect_info,
        mock_gpcmi,
        mock_conn,
    ):
        mock_conn.return_value = Mock()
        mock_gpcmi.return_value = {
            "Eth11/4": "po35",
            "Eth3/23": "po3",
            "Eth5/25": "po8",
            "Eth100/1": "None",
        }
        mock_umuser = "umuser"
        mock_umpass = "umpass"

        response_json = {
            "border_to_dcc": [
                {
                    "border_name": "rcdn9-br07-fab1-sw3812",
                    "border_interface": "Eth1/6",
                    "border_interface_errors": {
                        "input_error": "0",
                        "output_error": "0",
                        "input_discard": "0",
                        "output_discard": "0",
                    },
                    "border_port_channel": "po8",
                    "dcc_name": "rcdn9-cd1-dcc-gw3",
                    "dcc_interface": "Eth8/18",
                }
            ]
        }
        stat_data = [
            {
                "interface": "Ethernet8/18",
                "time_stamp": "timestamp1",
                "input_error": "0",
                "output_error": "0",
                "input_discard": "0",
                "output_discard": "0",
                "input_util": "0.5257863587104972",
                "output_util": "0.2509316151731895",
            }
        ]
        mock_scilogic_collect_info.return_value = stat_data, 200

        mock_gpcmi.return_value = {"Eth8/18": "po5"}

        expected_modified_json = {
            "border_to_dcc": [
                {
                    "border_interface": "Eth1/6",
                    "border_interface_errors": {
                        "input_discard": "0",
                        "input_error": "0",
                        "output_discard": "0",
                        "output_error": "0",
                    },
                    "border_name": "rcdn9-br07-fab1-sw3812",
                    "border_port_channel": "po8",
                    "dcc_interface": "Eth8/18",
                    "dcc_interface_errors": {
                        "input_discard": "0",
                        "input_error": "0",
                        "input_util": "0.5257863587104972",
                        "output_discard": "0",
                        "output_error": "0",
                        "output_util": "0.2509316151731895",
                        "time_stamp": "timestamp1",
                    },
                    "dcc_name": "rcdn9-cd1-dcc-gw3",
                    "dcc_port_channel": "po5",
                }
            ]
        }

        obj = ACITreeResource()
        obj.response_json = response_json
        obj.add_dcc_interface_stats()

        self.assertEqual(obj.response_json, expected_modified_json)

    @patch("hpc_app.resources.aci_tree.ACITreeResource.get_lldpadjep_output_from_api")
    @patch("hpc_app.resources.aci_tree.ACITreeResource.get_cdpadjep_output_from_api")
    @patch("hpc_app.resources.aci_tree.ACITreeResource.get_ethpm_phys_output_from_api")
    @patch("hpc_app.resources.aci_tree.ACITreeResource.get_node_id")
    @patch("hpc_app.resources.aci_tree.ACITreeResource.find_nodes_and_interfaces")
    @patch("hpc_app.resources.aci_tree.ACITreeResource.add_dcc_interface_stats")
    @patch("hpc_app.resources.aci_tree.SciLogicMultiUrlResource.collect_info")
    @patch("hpc_app.resources.aci_tree.CommonResource.apic_login")
    @patch("hpc_app.resources.aci_tree.CommonResource.webusername")
    @patch("hpc_app.resources.aci_tree.CommonResource.webpassword")
    @patch("hpc_app.resources.aci_tree.CommonResource.um_username")
    @patch("hpc_app.resources.aci_tree.CommonResource.um_password")
    def test_collect_info_tree_case(
        self,
        mock_um_pass,
        mock_um_user,
        mock_pass,
        mock_user,
        mock_apic_login,
        mock_sci_urls,
        mock_adis,
        mock_fnai,
        mock_gni,
        mock_gepofa,
        mock_gcofa,
        mock_glofa,
    ):

        mock_gepofa.return_val = None
        mock_gcofa.return_val = None
        mock_glofa.return_val = None
        mock_gni.return_val = None

        with open(
            "tests/sample_responses/aci_tree/response_json_with_dcc_data.json"
        ) as json_file:
            response_json = json.load(json_file)

        mock_fnai.side_effect = [
            response_json["switch_to_ucs"],
            response_json["switch_to_spine"],
            response_json["spine_to_border"],
            response_json["border_to_dcc"],
        ]
        mock_adis.return_value = None

        mock_sci_urls.return_value = (
            [
                ("rcdn9-fab1-ucs01-131-A", "url1"),
                ("rcdn9-fab1-sw1311", "url2"),
                ("rcdn9-bb07-fab1-sw3921", "url3"),
                ("rcdn9-br07-fab1-sw3812", "url5"),
                ("rcdn9-cd1-dcc-gw3", "url5"),
            ],
            200,
        )

        mock_user.return_value = "username"
        mock_pass.return_value = "password"
        mock_um_user.return_value = "username"
        mock_um_pass.return_value = "password"
        mock_apic_login.return_value = "session"

        obj = ACITreeResource()
        obj.host = "host"
        obj.apic = "rcdn9-fab1-apic2.cisco.com"
        obj.response_json = response_json

        tree = Tree(hostname=obj.host, type="host", order=-2)
        ucs = "rcdn9-fab1-ucs01-131-A"
        switch = "rcdn9-fab1-sw1311"
        spine = "rcdn9-bb07-fab1-sw3921"
        border = "rcdn9-br07-fab1-sw3812"
        dcc = "rcdn9-cd1-dcc-gw3"
        tree.add_node(ucs, "ucs", 0)
        tree.add_node(switch, "switch", 1)
        tree.add_node(spine, "spine", 2)
        tree.add_node(border, "border", 3)
        tree.add_node(dcc, "dcc", 4)

        tree.add_connection(switch, ucs, "Eth1/1", "Eth3/9", "switch_to_ucs", True)
        tree.add_connection(
            switch, spine, "Eth1/49", "Eth1/17", "switch_to_spine", True
        )
        tree.add_connection(
            spine, switch, "Eth1/17", "Eth1/49", "spine_to_switch", True
        )
        tree.add_connection(
            spine, border, "Eth2/19", "Eth1/52", "spine_to_border", True
        )
        tree.add_connection(
            border, spine, "Eth1/52", "Eth2/19", "border_to_spine", True
        )
        tree.add_connection(border, dcc, "Eth1/6", "Eth8/18", "border_to_dcc", True)
        tree.add_connection(dcc, border, "Eth8/18", "Eth1/6", "dcc_to_border", True)

        tree.add_link_data(
            switch,
            "Eth1/1",
            {
                "input_error": "0",
                "output_error": "0",
                "input_discard": "0",
                "output_discard": "0",
            },
            "po5",
        )
        tree.add_link_data(
            switch,
            "Eth1/49",
            {
                "input_error": "0",
                "output_error": "0",
                "input_discard": "0",
                "output_discard": "0",
            },
            "unspecified",
        )
        tree.add_link_data(
            spine,
            "Eth1/17",
            {
                "input_error": "0",
                "output_error": "0",
                "input_discard": "0",
                "output_discard": "0",
            },
            "unspecified",
        )
        tree.add_link_data(
            spine,
            "Eth2/19",
            {
                "input_error": "0",
                "output_error": "0",
                "input_discard": "0",
                "output_discard": "0",
            },
            "unspecified",
        )
        tree.add_link_data(
            border,
            "Eth1/52",
            {
                "input_error": "3",
                "output_error": "0",
                "input_discard": "0",
                "output_discard": "0",
            },
            "unspecified",
        )
        tree.add_link_data(
            border,
            "Eth1/6",
            {
                "input_error": "0",
                "output_error": "0",
                "input_discard": "0",
                "output_discard": "0",
            },
            "po8",
        )
        tree.add_link_data(
            dcc,
            "Eth8/18",
            {
                "input_error": "0",
                "output_error": "0",
                "input_discard": "0",
                "output_discard": "0",
            },
            "po5",
        )

        out_tree = obj.collect_info(
            "host",
            get_tree_obj=True,
            args={
                "hostname": "host",
                "ip": "host_ip",
                "location": "ACI",
                "dcgw_or_apic": "apic",
            },
        )
        self.assertEqual(len(tree.nodes), len(out_tree.nodes))
        self.assertEqual(
            set([node.name for node in tree.nodes]),
            set([node.name for node in out_tree.nodes]),
        )
