#!/usr/local/bin/python

import requests
import sys
import os
import tempfile
import re
import argparse
import csv
from dns.resolver import Resolver
from dns.resolver import NoAnswer, NXDOMAIN, NoNameservers, Timeout
import threading
from subprocess import Popen, PIPE, STDOUT
import pprint

DEFAULT_NS_URL = "https://public-dns.info/nameservers.csv"
CSV_COL_IP = "ip"
CSV_COL_COUNTRY = "country_id"
EU_COUNTRIES_ISO = ['AL', 'AD', 'AT', 'BY', 'BE', 'BA', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FO', 'FI', 'FR', 'DE', 'GI', 'GR', 'HU', 'IS', 'IE', 'IM', 'IT',
                    'RS', 'LV', 'LI', 'LT', 'LU', 'MK', 'MT', 'MD', 'MC', 'ME', 'NL', 'NO', 'PL', 'PT', 'RO', 'RU', 'SM', 'RS', 'SK', 'SI', 'ES', 'SE', 'CH', 'UA', 'GB', 'VA', 'RS'
                    ]
PATH = os.path.dirname(os.path.abspath(__file__))


class HostnameEdgeMaps(object):

    def __init__(self, hostname, ns_url=None):
        self.edge_maps = set({})
        self.hostname = hostname
        if ns_url is None:
            self.ns_url = DEFAULT_NS_URL
        else:
            self.ns_url = ns_url

    def add_map(self, ip_address):
        self.edge_maps.add(ip_address)

    def remove_map(self, ip_address):
        self.edge_maps.discard(ip_address)

    def get_all_maps(self):
        return self.edge_maps

    def generate_geo_edges(self, dns_file_name=None):
        if dns_file_name is None:
            print('Downloading CSV file...')
            response = requests.get(self.ns_url)
            response.raise_for_status()
            temp_csv = tempfile.NamedTemporaryFile(suffix=".csv")
            for chunk in response.iter_content(100000):
                temp_csv.write(chunk)
            print('nameservers file downloaded')
            local_csv_file = temp_csv.name
        else:
            local_csv_file = dns_file_name

        with open(local_csv_file) as csv_file:
            csv_reader = csv.DictReader(csv_file)
            ip_pattern = re.compile(
                '(?:^|\b(?<!\.))(?:1?\d\d?|2[0-4]\d|25[0-5])(?:\.(?:1?\d\d?|2[0-4]\d|25[0-5])){3}(?=$|[^\w.])')
            edge_count = 0
            line_count = 0

            for row in csv_reader:
                if line_count > 0:
                    if ip_pattern.match(row[CSV_COL_IP]) and str(row[CSV_COL_COUNTRY]) in EU_COUNTRIES_ISO:
                        #print(row[CSV_COL_IP], row[CSV_COL_COUNTRY])
                        mapped_ip = get_ip_from_nameserver(
                            self.hostname, row[CSV_COL_IP])
                        if mapped_ip is not None:
                            edgemaps.add_map(mapped_ip)
                            edge_count += 1

                line_count += 1

            local_csv_file.close()

            pp = pprint.PrettyPrinter()
            pp.pprint(edgemaps.get_all_maps())


def get_ip_from_nameserver(hostname, dns_ip):

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

    return (a_records[0])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Process command line options.')
    parser.add_argument('--hostname', '-d', action='store',
                        help='hostname to generate ghost maps from region.')
    args = parser.parse_args()

    edgemaps = HostnameEdgeMaps(args.hostname)
    edgemaps.generate_geo_edges('nameservers.csv')

    curl_command = 'curl -k --header "Host: $HOSTNAME" -s -D - -o /dev/null --header "Cookie:cache-warm=true" --header "Pragma:akamai-x-get-extracted-values, akamai-x-cache-on, akamai-x-cache-remote-on, akamai-x-check-cacheable, akamai-x-get-cache-key, akamai-x-get-true-cache-key, akamai-x-get-request-id" -A "Chrome"'
