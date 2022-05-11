## Tech support file deletion

### Description
* This project has the scripts for collecting the audit logs for tech support files and deleting the files that are older than 30 days via NSO 

### Requirements
* Scripts are required to be run in environment with python <=3.9 as of now. Issue reference: https://github.com/datacenter/acitoolkit/issues/377 (# The acitoolkit base package has been updated to remediate this dependancy)

### Running the scripts (listed in the order in which they should be ran)
* For production APICs run the scripts(especially Collecting_audit_data.py) from a jump host.
* For deletion scripts using NSO, create a file called .env in home directory and add these two lines
    ```
     NSO_SERVER=nso-rtp-test-01
     NSO_PORT=8888
    ```
  change the values based on the NSO server you are using (when you are running for prod devices configured in prod NSO
   instances)

* Collecting_audit_data.py -> this loads the faults for a given APIC and creates a json/excel with all the relevant information for 
deletion part under techcollection
* NS0_Techsupport_delete.py -> deletes the tech support files that are older than 30 days via NSO were the payload inputs will be CollectionTime,name and nodeId as we configured the same in NSO as a service package
* rollback -> Rollback is not possible as there won't be any commit will be performed during the deletion of Tech support files via NSO
** We can't retrieve the tech support files once we deleted either via APIC or NSO

Steps to follow:
1.Run the Collecting_audit_data.py script and get the files stored in Techsupportcollection_pre_deletion.json and also we have Techsupportcollection_pre_deletion.csv for pretty viewing.

2.Run the NS0_Techsupport_delete.py script and as per the script it will read the Techsupportcollection_pre_deletion.json and delete all the Tech support files older than 30 days and will be stored in 
Techsupportcollection_post_deletion.json and Techsupportcollection_post_deletion.csv for pretty viewing.
** .csv files are used only for pretty viewing only were the .json files will be always taken as a input.

3.Once all the operational data got deleted using NS0_Techsupport_delete.py vi NSO 
Run the Techsupport_Profile_deletion.py 
a).It will generate the Techsupportcollection_profile_check.json file.
b).The Techsupportcollection_profile_check.json file will check for the tsod(profile) with Techsupportcollection_profile_validate.json for the Tech support files.
C).If all Operational and policy files are deleted for a particular tsod(proflle) then Tech support profile will be deleted else it will skip to next tsod(profile).
d).The output of the file will be printed and stored in Techsupport_profile_deletion.txt

4.Storage information can be viewed in the StorageTechsupportinfo.json once we run the StorageTechsupportinfo.py file.

5.Deleting_local_Techsupportfiles_step5 to delete all the tech support files more than 30 days stored locally in the APIC.