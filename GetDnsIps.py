#!/usr/local/bin/python

import requests
import os
import bs4
import threading
import csv
import socket
import dns.resolver

CSV_COL_IP = "ip"
CSV_COL_COUNTRY = "country_id"


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
   line_count = 0
   for row in csv_reader:
       if line_count == 0:
           print(f'Column names are {", ".join(row)}')
           line_count += 1
        else:
            print(f'\t{row[0]} works in the {row[1]} department, and was born in {row[2]}.')
            line_count += 1
    print(f'Processed {line_count} lines.')

def check_nameserver_ip(dns_ip)


   # Set the DNS Server
   resolver = dns.resolver.Resolver()
   resolver.nameservers=[socket.gethostbyname('ns1.cisco.com')]
   for rdata in resolver.query('www.yahoo.com', 'CNAME') :
      print rdata.target


if __name__ == "__main__":

    url = "https://public-dns.info/nameservers.csv"
    download_ns_file(url)
