def loadConfig(device):
    myconfig=[]

#------auto check updates
    mydict={}
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

    myconfig.append(mydict)

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

    myconfig.append(mydict)

    return myconfig




