#!/usr/bin/env python3
import configparser
import subprocess
import requests

config_path : str = "./azar_ddns.ini"


def read_config():
    config = configparser.ConfigParser()
    config.read(config_path)
    return config['DDNS']

def get_shell_command_output(command):
    return subprocess.check_output(command, shell=True, executable="/bin/bash").decode().strip()

def get_ipv6(link):
    command = "ip -6 addr show dev " + link + " | grep -m 1 -oP 'inet6 \K[0-9a-fA-F:]+/[0-9]+ scope global (?!temporary|deprecated)' | awk -F""/"" '{print $1}'"
    return get_shell_command_output(command)

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
        "X-Auth-Email": token
    }

    response = requests.request("PUT", url, json=payload, headers=headers)
    print(response.text)
    

if __name__ == "__main__":
    config_data = read_config()
    
    link = config_data['link']
    name = config_data['name']
    
    ipv6 = get_ipv6(link)
    print(f"host address is: {ipv6}")
    dns = get_dns_record(name)
    print(f"aaaa dns record is: {dns}")

    if ipv6 == dns:
        print("No ddns update required. Exiting...")
        exit(0)
    else:
        token = config_data['token']
        zone_id = config_data['zone_id']
        account_id = config_data['account_id']
        update_ddns(ipv6, token, name, zone_id, account_id)
        print(f"ddns updated {dns} >> {ipv6}")
        