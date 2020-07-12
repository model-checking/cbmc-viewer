#!/usr/bin/env python3

"""Get the last version of a repository in an DockerHub account."""

import argparse
import json
import logging
import subprocess

ACCOUNT = 'markrtuttle'
LATEST = 'latest'
QUERY = 'https://registry.hub.docker.com/v2/repositories/{account}/{repo}/tags'

################################################################

def create_parser():
    parser = argparse.ArgumentParser(
        description='Get last version in a DockerHub repository.'
    )
    parser.add_argument(
        '--account',
        default=ACCOUNT,
        help='DockerHub account.'
    )
    parser.add_argument(
        '--repository',
        required=True,
        help='DockerHub repository (image) in DockerHub account.'
    )
    parser.add_argument(
        '--version-pairs',
        action='store_true',
        help="""
        Versions are expected to version pairs of the form N.M-NN.MM.
        Otherwise versions are expected to simple versions of the form N.M.
        """
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output.'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Debugging output.'
    )
    return parser

################################################################

def configure_logging(verbose, debug):
    if debug:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(levelname)s: %(message)s')
    elif verbose:
        logging.basicConfig(level=logging.INFO,
                            format='%(levelname)s: %(message)s')
    else:
        logging.basicConfig(format='%(levelname)s: %(message)s')

################################################################

VERSION_MAX_LEN = 10

def integer(string):
    try:
        return int(string)
    except ValueError:
        return None

def version_to_integers(string):
    strs = string.split('.')
    ints = integers(strs)
    if ints is None or len(strs) != len(ints) or len(strs) > VERSION_MAX_LEN:
        logging.debug("Expected version to be at most %s integers: %s",
                      VERSION_MAX_LEN, string)
        return None
    return (ints + [0] * VERSION_MAX_LEN)[:VERSION_MAX_LEN]

def filter_versions(versions):
    return [version for version in versions if version_to_integers(version)]

################################################################

def integers(strings):
    try:
        values = [integer(string) for string in strings]
        return None if any([value is None for value in values]) else values
    except TypeError:
        return None

def version_pair_to_integers(string):
    strings = string.split('-')
    if len(strings) != 2:
        logging.debug("Expected version pair: %s", string)
        return None

    values = [version_to_integers(version) for version in strings]
    if any([value is None for value in values]):
        logging.debug("Expected version pair: %s", string)
        return None

    return [val for vals in values for val in vals]

def filter_version_pairs(version_pairs):
    return [version_pair for version_pair in version_pairs
            if version_pair_to_integers(version_pair)]

################################################################

def docker_response(account, repository):
    cmd = ['curl', '-L', QUERY.format(account=account, repo=repository)]
    logging.debug("Query '%s'", ' '.join(cmd))
    data = subprocess.run(cmd, text=True, capture_output=True, check=True)
    logging.debug("Query output: %s", data.stdout)
    return data.stdout

def docker_tags(response):
    return {tag['name']: tag['images'][0]['digest']
            for tag in json.loads(response)['results']}

def last_tag(tags, pairs=False):
    if pairs:
        tags = sorted(filter_version_pairs(tags), key=version_pair_to_integers)
    else:
        tags = sorted(filter_versions(tags), key=version_to_integers)
    if not tags:
        return LATEST
    return tags[0]

def main():
    args = create_parser().parse_args()
    configure_logging(args.verbose, args.debug)

    tags = docker_tags(docker_response(args.account, args.repository))
    last = last_tag(tags, args.version_pairs)
    if tags[last] != tags[LATEST]:
        logging.warning("Last version %s is the latest image.", last)
        logging.warning("%s digest: %s...", last, tags[last][:40])
        logging.warning("%s digest: %s...", LATEST, tags[LATEST][:40])
    logging.info("Last %s digest: %s...", last, tags[last][:40])
    print(last)

if __name__ == "__main__":

    main()
