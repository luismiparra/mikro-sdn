from flask import Flask , render_template
from flask import request
import web_shared



import os
from dotenv import load_dotenv

import logging
import ipaddress


load_dotenv()

debugmode = os.environ.get("DEBUGMODE")
main_auto_py_exec = os.environ.get("MAIN_AUTO_PY_EXEC")
#Branding of the pages: name in the title and header, and the link of the logo and footer
org_name = os.environ.get("ORG_NAME") or "mikro-sdn"
portal_home_url = os.environ.get("PORTAL_HOME_URL") or ""


my_inventory = web_shared.load_inventory()
mycontrol = web_shared.loadControl()



app = Flask(__name__)


@app.context_processor
def branding():
        return {'org_name': org_name, 'portal_home_url': portal_home_url}


def getLocation(inventory,ip):
        #FAKE LOCALHOST IP FOR TESTING
        if ip == "127.0.0.1":
                ip = "10.22.1.2"
        #----------------------
        # 
        #         
        logging.debug("Get location - Check if valid private ip")
        if ipaddress.ip_address(ip) in ipaddress.ip_network('10.0.0.0/8'):
                for item in inventory:
                        if ipaddress.ip_address(ip) in ipaddress.ip_network(item['subnetv4']):
                                return item
        
        logging.error("invalid ip")
        return False

def router_bootCheck(inventory,ip):
        #FAKE LOCALHOST IP FOR TESTING
        if ip == "127.0.0.1":
                ip = "192.168.88.11"
        #----------------------
        # 
        #         
        logging.debug("Get location - Check if valid private ip")
        if ipaddress.ip_address(ip) in ipaddress.ip_network(mycontrol['mgmt_allow_subnet']):
                for item in inventory:
                        if ip == item['mgmt_int']:
                                return item

        #THIS IS JUST FOR TESTING ENV
        if ipaddress.ip_address(ip) in ipaddress.ip_network('192.168.88.0/24'):
                for item in inventory:
                        if ip == item['mgmt_int']:
                                return item

        logging.error("invalid ip")
        return False


def apiCheckPihole(device,ip):
        #FAKE LOCALHOST IP FOR TESTING
        if ip == "127.0.0.1":
                ip = "10.22.1.2"
        #----------------------

        response = web_shared.getItem(device,"/ip/firewall/address-list")
        for item in response:
                if f"auto_webapp_ACL4_PORTAL_DNS_{ip}" == item['comment']:
                        return item
        return False

def apiCheckVpn(device,ip):
        #FAKE LOCALHOST IP FOR TESTING
        if ip == "127.0.0.1":
                ip = "10.22.1.2"
        #----------------------

        response = web_shared.getItem(device,"/ip/firewall/address-list")
        for item in response:
                if f"auto_webapp_ACL4_PORTAL_VPN_{ip}" == item['comment']:
                        return item
        return False


#ENABLE IS DELETE THE ADL
def apiEnablePihole(device,ip):
        #FAKE LOCALHOST IP FOR TESTING
        if ip == "127.0.0.1":
                ip = "10.22.1.2"
        #----------------------
        #Get status
        response = apiCheckPihole(device,ip)
        #If exist
        if response:
                web_shared.deleteItem(device,"/ip/firewall/address-list",response['.id'])
        
def apiDisableVpn(device,ip):
        #FAKE LOCALHOST IP FOR TESTING
        if ip == "127.0.0.1":
                ip = "10.22.1.2"
        #----------------------
        #Get status
        response = apiCheckVpn(device,ip)
        #If exist
        if response:
                web_shared.deleteItem(device,"/ip/firewall/address-list",response['.id'])


#DISABLE IS ADD THE ADL
def apiDisablePihole(device,ip,forever):
        #FAKE LOCALHOST IP FOR TESTING
        if ip == "127.0.0.1":
                ip = "10.22.1.2"
        #----------------------
        if forever:
                mydata = {'comment':f"auto_webapp_ACL4_PORTAL_DNS_{ip}", 'address':ip, 'list':'ACL4_PORTAL_DNS', 'timeout':'30d','disabled':'false' }
        else:
                mydata = {'comment':f"auto_webapp_ACL4_PORTAL_DNS_{ip}", 'address':ip, 'list':'ACL4_PORTAL_DNS', 'timeout':'1d', 'disabled':'false' }
        response = apiCheckPihole(device,ip)
        #If exist
        if response:
                web_shared.patchItem(device,"/ip/firewall/address-list",mydata,response['.id'])
        else:
                web_shared.putItem(device,"/ip/firewall/address-list",mydata)

def apiEnableVpn(device,ip):
        #FAKE LOCALHOST IP FOR TESTING
        if ip == "127.0.0.1":
                ip = "10.22.1.2"
        #----------------------
        mydata = {'comment':f"auto_webapp_ACL4_PORTAL_VPN_{ip}", 'address':ip, 'list':'ACL4_PORTAL_VPN',  'disabled':'false' }
        response = apiCheckVpn(device,ip)
        #If exist
        if response:
                web_shared.patchItem(device,"/ip/firewall/address-list",mydata,response['.id'])
        else:
                web_shared.putItem(device,"/ip/firewall/address-list",mydata)


