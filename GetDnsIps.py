#!/usr/local/bin/python

import requests
import os
import bs4
import threading
import csv


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
   csv_reader = csv.reader(csv_file, delimiter=',')
   line_count = 0
   for row in csv_reader:
       if line_count == 0:
           print(f'Column names are {", ".join(row)}')
           line_count += 1
        else:
            print(f'\t{row[0]} works in the {row[1]} department, and was born in {row[2]}.')
            line_count += 1
    print(f'Processed {line_count} lines.')

if __name__ == "__main__":

    url = "https://public-dns.info/nameservers.csv"
    download_ns_file(url)
