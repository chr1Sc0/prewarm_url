#!/usr/local/bin/python

import requests
import os
import bs4
import threading
import csv
import socket
import dns.resolver
import re

CSV_COL_IP = "ip"
CSV_COL_COUNTRY = "country_id"
TARGET_HOSTNAME = 'static.zara.net'
EU_COUNTRIES_ISO = ['AL', 'AD', 'AT', 'BY', 'BE', 'BA', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FO', 'FI', 'FR', 'DE', 'GI', 'GR', 'HU', 'IS', 'IE', 'IM', 'IT',
                    'RS', 'LV', 'LI', 'LT', 'LU', 'MK', 'MT', 'MD', 'MC', 'ME', 'NL', 'NO', 'PL', 'PT', 'RO', 'RU', 'SM', 'RS', 'SK', 'SI', 'ES', 'SE', 'CH', 'UA', 'GB', 'VA', 'RS']


def download_ns_file(url):
    print('Downloading CSV file...')
    response = requests.get(url)
    response.raise_for_status()
    csvfile = open('nameservers.csv', 'wb')
    for chunk in response.iter_content(100000):
        csvfile.write(chunk)
    csvfile.close
    print('nameservers file downloaded')


def extract_dns_servers(dnsfile):
    with open(dnsfile) as csv_file:
        csv_reader = csv.DictReader(csv_file)

        ip_pattern = re.compile(
            '(?:^|\b(?<!\.))(?:1?\d\d?|2[0-4]\d|25[0-5])(?:\.(?:1?\d\d?|2[0-4]\d|25[0-5])){3}(?=$|[^\w.])')

        line_count = 0
        edge_count = 0

        for row in csv_reader:
            if line_count > 0:
                if ip_pattern.match(row[CSV_COL_IP]) and str(row[CSV_COL_COUNTRY]) in EU_COUNTRIES_ISO:
                    mapped_ip = check_nameserver_ip(
                        row[CSV_COL_IP], TARGET_HOSTNAME)
                    if mapped_ip is not None:
                        print(
                            f'{row[CSV_COL_IP]},{row[CSV_COL_COUNTRY]},{mapped_ip}')
                        edge_count += 1

            line_count += 1
        print(f'There are {edge_count} Edge IPs for this hostname in .')


def check_nameserver_ip(dns_ip, hostname):
    # Set the DNS Server
    from dns.resolver import NoAnswer, NXDOMAIN, NoNameservers, Timeout

    a_records = []

    resolver = dns.resolver.Resolver()
    resolver.nameservers = [socket.gethostbyname(dns_ip)]
    resolver.timeout = 1
    resolver.lifetime = 1
    try:
        for rdata in resolver.query(hostname, 'A'):
            a_records.append(str(rdata))

    except NoAnswer:
        return None
    except NXDOMAIN:
        return None
    except NoNameservers:
        return None
    except Timeout:
        return None
    return(a_records[0])


if __name__ == "__main__":

    url = "https://public-dns.info/nameservers.csv"
    download_ns_file(url)
    extract_dns_servers('nameservers.csv')
