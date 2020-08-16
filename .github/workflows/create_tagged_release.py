#!/usr/bin/env python3

"""Create a GitHub release for a tagged commit."""

import logging
import os
import re

import github_release

################################################################

def extend_argument_parser(parser):
    """Add flags to the command line parser."""

    parser.add_argument(
        '--source-package',
        help='Path to pip source installation package.'
    )

    parser.add_argument(
        '--binary-package',
        required=True,
        help='Path to pip binary installation package.'
    )

    parser.add_argument(
        '--tag',
        required=True,
        help='GitHub tag of the package being released'
    )

    parser.add_argument(
        '--version',
        required=True,
        help='Version of the package being released'
    )

    return parser

def main():
    """Create a GitHub release for a tagged commit."""

    parser = github_release.argument_parser()
    parser = extend_argument_parser(parser)
    args = parser.parse_args()
    args = github_release.argument_defaults(args)

    if not os.path.isfile(args.binary_package):
        raise UserWarning("Binary package does not exist: {}"
                          .format(args.binary_package))

    if not re.match(r'[\w.-]+', args.tag, re.ASCII):
        raise UserWarning("Package version contains an illegal character: {}"
                          .format(args.tag))

    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        logging.info(
            'Failed to find GitHub token in environment variable '
            'GITHUB_TOKEN'
        )

    repo_name = os.environ.get('GITHUB_REPOSITORY')
    if not repo_name:
        logging.info(
            'Failed to find GitHub repository in environment variable '
            'GITHUB_REPOSITORY'
        )

    repo = github_release.get_repository(repo_name, token)
    assets = [
        {
            'path': args.binary_package,
            'name': os.path.basename(args.binary_package),
            'label': 'PIP installation package',
            'type': 'application/binary'
        }
    ]
    github_release.tagged_software_release(repo, args.tag, args.version,
                                           assets)

if __name__ == "__main__":
    main()
