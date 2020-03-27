#!/usr/local/bin/python3

import requests
# import sys
import os
# import logging
import tempfile
import re
import argparse
import csv
from itertools import cycle

# Requires dns.resolver from dnspython package
from dns.resolver import Resolver
from dns.resolver import NoAnswer, NXDOMAIN, NoNameservers, Timeout

# Requires urlparse to extract paths and qs from file
from urllib.parse import urlparse
import shlex
import subprocess
# import multiprocessing
import pprint


FILENAME = "prewarm_urls.py"

# Name of known public nameservers public CSV file
DEFAULT_NS_URL = "https://public-dns.info/nameservers.csv"

# Column headers containing DNS IP address and country code within the CSV
CSV_COL_IP = "ip"
CSV_COL_COUNTRY = "country_id"

# ISO Country Codes from EU
EU_COUNTRIES_ISO = ['AL', 'AD', 'AT', 'BY', 'BE', 'BA', 'BG', 'HR', 'CY', 'CZ',
                    'DK', 'EE', 'FO', 'FI', 'FR', 'DE', 'GI', 'GR', 'HU', 'IS',
                    'IE', 'IM', 'IT', 'RS', 'LV', 'LI', 'LT', 'LU', 'MK', 'MT',
                    'MD', 'MC', 'ME', 'NL', 'NO', 'PL', 'PT', 'RO', 'RU', 'SM',
                    'RS', 'SK', 'SI', 'ES', 'SE', 'CH', 'UA', 'GB', 'VA', 'RS']


CURL_COMMAND = '''/usr/local/bin/curl -s -D - -o /dev/null -H "Pragma:akamai-x-get-extracted-values,akamai-x-cache-on,akamai-x-cache-remote-on,akamai-x-check-cacheable,akamai-x-get-cache-key,akamai-x-get-true-cache-key,akamai-x-get-request-id" '''

PATH = os.path.dirname(os.path.abspath(__file__))


class HostnameEdgeMaps(object):

    def __init__(self, hostname, max_edges, ns_url=None):
        self.edge_maps = set({})
        self.hostname = hostname
        self.max_ips = max_edges
        if ns_url is None:
            self.ns_url = DEFAULT_NS_URL
        else:
            self.ns_url = ns_url

    def add_map(self, ip_address):
        self.edge_maps.add(ip_address)

    def remove_map(self, ip_address):
        self.edge_maps.discard(ip_address)

    def get_all_maps(self):
        return list(self.edge_maps)

    def generate_geo_edges(self, dns_file_name=None):
        if dns_file_name is None:
            response = requests.get(self.ns_url)
            response.raise_for_status()
            temp_csv = tempfile.NamedTemporaryFile(suffix=".csv")
            for chunk in response.iter_content(100000):
                temp_csv.write(chunk)
            local_csv_file = temp_csv.name
        else:
            local_csv_file = dns_file_name

        with open(local_csv_file) as csv_file:
            csv_reader = csv.DictReader(csv_file)
            ip_pattern = re.compile(r"""(?:^|\b(?<!\.))(?:1?\d\d?|2[0-4]\d|
                                         25[0-5])(?:\.(?:1?\d\d?|2[0-4]\d|
                                         25[0-5])){3}(?=$|[^\w.])""",
                                    re.VERBOSE)

            for row in csv_reader:
                if (ip_pattern.match(row[CSV_COL_IP]) and
                        (str(row[CSV_COL_COUNTRY]) in EU_COUNTRIES_ISO)):
                    mapped_ip = get_ip_from_nameserver(
                        self.hostname, row[CSV_COL_IP])

                    if mapped_ip is not None:
                        edgemaps.add_map(mapped_ip)
                        if len(self.edge_maps) >= self.max_ips:
                            break

            csv_file.close()

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


def do_curl(edge_ip, full_url):

    final_curl = " ".join(
        [CURL_COMMAND, "--connect-to ::" + edge_ip, full_url])
    # print(final_curl)
    args = shlex.split(final_curl)
    p = subprocess.Popen(args, universal_newlines=True)
    output, error = p.communicate()
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Process command line options',
        usage="""Usage: {} (-f <input_file> | --file=<input file>)
                (-d <hostname> |--hostname <hostname>)""".format(FILENAME))

    parser.add_argument('--hostname', '-d', action='store', required=True,
                        help='hostname to generate edge maps from region.')

    parser.add_argument('--inputfile', '-f', action='store', required=True,
                        help='file with images to prewarm')

    parser.add_argument('--max_edges', '-n', type=int, action='store',
                        default=20,
                        help='number of edge ip maps for the hostname')

    args = parser.parse_args()

    edgemaps = HostnameEdgeMaps(args.hostname, args.max_edges)
    edgemaps.generate_geo_edges('nameservers.csv')

    # Declare cycle object from itertools to loop over the edge mapped IPs
    edge_maps_cycle = cycle(edgemaps.get_all_maps())

    # print("Number of CPUs: {}".format(multiprocessing.cpu_count()))
    # p = multiprocessing.Pool(multiprocessing.cpu_count() - 1)

    with open(args.inputfile) as url_file:
        for url_line in url_file:
            # Skip comment lines from input file
            if not url_line.lstrip().startswith("#"):
                # Parse URLs removing new lines characters from current line
                u = urlparse(url_line.strip())
                # Include query string if present in the final path
                fullpath = u.path + "?" + u.query if u.query else u.path
                full_url = "https://" + args.hostname + "/" + fullpath
                # get next edge mapped IP from all maps
                ip_address = next(edge_maps_cycle)
                print("Run do_curl with IP address {} and URL: {}".format(
                    ip_address, full_url)
                do_curl(ip_address, full_url)