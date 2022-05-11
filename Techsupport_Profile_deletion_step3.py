import argparse
import json
import os
import getpass
from apic_api_driver import ApiDriver
from dotenv import load_dotenv

# loads environment variables from .env file
load_dotenv()
#Get output of the Tech support profile information and split the tsod information

def get_Profile_tsodinfo(fab=''):
    query = '/api/node/mo/uni/fabric.json?query-target=subtree&target-subtree-class=dbgexpTechSupOnD&query-target-filter=not(wcard(dbgexpTechSupOnD.dn,"__ui_"))&target-subtree-class=dbgexpRsExportDest,dbgexpRsTsSrc,dbgexpRtApplTechSupOnDemand&query-target=subtree&subscription=yes'
    resp = Driver.get(query)
    data = resp.json()
    with open('techcollection/Techsupportcollection_profile_check.json', 'w') as f:
        json.dump(data,f,indent=2)
    final_op = []
    for i in data["imdata"]:
       for j in i.values():
           if "attributes" in j.keys():
               final_op.append(j["attributes"]["dn"].split("/")[2])
    return list(set(final_op))

#Get the output of the operational data for the tech support profile

def get_profile_deletionstatus(fab=''):
    query = '/api/node/class/dbgexpTechSupStatus.json?query-target-filter=and(not(wcard(dbgexpTechSupStatus.dn,"__ui_")),and(ne(dbgexpTechSupStatus.exportStatus,"preInit"),wcard(dbgexpTechSupStatus.dn,"expcont/expstatus-tsod-")))&subscription=yes'
    resp = Driver.get(query).json()
    with open('techcollection/Techsupportcollection_profile_validate.json', 'w') as f:
        json.dump(resp,f,indent=2)
    return resp["imdata"]

#To delete the Tech support  profile(tsod)
#method: POST
#url: http://svlngen4-fab1-apic1.cisco.com/api/node/mo/uni/fabric/tsod-coparaoc2_test.json
#payload{"dbgexpTechSupOnD":{"attributes":{"dn":"uni/fabric/tsod-coparaoc2_test","status":"deleted"},"children":[]}}

def delete_profile_tsod(fab='',tsod = "uni/fabric/tsod-693081086_opflexdown",f=None):
    query = f'/api/node/mo/{tsod}.json'
    payload = {"dbgexpTechSupOnD": {"attributes": {"dn": tsod, "status": "deleted"}, "children": []}}
    resp = Driver.post(query, payload=payload)
    if resp.status_code ==200:
        print(f"Successfully deleted {tsod}")
        f.write(f"Successfully deleted {tsod}\n")
    else:
        print(f"Unsuccessful for {tsod}",resp.status_code, resp.text)
        f.write(f"Unsuccessful for {tsod}{str(resp.status_code)}{resp.text}\n")

#checking the files in operational data with "exportDbUri","exportFileUri"and "exportLogsUri" if theese files are already deleted for its respective tsod and  tsnode
#if the files are still there it will go for "Not to be deleted" else if the fileuri is showing login denied or "" empty
# then it will go for "To_be_deleted" and delete the Tech support profile under delete__profile_tsod

def checking_deleting_tsodprofile(fab=""):
    tsod_list = get_Profile_tsodinfo(fab)
    deletion_status = get_profile_deletionstatus(fab)
    Not_to_be_deleted = []  #collect the Not_to_be_deleted file
    for tsod in tsod_list:
        flag = False
        for i in deletion_status:
            if not flag:
                for j in i.values():
                    if "attributes" in j.keys() and tsod in j["attributes"]["dn"] and \
                            (j["attributes"]["exportDbUri"] not in ["","Login denied"] or j["attributes"]["exportFileUri"] not in ["","Login denied"] or j["attributes"]["exportLogsUri"] not in ["","Login denied"]):
                        Not_to_be_deleted.append(tsod)
                        flag = True
    with open("techcollection/Techsupport_profile_deletion.txt","w") as f:
        f.write("Not_to_be_deleted:\n")
        print("\n\n NOT_To_Be_Deleted:")
        if Not_to_be_deleted == []:
            print("NA")
            f.write("NA\n")
        else:
            for i in Not_to_be_deleted:
                print(i)
                f.write(i+"\n")
        to_be_deleted = list(set(tsod_list) - set(Not_to_be_deleted))   #collect the To_be_deleted file
        print("#"*50)
        f.write("#"*50)
        print("\n\n\n\nTo_Be_Deleted:\n")
        f.write("\n\n\nTo_be_Deleted:\n")
        for j in to_be_deleted:
            print(j)
            f.write(j+"\n")
        print("#"*50)
        f.write("#"*50)
        print("\n\nTech support Profile Deletion:")
        f.write(f"\n\nTech support Profile Deletion:\n")
        for tsod in to_be_deleted:
            delete_profile_tsod(fab,"uni/fabric/"+ tsod,f)   #Delete the Profile information

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
        apic = input('APIC:  ').strip()
         #apic = 'svlngen4-fab2-apic1'
    if args.apic_user:
        os.environ['apic-username'] = args.apic_user
    else:
        os.environ['apic-username'] = input('APIC User: ').strip()

    os.environ['apic-password'] = getpass.getpass(prompt='password: ').strip()


    Driver = ApiDriver(apic)
    checking_deleting_tsodprofile(Driver.fab)