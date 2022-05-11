import argparse
import json
import os
import getpass
import csv
from apic_api_driver import ApiDriver
from dotenv import load_dotenv

# loads environment variables from .env file
load_dotenv()

def get_data(Driver='', folder='techcollection'):
    if not os.path.isdir(folder):
        os.makedirs(folder)
    file_name = f"Techsupportcollection_pre_deletion.json"
    file_name = f"{folder}/{file_name}"

    output_file = f'{folder}/{Driver.apic}Techsupportcollection_pre_deletion.csv'
    csv_file = open(output_file, 'w', newline='')
    csv_writer = csv.writer(csv_file)
    # Print the Header row
    csv_writer.writerow(['Creation Time', 'Policy Name', 'Node ID'])

    # Generate the json file
    query = '/api/node/class/dbgexpTechSupStatus.json?query-target-filter=' \
            'and(not(wcard(dbgexpTechSupStatus.dn,"__ui_")),' \
            'and(ne(dbgexpTechSupStatus.exportStatus,"preInit"),' \
            'wcard(dbgexpTechSupStatus.dn,"expcont/expstatus-tsod-")))&subscription=yes'

    resp = Driver.get(query)
    print("\n Successfully downloaded Tech support files \n ")
    if not resp.ok:
        raise Exception("Failed to get path")

    with open(file_name, "w") as f:
        f.write(json.dumps(resp.json(), indent=4))

    # Generate the .csv file
    with open(file_name, 'r') as f:
        file_data = json.load(f)

        for child_iter in file_data['imdata']:
            collectionTime = child_iter['dbgexpTechSupStatus']['attributes']['collectionTime']
            polName = child_iter['dbgexpTechSupStatus']['attributes']['polName']
            nodeid = child_iter['dbgexpTechSupStatus']['attributes']['nodeId']
            print(collectionTime, polName, nodeid)
            csv_writer.writerow([collectionTime, polName, nodeid])


    print("\n Techsupportcollection_pre_deletion.json created successfully ")
    print(" Techsupportcollection_pre_deletion.csv created successfully \n ")

if __name__ == "__main__":
    apic_list = ["svlngen4-fab1-apic1","svlngen4-fab2-apic1"]
    username_list = ["admin","admin"]
    password_list = ["5vlFab1!!","F@b2ap1c"]


    for i in range (0,len(apic_list)):
        os.environ['apic-username'] = username_list[i]
        os.environ['apic-password'] = password_list[i]
        Driver = ApiDriver(apic_list[i])
        get_data(Driver)

