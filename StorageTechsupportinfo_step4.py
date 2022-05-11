import argparse
import json
import os
import getpass
import csv
from apic_api_driver import ApiDriver
from dotenv import load_dotenv

# loads environment variables from .env file
load_dotenv()

def get_data(fab='', folder='techcollection'):
    if not os.path.isdir(folder):
        os.makedirs(folder)
    file_name = f"StorageTechsupportinfo.json"
    file_name = f"{folder}/{file_name}"


    # Generate the json file
    query = '/api/node/mo/topology/pod-1/node-1/sys/ch/p-[/techsupport]-f-[/dev/mapper/vg_ifc0-techsupport].json?' \
            'rsp-subtree-include=fault-records,no-scoped,subtree&subscription=yes&order-by=faultRecord.created|desc&page=0&page-size=100'

    resp = Driver.get(query)
    print("\n Successfully downloaded the storagetechsupport info files \n ")
    if not resp.ok:
        raise Exception("Failed to get path")

    with open(file_name, "w") as f:
        f.write(json.dumps(resp.json(), indent=4))


if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser()

    # Add the arguments
    parser.add_argument('-a', '--apic',
                        type=str,
                        help='apic name, give the full hostname, avoid .cisco.com  eg: svlngen4-fab1-apic1')
    parser.add_argument('-u', '--apic_user',
                        type=str,
                        help='apic username')
    args = parser.parse_args()

    if args.apic:
        apic = args.apic
    else:
        apic = input('APIC: ').strip()

    if args.apic_user:
        os.environ['apic-username'] = args.apic_user
    else:
        os.environ['apic-username'] = input('APIC User: ').strip()

    os.environ['apic-password'] = getpass.getpass(prompt='password: ').strip()

    try:
        Driver = ApiDriver(apic)
        get_data(Driver.fab)
    except Exception as e:
        print(e)
        exit(0)
