from acitoolkit import acitoolkit as aci

import os
import re


class ApiDriver:
    def __init__(self, apic):
        self.apic = apic
        self.session = self._apic_login(self.apic)

    @staticmethod
    def _apic_login(apic):
        apic_url = f"https://{apic}"
        session = aci.Session(apic_url, os.environ['apic-username'], os.environ['apic-password'])
        resp = session.login()
        if not resp.ok:
            print(resp.text)
            raise Exception(f"Could not login to {apic}. Resp: {resp.text}")
        else:
            return session

    def close(self):
        self.session.close()

    def get(self, query):
        return self.session.get(query)

    def post(self, url, payload):
        return self.session.push_to_apic(url, payload)

    @property
    def fab(self):
        dc = self.apic.split('-')[0]
        fab = re.search(r"fab\d+", self.apic).group(0)
        return f"{dc}-{fab}"