@app.route('/')
def index():
        global my_inventory
        mydevice = getLocation(my_inventory,request.remote_addr)
        pihole_mystatus = apiCheckPihole(mydevice,request.remote_addr)
        my_piholestatus  = piholeStatusSTR(pihole_mystatus)
        vpn_mystatus = apiCheckVpn(mydevice,request.remote_addr)
        my_vpnstatus  = vpnStatusSTR(vpn_mystatus)

        return render_template('index.html', title='Welcome', ip=request.remote_addr, location=mydevice['location'], piholestatus=my_piholestatus, vpnstatus=my_vpnstatus, )

@app.route('/enable_pihole')
def enable_pihole():
        global my_inventory
        mydevice = getLocation(my_inventory,request.remote_addr)
        apiEnablePihole(mydevice,request.remote_addr)
        pihole_mystatus = apiCheckPihole(mydevice,request.remote_addr)
        my_piholestatus  = piholeStatusSTR(pihole_mystatus)
        vpn_mystatus = apiCheckVpn(mydevice,request.remote_addr)
        my_vpnstatus  = vpnStatusSTR(vpn_mystatus)

        return render_template('ok.html', title='Welcome', ip=request.remote_addr , piholestatus=my_piholestatus, vpnstatus=my_vpnstatus, )

@app.route('/disable_pihole')
def disable_pihole():
        mydevice = getLocation(my_inventory,request.remote_addr)
        apiDisablePihole(mydevice,request.remote_addr,False)
        pihole_mystatus = apiCheckPihole(mydevice,request.remote_addr)
        my_piholestatus  = piholeStatusSTR(pihole_mystatus)
        vpn_mystatus = apiCheckVpn(mydevice,request.remote_addr)
        my_vpnstatus  = vpnStatusSTR(vpn_mystatus)

        return render_template('ok.html', title='Welcome', ip=request.remote_addr , piholestatus=my_piholestatus, vpnstatus=my_vpnstatus, )

@app.route('/disable_pihole_forever')
def disable_pihole_forever():
        mydevice = getLocation(my_inventory,request.remote_addr)
        apiDisablePihole(mydevice,request.remote_addr,True)
        pihole_mystatus = apiCheckPihole(mydevice,request.remote_addr)
        my_piholestatus  = piholeStatusSTR(pihole_mystatus)
        vpn_mystatus = apiCheckVpn(mydevice,request.remote_addr)
        my_vpnstatus  = vpnStatusSTR(vpn_mystatus)

        return render_template('ok.html', title='Welcome', ip=request.remote_addr , piholestatus=my_piholestatus, vpnstatus=my_vpnstatus, )

@app.route('/enable_vpn')
def enable_vpn():
        global my_inventory
        mydevice = getLocation(my_inventory,request.remote_addr)
        apiEnableVpn(mydevice,request.remote_addr)
        pihole_mystatus = apiCheckPihole(mydevice,request.remote_addr)
        my_piholestatus  = piholeStatusSTR(pihole_mystatus)
        vpn_mystatus = apiCheckVpn(mydevice,request.remote_addr)
        my_vpnstatus  = vpnStatusSTR(vpn_mystatus)

        return render_template('ok.html', title='Welcome', ip=request.remote_addr , piholestatus=my_piholestatus, vpnstatus=my_vpnstatus, )

@app.route('/disable_vpn')
def disable_vpn():
        mydevice = getLocation(my_inventory,request.remote_addr)
        apiDisableVpn(mydevice,request.remote_addr)
        pihole_mystatus = apiCheckPihole(mydevice,request.remote_addr)
        my_piholestatus  = piholeStatusSTR(pihole_mystatus)
        vpn_mystatus = apiCheckVpn(mydevice,request.remote_addr)
        my_vpnstatus  = vpnStatusSTR(vpn_mystatus)

        return render_template('ok.html', title='Welcome', ip=request.remote_addr , piholestatus=my_piholestatus, vpnstatus=my_vpnstatus, )

@app.route('/router_boot_update')
def router_boot_update():
        device = router_bootCheck(my_inventory,request.remote_addr)
        if device:
                os.system(f"python3 {main_auto_py_exec} {device['name']} &")
                return 'ok'
        else:
                return 'device_not_found'




def piholeStatusSTR(pihole_mystatus):
        if pihole_mystatus:
                return "Off ❌"
        else:
                return "On ✅"

def vpnStatusSTR(vpn_mystatus):
        if vpn_mystatus:
                return "On 🚀"
        else:
                return "Off 👀"
                

if debugmode:
        app.run(host='0.0.0.0', port=8080)








application = app