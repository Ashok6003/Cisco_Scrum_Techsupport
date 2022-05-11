from netmiko import ConnectHandler
import getpass

APIC = input("APIC: ")
User = input("User: ")
Password = getpass.getpass()
print(f"\n{'#' * 50}\n1. Connecting tO APIC \n{'#' * 50}")

def Deleting_local_Techsupport_files(APIC,User,Password):
    with open("techcollection/Deleting_Local_Techsupportfiles.txt", "w") as f:
        devices123 = {
                "device_type": "cisco_nxos",
                "host": APIC,
                "username": User,
                "password": Password
            }
        ssh123 = ConnectHandler(**devices123)
        cmds = ["cd /data/techsupport/","ls -l","df -h | grep tech"]
        for cmd in cmds:
            Get_list = ssh123.send_command(cmd)
            print(Get_list)
            f.write(f"{Get_list}")
        print("#" * 50)
        f.write("#" * 50)
        print("\nCollecting Tech support files more than 30 days:\n")
        f.write("\nCollecting Tech support files more than 30 days:\n")
        Collectfiles_more30days = ssh123.send_command("find /data/techsupport/ -mtime +30 -ls | grep .gz")
        print(Collectfiles_more30days)
        f.write(f"{Collectfiles_more30days}")
        print("#" * 50)
        f.write("#" * 50)
        print("\nDeleting Tech support files more than 30 days:\n")
        f.write("\nDeleting Tech support files more than 30 days:\n")
        Delete_techsupportfiles_morethan_30days = ssh123.send_command("find /data/techsupport/ -type f -mtime +30 -name '*.gz' -delete")
        print(Delete_techsupportfiles_morethan_30days)
        f.write(f"{Delete_techsupportfiles_morethan_30days}")
        print("#" * 50)
        f.write("#" * 50)
        print("\nAfter deletion of all Tech support files more than 30 days:\n")
        f.write("\nAfter deletion of all Tech support files more than 30 days:\n")
        collect = ["cd /data/techsupport/","ls -l","df -h | grep tech"]
        for collectfiles in collect :
            Get_list2 = ssh123.send_command(collectfiles)
            print(Get_list2)
            f.write(f"{Get_list2}")
        print(f"\n{'#'*50}\nFinished Executing Script\n{'#'*50}")
        f.write(f"\n{'#'*50}\nFinished Executing Script\n{'#'*50}")


Deleting_local_Techsupport_files(APIC,User,Password)