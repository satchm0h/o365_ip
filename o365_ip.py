#!/bin/env python3

import os
import sys
import json
import uuid
import argparse
import logging
import coloredlogs
import requests

# Defining the default values that can be overridden on the CLI
DEFAULTS = {
    'guidfile': 'client-guid',
    'outfile': 'last-dump',
    'verfile': 'last-version',
    'instance': 'Worldwide'
}


def main(options):
    # Lets make do stuff. See init at the bottom for the 'options' logic
    logging.info('Starting')

    if options.force:
        if options.deltafile:
            if os.path.isfile(options.deltafile):
                os.remove(options.deltafile)
        if os.path.isfile(options.verfile):
            os.remove(options.verfile)
        if os.path.isfile(options.outfile):
            os.remove(options.outfile)

    # If we are doing a delta, wipe any previous delta file
    if options.deltafile is not None:
        write_json_file(options.deltafile, {})

    # If there is no update we are done, unless forced
    (new_version, previous_version) = get_versions(options.version_url,
                                                   options.verfile)
    if new_version == previous_version:
        logging.info('Version matches previous. No update')
        sys.exit(0)

    # Download and process the latest IPs
    ip_struct = get_ip_addresses(options.data_url, options.optional)

    # Calcualte delta if we are asked to do so
    if options.deltafile is not None:
        generate_delta(ip_struct, options.outfile, options.deltafile)
        logging.info(f'Delta File: {options.deltafile}')

    # Dump the latest results to disk
    write_json_file(options.outfile, ip_struct, True)
    commit_processed_version(options.verfile, new_version)
    logging.info(f'Output File: {options.outfile}')
    logging.info('Complete!')


def write_json_file(filename, data, pretty=False):
    # Dump a python data structure to JSON FILE
    logging.debug(f'Writing JSON File : {filename}')
    with open(filename, 'w') as file_handle:
        if pretty:
            json.dump(data, file_handle, indent=2)
        else:
            json.dump(data, file_handle)


def get_versions(url, filename):
    # Here we want to determinge if there is a new version to process or not
    previous_version = "42"
    logging.debug('Downloading Version Information')
    current_version = get_version_info(url)

    # If we've run before, read in the version last processed
    if os.path.isfile(filename):
        previous_version = read_single_state(filename)

    if current_version == previous_version:
        logging.debug(f'No version change: {current_version}')
    else:
        logging.debug(f'New version discovered: {current_version}')

    return (current_version, previous_version)


def commit_processed_version(filename, version):
    # Write out the version we have finished processing
    logging.debug(f'Writing last processed version to: {filename}')
    write_single_state(filename, version)


def get_version_info(url):
    version_info = requests.get(url).json()
    if 'latest' in version_info:
        return version_info['latest']
    return None


def read_single_state(filename):
    logging.debug(f'Read state file: {filename}')
    with open(filename, 'r') as file_handle:
        return file_handle.readline().rstrip()


def write_single_state(filename, value):
    logging.debug(f'Write state file: {filename}')
    with open(filename, 'w') as file_handle:
        print(value, file=file_handle)


def generate_delta(data, filename, deltafile):
    logging.debug('Generating Delta')
    delta = {'add': [], 'remove': []}
    previous = {}

    # If there is a previous run, lets load it.
    if os.path.isfile(filename):
        with open(filename, 'r') as file_handle:
            previous = json.load(file_handle)

    # Find new additions
    for ip in data:
        if ip not in previous:
            delta['add'].append(ip)

    # Find removals
    for ip in previous:
        if ip not in data:
            delta['remove'].append(ip)

    # Write out the Delta
    write_json_file(deltafile, delta, True)


def init_deltafile(filename):
    logging.debug(f'Initializing Delta File : {filename}')
    if os.path.isfile(filename):
        with open(filename, 'w') as file_handle:
            # Empty object in-case there are no changes
            print('{}', file=file_handle)


def get_ip_addresses(url, include_optional):
    logging.debug(f'Include optional IPs: {include_optional}')
    # We are going to accumualte IPs in dicts to de-dup
    ips = {}
    records = requests.get(url).json()
    for record in records:
        if 'ips' in record:
            for ip in record['ips']:
                if record['required']:
                    ips[ip] = 42
                elif include_optional:
                    ips[ip] = 42
    return ips


def init():
    '''
        init()
        Handle command line args, setup log, etc..
    '''
    global DEFAULTS

    # Configure log
    coloredlogs.install(level='DEBUG',
                        fmt='%(asctime)s %(levelname)s %(message)s')

    # Supress requests log
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    # Handle command line args
    parser = argparse.ArgumentParser(
        description='Get Microsoft Office 365 IP lists.')
    parser.add_argument('-D, --debug', dest='debug',
                        help='Full download output',
                        action='store_true')
    parser.add_argument('-f, --force', dest='force',
                        help='Download update even if version has not changed',
                        action='store_true')
    parser.add_argument('-o, --outfile', dest='outfile',
                        help='Full download output',
                        default=DEFAULTS['outfile'])
    parser.add_argument('-v, --verfile', dest='verfile',
                        help='File to store version infomation',
                        default=DEFAULTS['verfile'])
    parser.add_argument('-d, --deltafile', dest='deltafile',
                        help='Generate delta to file',
                        default=None)
    parser.add_argument('-g, --guidfile', dest='guidfile',
                        help='File to load guid from. Will generate if file not found',
                        default=DEFAULTS['guidfile'])
    parser.add_argument('-i, --instance', dest='instance',
                        help='Microsoft Office 365 Instance',
                        choices=['Worldwide', 'China', 'Germany',
                                 'USGovDoD', 'USGovGCCHigh'],
                        default=DEFAULTS['instance'])
    parser.add_argument('-p, --disable_optional_ips', dest='optional',
                        help="Do not include optional IPs",
                        action='store_false')
    options = parser.parse_args()

    # Enable debug
    if not options.debug:
        coloredlogs.decrease_verbosity()

    # Read client guid from file or generate and write to file for
    # subsequent runs. Not Microsoft asks for a unique UUID per "system" that
    # accesses the API
    if os.path.isfile(options.guidfile):
        options.client_guid = read_single_state(options.guidfile)
    else:
        options.client_guid = uuid.uuid4()
        write_single_state(options.guidfile, options.client_guid)

    # Build the URLs based on the Instance selection and our guid
    base_url = 'https://endpoints.office.com'
    options.version_url = f'{base_url}/version/{options.instance}/?clientrequestid={options.client_guid}'
    options.data_url = f'{base_url}/endpoints/{options.instance}/?clientrequestid={options.client_guid}'

    return options


if __name__ == '__main__':
    main(init())
