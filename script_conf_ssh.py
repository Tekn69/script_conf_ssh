from netmiko import *
import logging
import subprocess
from ipaddress import ip_address, ip_network
import concurrent.futures
from getpass4 import getpass
from colorama import init
from paramiko.ssh_exception import SSHException, AuthenticationException
from termcolor import colored
import os


def ping(ip_addr):
    requete = os.popen(f"ping -n 2 -w 2000 {ip_addr}")
    response = "".join(requete.readlines())
    if "TTL=" not in response:
        inactive_hosts.append(ip_addr)
    else:
        active_hosts.append(ip_addr)

def error(error_message : str):
    init()
    print(error_message)
    connected = False



def conf_ssh(host):
    try:  # si pas d'erreur

        net_connect =  ConnectHandler(**devices[host])  # debut de la connexion
        try:
            net_connect.disable_paging()

            if not net_connect.check_enable_mode():  # auto enable
                net_connect.enable()

            if not net_connect.check_config_mode():  # auto conf t
                net_connect.config_mode()

            output = net_connect.send_config_from_file(file)

            print(f'======= IP: {host} ==========\n'+output+'\n==================================== \n')

            connexions_ssh.append(net_connect)

        except NetMikoTimeoutException:
            error(f'Connection timeout while executing commands: {host}')
        except EOFError:
            error(f'End of File while attempting device: {host}')
        except SSHException:
            error(f'SSH issue while executing commands: {host}')
        except Exception as unknown_error:
            error(f'Some other error while executing commands: {host} {unknown_error.__str__()}')


    except AuthenticationException:
        error(f'Authentication failure: {host}')
    except NetMikoTimeoutException:
        error(f'Connection timeout: {host}')
    except EOFError:
        error(f'End of File while attempting device: {host}')
    except SSHException:
        error(f'SSH issue while trying to connect to {host}')
    except Exception as unknown_error:
        error(f'Some other error while trying to connect to {host}: {unknown_error.__str__()}')


def save_ssh(connexion):
    try:
        connexion.save_config()
        print(f'Successfully saved: {connexion.host}')
        connexion.disconnect()
    except NetMikoTimeoutException:
        error(f'Connection timeout while saving: {connexion.host}')
    except EOFError:
        error(f'End of File while saving: {connexion.host}')
    except SSHException:
        error(f'SSH issue while while saving: {connexion.host}')
    except Exception as unknown_error:
        error(f'Some other error while saving: {connexion.host} {unknown_error.__str__()}')


def disconnect_ssh():
    for connexion in connexions_ssh:
        try:
            connexion.disconnect()
        except:
            pass


network = ip_network(input("\nNetwork address (IP/CIDR) : "))
hosts = network.hosts()
count = len(list(network.hosts()))
active_hosts = []
inactive_hosts = []

print("\nRecovering IPs from the network...")


executor = concurrent.futures.ThreadPoolExecutor(count)
ping_hosts = concurrent.futures.wait([executor.submit(ping, str(ip)) for ip in hosts], return_when="ALL_COMPLETED")

print("Recovery completed\n")
print(f'IP detected: {active_hosts}\n')

# exclusion de certaines IP
for ip in input("IP to exclude (format IP,IP...) : ").split(","):
    if ip in active_hosts:
        del active_hosts[active_hosts.index(ip)]

# recuperation des informations
device_type = input("Device_type (extreme_exos, extreme_vsp): ")
username = input("login: ")
passwd = getpass("password: ")

devices = {}
for ip in active_hosts:
    devices[ip] = {
        "device_type": device_type,
        "host": ip,
        "username": username,
        "password": passwd,
        "keepalive": 5
    }

#A decommenter en cas de probleme
#logging.basicConfig(filename=f'debug.log', level=logging.DEBUG)
#logger = logging.getLogger("netmiko")

file = input("Path to configuration file: ")

print("File opened successfully\n")

print("Start of configuration\n")

connexions_ssh = []

executor = concurrent.futures.ThreadPoolExecutor(count)
ssh_hosts = concurrent.futures.wait([executor.submit(conf_ssh, host) for host in active_hosts],
                                     return_when="ALL_COMPLETED")

print("End of configuration")

reponse = input("Do you want to save configuration ? (yes/no): ")

while reponse not in ["yes", "no"]:
    print("Invalid value")
    reponse = input("Do you want to save configuration ? (yes/no): ")

if reponse == "yes":
    executor = concurrent.futures.ThreadPoolExecutor(count)
    save_ssh = concurrent.futures.wait([executor.submit(save_ssh,connexion) for connexion in connexions_ssh],
                                        return_when="ALL_COMPLETED")
else:
    disconnect_ssh()

