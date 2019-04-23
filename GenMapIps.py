#!/usr/local/bin/python

import requests
import sys
import os
import re
import argparse
import csv
from dns.resolver import Resolver
from dns.resolver import NoAnswer, NXDOMAIN, NoNameservers, Timeout
import threading
import pprint

NS_URL = "https://public-dns.info/nameservers.csv"
CSV_COL_IP = "ip"
CSV_COL_COUNTRY = "country_id"
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


def generate_geo_edges(dnsfile, target_hostname):
    with open(dnsfile) as csv_file:
        csv_reader = csv.DictReader(csv_file)

        ip_pattern = re.compile(
            '(?:^|\b(?<!\.))(?:1?\d\d?|2[0-4]\d|25[0-5])(?:\.(?:1?\d\d?|2[0-4]\d|25[0-5])){3}(?=$|[^\w.])')

        line_count = 0
        edge_count = 0

        edgemaps = HostnameEdgeMaps(target_hostname)

        for row in csv_reader:
            if line_count > 0:
                if ip_pattern.match(row[CSV_COL_IP]) and str(row[CSV_COL_COUNTRY]) in EU_COUNTRIES_ISO:
                    mapped_ip = check_nameserver_ip(
                        row[CSV_COL_IP], target_hostname)
                    if mapped_ip is not None:
                        edgemaps.add_map(mapped_ip)

                        # print(
                        #    f'{row[CSV_COL_IP]},{row[CSV_COL_COUNTRY]},{mapped_ip}')
                        edge_count += 1

            line_count += 1
        # print(f'There are {edge_count} Edge IPs for this hostname')
        pp = pprint.PrettyPrinter()
        pp.pprint(edgemaps.get_all_maps())


def check_nameserver_ip(dns_ip, hostname):
    # Set the DNS Server

    a_records = []

    resolver = Resolver()
    resolver.nameservers = [dns_ip]
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


class HostnameEdgeMaps(object):

    def __init__(self, hostname):
        self.edge_maps = set({})
        self.hostname = hostname
        # self.region =

    def add_map(self, ip_address):
        # if not ip_address in self.edge_maps[country_id]:
        self.edge_maps.add(ip_address)

        #self.edge_maps.setdefault(country_id, {})[ip_address] = 1
    def remove_map(self, ip_address):
        self.edge_maps.discard(ip_address)

    def get_all_maps(self):
        return self.edge_maps


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Process command line options.')
    parser.add_argument('--hostname', action='store',
                        help='hostname to generate ghost maps from region.')
    # parser.add_argument('--region', '-r', action='store',
    #                    help = '[--region AM|EMEA|AP', default = 'EMEA')
    args = parser.parse_args()

    # download_ns_file(NS_URL)

    generate_geo_edges('nameservers.csv', args.hostname)
