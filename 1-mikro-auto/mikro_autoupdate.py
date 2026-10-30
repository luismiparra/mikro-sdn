import os
import json
from dotenv import load_dotenv

load_dotenv()

#Url every router calls 5 minutes after boot to ask for a push of its config
#(the /router_boot_update endpoint of the web portal). Empty: the boot script is not created
boot_update_url = os.environ.get("BOOT_UPDATE_URL")
#Hosts every router pings each hour, it reboots when none of them answers. Empty: the script is not created
mgmt_check_hosts = json.loads(os.environ.get("MGMT_CHECK_HOSTS") or "[]")

def load_config(device):
    my_config=[]

#------auto check updates
    mydict={}
    mydict['disabled'] = 'true'
    mydict['comment'] = f"script_autoupdate"
    mydict['resource'] = '/system/scheduler'
    mydict['name'] = f"script_autoupdate"
    mydict['use_set'] = False
    mydict['policy'] = "ftp,reboot,read,write,policy,test,password,sniff,sensitive,romon"
    mydict['start-date'] = "2022-01-01"
    mydict['start-time'] = "03:10:00"
    mydict['interval'] = "1d"
    mydict['on-event'] = f"\
/system package update\r\
\ncheck-for-updates once\r\
\n:delay 3s;\r\
\n:if ( [get status] = \"New version is available\") do={{ install }}"

    my_config.append(mydict)

#------ask for config on boot
    if boot_update_url:
        mydict={}
        mydict['comment'] = f"script_boot_get_config"
        mydict['resource'] = '/system/scheduler'
        mydict['name'] = f"script_boot_get_config"
        mydict['use_set'] = False
        mydict['policy'] = "ftp,reboot,read,write,policy,test,password,sniff,sensitive,romon"
        mydict['start-time'] = "startup"
        mydict['on-event'] = f"\
:delay 300s;\r\
\ntool/fetch mode=http http-method=get output=none port=80 url={boot_update_url}"

        my_config.append(mydict)

#------clean usermanager sessions on boot
    mydict={}
    mydict['comment'] = f"script_clean_usermanagersessions"
    mydict['resource'] = '/system/scheduler'
    mydict['name'] = f"script_clean_usermanagersessions"
    mydict['use_set'] = False
    mydict['policy'] = "ftp,reboot,read,write,policy,test,password,sniff,sensitive,romon"
    mydict['start-time'] = "startup"
    mydict['interval'] = "1d"
    mydict['on-event'] = f"\
:delay 60s;\r\
\nuser-manager/session remove [find where active=yes]\r\
\nuser-manager/session remove [find where active=no]"

    my_config.append(mydict)

#------Enable all WG peers always
#Fix issues with duplicated ports that disable the interface
    mydict={}
    mydict['comment'] = f"script_enable_all_wireguard_interfaces"
    mydict['resource'] = '/system/scheduler'
    mydict['name'] = f"script_enable_all_wireguard_interfaces"
    mydict['use_set'] = False
    mydict['policy'] = "ftp,reboot,read,write,policy,test,password,sniff,sensitive,romon"
    mydict['start-time'] = "startup"
    mydict['interval'] = "1d"
    mydict['on-event'] = ":foreach i in=[/interface wireguard find] do={/interface wireguard enable $i}"

    my_config.append(mydict)

#------Auto Reboot if mgmt lost
    if mgmt_check_hosts:
        pings = ""
        for number, host in enumerate(mgmt_check_hosts, start=1):
            pings += f"\nlocal host{number} \"{host}\"\r"
        pings += "\nlocal pingCount 20\r\nlocal successCount 0\r\n\r"
        for number in range(1, len(mgmt_check_hosts) + 1):
            pings += (f"\nif ([/ping $host{number} count=$pingCount] > 0) do={{set successCount ($successCount + 1)}}"
                      f" else={{/log warning (\"Ping host{number} (\" . $host{number} . \") fail.\")}}\r")

        mydict={}
        mydict['comment'] = f"script_auto_reboot_if_mgmt_lost"
        mydict['resource'] = '/system/scheduler'
        mydict['name'] = f"script_auto_reboot_if_mgmt_lost"
        mydict['use_set'] = False
        mydict['policy'] = "ftp,reboot,read,write,policy,test,password,sniff,sensitive,romon"
        mydict['start-time'] = "startup"
        mydict['interval'] = "1h"
        mydict['on-event'] = pings + "\
\nif ($successCount = 0) do={\r\
\n/log warning \"Auto reloading device all mgmt pings fail.\"\r\
\n/system reboot}\r"

        my_config.append(mydict)

    return my_config