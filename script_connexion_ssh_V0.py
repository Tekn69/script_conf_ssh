from netmiko import *
import logging
import subprocess
from ipaddress import ip_address, ip_network
import concurrent.futures
from getpass4 import getpass
from colorama import init
from termcolor import colored
import os


def ping(ip_addr):
    requete = os.popen(f"ping -n 2 -w 2000 {ip_addr}")
    response = "".join(requete.readlines())
    if "TTL=" not in response:
        inactive_hosts.append(ip_addr)
    else:
        active_hosts.append(ip_addr)


def conf_ssh(host):
    device["host"] = host
    try:  # si pas d'erreur

        print(f"Connecté à {host}\n")

        net_connect = ConnectHandler(**device)  # debut de la connexion
        net_connect.disable_paging()

        if not net_connect.check_enable_mode():  # auto enable
            net_connect.enable()

        if not net_connect.check_config_mode():  # auto conf t
            net_connect.config_mode()

        output = net_connect.find_prompt() + net_connect.send_config_set(commandes)

        print(host,output)  # print output dans la console

        connexions_ssh.append(net_connect)

    except Exception as error:
        init()
        print(colored(f"{host} : erreur {type(error).__name__}\n", 'red'))


def save_ssh():
    for connexion in connexions_ssh:
        try:
            connexion.save_config()
            print(f'Sauvegarde réussie: {connexion.host}')
            connexion.disconnect()
        except Exception as error:
            init()
            print(colored(f"{connexion.host} : erreur lors de la sauvegarde {type(error).__name__}\n", 'red'))


def disconnect_ssh():
    for connexion in connexions_ssh:
        try:
            connexion.disconnect()
        except:
            pass


network = ip_network(input("Network address (IP/CIDR) : "))
hosts = network.hosts()
count = len(list(network.hosts()))
active_hosts = []
inactive_hosts = []

print("Récupération des IP présentes sur le réseau en cours...")


executor = concurrent.futures.ThreadPoolExecutor(count)
ping_hosts = concurrent.futures.wait([executor.submit(ping, str(ip)) for ip in hosts], return_when="ALL_COMPLETED")

print("Récupération terminée\n")
print(f'Voici la liste des IP détectées: {active_hosts}\n')

# exclusion de certaines IP
for ip in input("IP a exclure (format attendu ip,ip...) : ").split(","):
    if ip in active_hosts:
        del active_hosts[active_hosts.index(ip)]

# recuperation des informations
device = {
    "device_type": input("Type de device (extreme_exos, extreme_vsp): "),
    "host": "",  # ne rien mettre
    "username": input("login: "),
    "password": getpass("password: "),
    "session_log": "debug.log"
}

logging.basicConfig(filename=f'debug.log', level=logging.DEBUG)  # fichier de log en cas de problemes
logger = logging.getLogger("netmiko")

config = input("chemin relatif vers le fichier de conf: ")

with open(config, "r") as conf:  # ouverture + lecture du fichier de conf
    commandes = conf.readlines()

print("ouverture du fichier réussie\n")

print("Début des connexions ssh...\n")

connexions_ssh = []

for host in active_hosts:
    conf_ssh(host)

print("Fin de configuration")

reponse = input("Voulez-vous sauvegarder ? (oui/non): ")

while reponse not in ["oui", "non"]:
    print("Réponse invalide")
    reponse = input("Voulez-vous sauvegarder ? (oui/non): ")

if reponse == "oui":
    save_ssh()
    print("Sauvegarde terminée")
else:
    disconnect_ssh()

print("Fin des connexions ssh")

