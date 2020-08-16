#!/usr/bin/env python3

"""Manage GitHub software releases."""


import argparse
import logging
import os

import github

NIGHTLY_TAG = 'nightly'
NIGHTLY_BRANCH = 'master'

TAGGED_RELEASE_MESSAGE = "tagged_release_message.md"

################################################################

def argument_parser():
    """Parser for command-line arguments."""

    parser = argparse.ArgumentParser(
        description='Create GitHub software release with build artifacts.'
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

def argument_defaults(args):
    """Default values for command-line arguments."""

    # Configure logging to print INFO messages by default
    args.verbose = True
    if args.debug:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(levelname)s: %(message)s')
    elif args.verbose:
        logging.basicConfig(level=logging.INFO,
                            format='%(levelname)s: %(message)s')
    else:
        logging.basicConfig(format='%(levelname)s: %(message)s')

    return args

################################################################

def get_repository(full_name, token):
    """GitHub repository with given name authenticated with given token."""

    return github.Github(token).get_repo(full_name)

def lookup_tag(repo, tag_name):
    """The reference corresponding to a tag name."""

    try:
        ref = repo.get_git_ref('tags/{}'.format(tag_name))
    except github.UnknownObjectException as error:
        logging.info('Failed to find reference for tag %s: %s', tag_name, error)
        return None

    logging.info('Found reference for tag %s: %s', tag_name, ref)
    return ref

def lookup_release(repo, tag_name):
    """The release corresponding to a tag name."""

    for release in repo.get_releases():
        if release.tag_name == tag_name:
            logging.info('Found release for tag %s: %s', tag_name, release)
            return release
    logging.info('Failed to find release for tag %s', tag_name)
    return None

################################################################
# Create a GitHub release for a versioned software release (a tagged
# commit) with a set of installation packages for this version.

def tagged_release_message(version, path=None):
    """The message to use with a tagged release."""

    path = path or TAGGED_RELEASE_MESSAGE
    path = os.path.join(os.path.dirname(__file__), path)

    try:
        with open(path) as msg:
            return msg.read().format(version)
    except FileNotFoundError:
        logging.info("Couldn't open tagged release message file: %s", path)
        return "This is release {}".format(version)

def create_tagged_release(repo, tag_name, version=None):
    """Create a release for a tagged commit."""

    release = lookup_release(repo, tag_name)
    if release:
        release.delete_release()
        logging.info('Deleted release for tag %s: %s', tag_name, release)

    reference = lookup_tag(repo, tag_name)
    if not reference:
        raise UserWarning("Tag does not exist: {}".format(tag_name))

    version = version or tag_name.split('-')[-1]
    release_name = tag_name
    release_msg = tagged_release_message(version)
    release = repo.create_git_release(tag_name, release_name, release_msg)
    logging.info('Created release for tag %s: %s', tag_name, release)
    if not release:
        raise UserWarning("Failed to create tagged release for tag {}"
                          .format(tag_name))

    return release

def upload_release_asset(release, path,
                         label=None, content_type=None, name=None):
    """Upload an asset (an installation package) to a release."""

    filename = os.path.basename(path)
    label = label or filename
    name = name or filename
    content_type = content_type or 'text/plain'

    try:
        asset = release.upload_asset(path, label, content_type, name)
    except github.GithubException as error:
        logging.info("Failed to upload asset '%s': %s", path, error)

    logging.info("Uploaded asset '%s': %s", path, asset)
    return asset

def tagged_software_release(repo, tag_name, version=None, assets=None):
    """Create a release for a tagged commit with a list of assets."""

    # asset: {
    #   path  : required string: local path to the assest to upload to GitHub
    #   name  : string: filename to use for the asset on GitHub
    #   label : string: text to display in the link to the asset in release
    #   type  : string content type of the asset
    # }
    assets = assets or []

    release = create_tagged_release(repo, tag_name, version)
    for asset in assets:
        upload_release_asset(release, asset['path'],
                             label=asset.get('label'),
                             content_type=asset.get('type'),
                             name=asset.get('name'))

################################################################
# Create a GitHub release for a nightly build of a development branch
# with a set of installation packages for the nightly build.
#
# This works by creating (updating) a 'nightly' tag for the tip of the
# development branch, then creating an ordinary tagged release for
# this newly tagged commit, but a) the release message tailored to a
# nightly release, and b) the release type is set to "prerelease".
#
# One issue with this implementation is that the constant updating of
# the 'nightly' tag will require constant forced pulls to the local
# copy of the 'nightly' tag.  This annoyance is the primary reason
# this implementation is not currently used.

def update_nightly_tag(repo):
    """Update the nightly tag to the tip of the development branch."""

    reference = lookup_tag(repo, NIGHTLY_TAG)
    if reference:
        reference.delete()
        logging.info('Deleted tag %s: %s', NIGHTLY_TAG, reference)

    ref = 'refs/tags/{}'.format(NIGHTLY_TAG)
    sha = repo.get_branch(NIGHTLY_BRANCH).commit.sha
    reference = repo.create_git_ref(ref, sha)
    logging.info('Created tag %s for branch %s (ref %s, sha %s): %s',
                 NIGHTLY_TAG, NIGHTLY_BRANCH, ref, sha, reference)

def create_nightly_release(repo):
    """Create a tagged release for the nightly commit."""

    release = lookup_release(repo, NIGHTLY_TAG)
    if release:
        release.delete_release()
        logging.info('Deleted release for tag %s: %s', NIGHTLY_TAG, release)

    update_nightly_tag(repo)
    reference = lookup_tag(repo, NIGHTLY_TAG)
    if not reference:
        raise UserWarning("Tag does not exist: {}".format(NIGHTLY_TAG))

    release_name = "Nightly release"
    release_msg = "This is a nightly release"
    # GitHub doesn't display release with draft=False, prelease=True
    release = repo.create_git_release(NIGHTLY_TAG,
                                      release_name, release_msg,
                                      prerelease=True)
    logging.info('Created nightly release with tag %s for branch %s: %s',
                 NIGHTLY_TAG, NIGHTLY_BRANCH, release)
    if not release:
        raise UserWarning(
            "Failed to create nightly release with tag {} for branch {}"
            .format(NIGHTLY_TAG, NIGHTLY_BRANCH))
    return release

def nightly_software_release(repo, assets=None):
    """Create a tagged release for the nightly commit and pacakges."""

    # asset: {
    #   path  : required string: local path to the assest to upload to GitHub
    #   name  : string: filename to use for the asset on GitHub
    #   label : string: text to display in the link to the asset in release
    #   type  : string: content type of the asset
    # }
    assets = assets or []

    release = create_nightly_release(repo)
    for asset in assets:
        upload_release_asset(release, asset['path'],
                             label=asset.get('label'),
                             content_type=asset.get('type'),
                             name=asset.get('name'))

################################################################
