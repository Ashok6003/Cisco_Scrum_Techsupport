import os
import time
import requests
import json
import re
from dotenv import load_dotenv

load_dotenv()

PROTOCOL = 'https'

def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts))
        else:
            print('%r  %2.2f s %r' % (method.__name__, (te - ts), args[1] if args else None))
        if isinstance(result, requests.Response):
            print(f"{result.status_code}")
        return result

    return timed


class NSOAPIDriver:
    """Facilitates communicating with NSO. Initially will only support RESTCONF
    as that is the NSO preferred way of communicating over HTTP/s.
    """

    def __init__(self, device):
        self.api_base = f"{PROTOCOL}://{os.environ['NSO_SERVER']}:{os.environ['NSO_PORT']}/restconf/data/tailf-ncs" \
                        f":devices/device={device}/"

    # "https://nso-rtp-test-01:8888/restconf/data/tailf-ncs:devices/device=svlngen4-fab1-apic1"
        self.user = os.environ['NSO_USERNAME']
        self.password = os.environ['NSO_PASSWORD']

        self.__auth = (self.user, self.password)

        self.device = device

        # content-type headers to return the various types of responses from NSO in JSON format
        self.headers = {
            "Accept": "application/yang-data+json",
            "Content-Type": "application/yang-data+json",
        }

    @timeit
    def get(self, url):
        response = requests.request("GET", self.api_base + url, headers=self.headers, auth=self.__auth, verify=False)
        return response

    @timeit
    def delete(self, url):
        response = requests.request("DELETE", self.api_base + url, headers=self.headers, auth=self.__auth, verify=False)
        return response

    @timeit
    def post(self, url, payload):
        response = requests.request("POST", self.api_base + url, headers=self.headers, auth=self.__auth,
                                    data=json.dumps(payload), verify=False)
        return response

    @timeit
    def patch(self, url, payload):
        response = requests.request("PATCH", self.api_base + url, headers=self.headers, auth=self.__auth, data=payload)
        return response

    def get_rollbacks(self):
        response = requests. \
            request("GET",
                    f"{PROTOCOL}://{os.environ['NSO_SERVER']}:{os.environ['NSO_PORT']}/restconf/data/tailf-rollback"
                    f":rollback-files/file",
                    headers=self.headers, auth=self.__auth, verify=False)
        return response

    @timeit
    def rollback(self, rollback_id):
        response = requests. \
            request("POST", f"{PROTOCOL}://{os.environ['NSO_SERVER']}:{os.environ['NSO_PORT']}/restconf/data/tailf"
                            f"-rollback:rollback-files/apply-rollback-file",
                    headers=self.headers, auth=self.__auth, data=json.dumps({"input": {"fixed-number": rollback_id}}),
                    verify=False)
        return response

    def sync_from(self):
        return self.post(f"sync-from", {})

    @property
    def fab(self):
        dc = self.device.split('-')[0]
        fab = re.search(r"fab\d+", self.device).group(0)
        return f"{dc}-{fab}"
