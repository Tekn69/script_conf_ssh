import threading
import time
from netmiko import ConnectHandler, NetMikoTimeoutException
from ipaddress import ip_network
import concurrent.futures
from colorama import init
from paramiko.ssh_exception import SSHException, AuthenticationException
from termcolor import colored
import getpass
import os
import dns.exception
from dns.resolver import Resolver
from io import *
import sys
import string

def dns_lookup(input, timeout=3, server=[]):
	"""
	  Perform a simple DNS lookup, return results in a dictionary
	"""
	resolver = Resolver()
	resolver.timeout = float(timeout)
	resolver.lifetime = float(timeout)

	result = {}

	if server:
		resolver.nameservers = server
	try:
		records = resolver.resolve(input)
		result = {
			"addrs": [ii.address for ii in records],
			"error": "",
			"name": input,
		}
	except dns.resolver.NXDOMAIN as e:
		result = {
			"addrs": [],
			"error": f"No such domain {input}",
			"name": input,
		}
	except dns.resolver.Timeout:
		result = {
			"addrs": [],
			"error": f"Timed out while resolving {input}",
			"name": input,
		}
		# print(f"Timed out while resolving {input}")
	except dns.exception.DNSException as e:
		result = {
			"addrs": [],
			"error": f"Unhandled exception ({repr(e)})",
			"name": input,
		}
		# print("Unhandled exception")

	return result


def ping(ip_addr):
	response = "".join(os.popen(f"ping -n 2 -w 2000 {ip_addr}").readlines())
	if "TTL=" not in response:
		inactive_hosts.append(ip_addr)
	else:
		active_hosts.append(ip_addr)


def error(error_message: str):
	init()
	print(colored(error_message, 'red'))
	connected = False


def save_log(log_bytes: BufferedIOBase):
	with lock:
		log_bytes.seek(0)
		lecture_log = log_bytes.read()
		log_str = lecture_log.decode()
		with open(log_path, 'a') as f:
			f.write(log_str+"\n\n\nNew Connection\n\n")


def conf_ssh(host):
	try:  # si pas d'erreur

		net_connect = ConnectHandler(**devices[host])  # debut de la connexion
		try:
			net_connect.disable_paging()

			if not net_connect.check_enable_mode():  # auto enable
				net_connect.enable()

			if not net_connect.check_config_mode():  # auto conf t
				net_connect.config_mode()

			output = ""

			tmp=net_connect.send_config_set(commands)
			output += net_connect.find_prompt() + " " + tmp + "\n"

			print(f'======= IP: {host} ==========\n' + output + '\n==================================== \n')

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

mode = input("Discovery mode ? yes/no : ").lower()
if mode == "yes":
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

else:
	active_hosts = input("list of equipment (format IP,FQDN,IP...) : ").split(",")
	resolver = dns.resolver.Resolver()

	for i in range(len(active_hosts)):

		for car in active_hosts[i]:
			if car in string.ascii_letters:

				reponse=dns_lookup(active_hosts[i])
				if reponse['error'] != '':
					error(reponse['error'])
					sys.exit(0)

				active_hosts[i] = reponse['addrs'][0]
				break

	count = len(active_hosts)


# recuperation des informations
device_type = input("Device_type : ")

port = input('tcp port (press enter for 22) : ')

while not port.isdigit() or port == '':
	if port == '':
		port = '22'
	else:
		print('incorrect input')
		port = input('tcp port (press enter for 22) : ')

port = int(port)

username = input("login: ")
passwd = getpass.getpass("password: ")


# stockage des log dans une string pour chaque thread
log_strIO = {}
for ip in active_hosts:
	log_strIO[ip] = BufferedRandom(BytesIO())

devices = {}
for ip in active_hosts:
	devices[ip] = {
		"device_type": device_type,
		"host": ip,
		"username": username,
		"password": passwd,
		"keepalive": 5,
		"session_log": log_strIO[ip],
		"port" : port
	}

file = input("Path to configuration file: ")

with open(file, "r") as cfg_file:
	commands = cfg_file.read().split('\n')
	if commands[-1] == '':
		del(commands[-1])

print("File opened successfully\n")

print("Start of configuration\n")

connexions_ssh = []

executor = concurrent.futures.ThreadPoolExecutor(count)
ssh_hosts = concurrent.futures.wait([executor.submit(conf_ssh, host) for host in active_hosts],
									return_when="ALL_COMPLETED")

print("End of configuration")

if connexions_ssh != []:

	reponse = input("Do you want to save configuration ? (yes/no): ")

	while reponse not in ["yes", "no"]:
		print("Invalid value")
		reponse = input("Do you want to save configuration ? (yes/no): ")

	if reponse == "yes":
		executor = concurrent.futures.ThreadPoolExecutor(count)
		save_ssh = concurrent.futures.wait([executor.submit(save_ssh, connexion) for connexion in connexions_ssh],
										   return_when="ALL_COMPLETED")
	else:
		disconnect_ssh()

lock = threading.Lock()

if not os.path.exists("logs"):
	os.makedirs("logs")

log_path = os.path.join("logs", f"DEBUG-{time.strftime('%Y%m%d_%H%M%S')}.log")

f = open(log_path, "w")
f.write(f"New Session\n\n")
f.close()

for ip in active_hosts:
	save_log(log_strIO[ip])

print("End of script")
