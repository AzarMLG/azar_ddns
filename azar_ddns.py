#!/usr/bin/env python3
import configparser
import subprocess
import requests
import platform
import ipaddress

current_os : str = platform.system()
supported_os : str = ["Linux", "Darwin"]

config_path : str = "./azar_ddns.ini"

debug_turn_off_dns_update : bool = True # if debuging can set this to True to not mess with dns

def read_config():
    config = configparser.ConfigParser()
    config.read(config_path)
    return config['DDNS']

def get_shell_command_output(command):
    return subprocess.check_output(command, shell=True, executable="/bin/bash").decode().strip()

def get_ipv6(link):
    if current_os == "Linux":
        command = "ip -6 addr show dev " + link + " | grep -m 1 -oP 'inet6 \\K[0-9a-fA-F:]+/[0-9]+ scope global (?!temporary|deprecated)' | awk -F""/"" '{print $1}'"
        return get_shell_command_output(command)
    elif current_os == "Darwin":
        command = "ifconfig " + link + " | awk '/inet6/{print $2}' | grep -m 1 -v 'fe80::'"
        return get_shell_command_output(command)
    else:
        raise NotImplementedError(f"Unsupported operating system: {current_os}")

        
def get_ipv6_darwin(link):
    return get_ipv6(link)

def get_dns_record(name):
    command = f"dig aaaa {name} +short"
    return  get_shell_command_output(command)

def update_ddns(ipv6, token, name, zone_id, account_id):
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{account_id}"

    payload = {
    "content": ipv6,
    "name": name,
    "proxied": False,
    "type": "AAAA",
    "ttl": 1
    }
    headers = {
        "Content-Type": "application/json",
        "X-Auth-Email": token #TODO fix this
    }

    response = requests.request("PUT", url, json=payload, headers=headers)
    #TODO check if response is succesful, if not return error
    print(response.text)
    

if __name__ == "__main__":
    if current_os not in supported_os:
        raise NotImplementedError(f"Unsupported operating system: {current_os}")

    config_data = read_config()
    
    link = config_data['link']
    name = config_data['name']
    
    ipv6_str : str = get_ipv6(link)
    ipv6_address : ipaddress.IPv6Address = None

    try:
        ipv6_address = ipaddress.IPv6Address(ipv6_str)
    except ipaddress.AddressValueError:
        print(f"ipv6_str = \"{ipv6_str}\"")
        print("Looks like this host does not have ipv6 address set. Exiting...")
        exit(1)
    except Exception as e:
        print(f"Could not convert {ipv6_str} to valid ipv6 address: {e}. Exiting...")
        exit(1)

    if ipv6_address.is_global:    
        print(f"host address is: {ipv6_str}")
        dns = get_dns_record(name)
        print(f"aaaa dns record is: {dns}")

        if ipv6_str == dns:
            print("No ddns update required. Exiting...")
            exit(0)
        elif debug_turn_off_dns_update:
            pass
        else:
            token = config_data['token']
            zone_id = config_data['zone_id']
            account_id = config_data['account_id']
            update_ddns(ipv6_str, token, name, zone_id, account_id)
            print(f"ddns updated {dns} >> {ipv6_str}")
    else:
        print(f"{ipv6_str} is not global ipv6 address. Exiting...")
        