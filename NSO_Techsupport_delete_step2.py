from nso_helper import NSOAPIDriver
from datetime import timedelta, datetime, date
import getpass
import json
import argparse
import os
import urllib3
import csv
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def delete_tech_supp_files(collectionTime, polName, nodeId):
    # define for dynamically taking values from input params
    # Rollback can't be performed as the delete can't perform any commit

    deletion_url = "/live-status/tailf-ned-cisco-apicdc-stats:exec/delete-tech-support-status"
    del_payload = {
        "input": {
            "polName": polName,
            "collectionTime": collectionTime,
            "nodeId": nodeId
        }
    }

    # Call the API using NSO for deleting the tech support file

    resp = Driver.post(deletion_url, payload=del_payload)
    print(resp.text)

    if resp.status_code == 404:
        print('No file is found for deletion')
        return False
    elif resp.status_code != 200:
        print('Some error occurred. Couldn\'t delete the tech support file. Check manually')
        return False
    else:
        print("Tech support file is deleted \n")
        print("############################################################### \n")
        return True
    # Print the rollback id
    # #print(f'Rollback ID: {resp.json()["tailf-restconf:result"]["rollback"]["id"]}')


# inside you're using the existing audit script, create the NSO driver instance inside __name__ == "__main__",
# Else create a new script for deletion (copy the apic, user, password part from the audit script
if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser()

    # Add the arguments
    parser.add_argument('-a', '--apic',
                        type=str,
                        help='apic name as per in NSO')
    parser.add_argument('-u', '--nso_user',
                        type=str,
                        help='apic username')
    args = parser.parse_args()

    if args.apic:
        apic = args.apic
    else:
        apic = input('APIC: ').strip()  # "svlngen4-fab1-apic1" #

    if args.nso_user:
        os.environ['NSO_USERNAME'] = args.nso_user
    else:
        os.environ['NSO_USERNAME'] = input('NSO User:  ').strip()

    os.environ['NSO_PASSWORD'] = getpass.getpass(prompt='password: ').strip()

    Driver = NSOAPIDriver(apic)
    # syncing to make sure we have latest data
    print('Running sync from...')
    Driver.sync_from()
    # Generate the required fields/params for deletion from the audit json file
    output_file = 'techcollection/Techsupportcollection_post_deletion.csv'
    csv_file = open(output_file, 'w', newline='')
    csv_writer = csv.writer(csv_file)

    # Print the Header row
    csv_writer.writerow(['Creation Time', 'Policy Name', 'Node ID'])

    with open('techcollection/Techsupportcollection_pre_deletion.json', 'r') as f:

        file_data = json.load(f)
        delete_json = []
        for child_iter in file_data['imdata']:
            collectionTime = child_iter['dbgexpTechSupStatus']['attributes']['collectionTime']
            polName = child_iter['dbgexpTechSupStatus']['attributes']['polName']
            nodeId = child_iter['dbgexpTechSupStatus']['attributes']['nodeId']

            try:
                today = date.today()
                creation_date = datetime.strptime(collectionTime.split("T")[0], "%Y-%m-%d").date()
                if today - creation_date > timedelta(days=30):
                    print(collectionTime, polName, nodeId)
                    if delete_tech_supp_files(collectionTime, polName, nodeId):
                        csv_writer.writerow([collectionTime, polName, nodeId])
                        delete_json.append(child_iter)
                    else:
                        print("Failed")
            except Exception as e:
                print(e.__str__())
                exit(0)
            except KeyboardInterrupt as K:
                break
        with open("techcollection/Techsupportcollection_post_deletion.json", 'w') as T:
            json.dump(delete_json, T)
    csv_file.close()
    print("\n Techsupportcollection_post_deletion.csv is generated")
    print(" Techsupportcollection_post_deletion.json is generated \n")
