# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Run a command with simple error handling."""

import logging
import subprocess
import sys

def run(cmd, cwd=None, ignored=None, encoding=None):
    """Run command cmd in directory cwd.

    The argument 'ignored' may be a list of integers giving command
    return codes that are acceptable and can be ignored.

    The argument 'encoding' is a character encoding for the text
    string captured as stdout and stderr.  The default encoding for
    modern Python is utf-8, but source code written on Windows
    platforms uses a different character encoding.  In this case,
    'latin1' is a reasonable choice, since it agrees with utf-8 on the
    ascii character set.  The wikipedia page on latin1 goes so far as
    to say latin1 is "often assumed to be the encoding of 8-bit text
    on Unix and Microsoft Windows...".
    """

    kwds = {
        'cwd': cwd,
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE,
        'universal_newlines': True,
    }

    # encoding keyword argument was introduced in Python 3.6
    if sys.version_info >= (3, 6):
        kwds['encoding'] = encoding

    logging.debug('run: cmd: %s', cmd)
    logging.debug('run: kwds: %s', kwds)

    result = subprocess.run(cmd, **kwds, check=False)

    if result.returncode:
        logging.debug('Failed to run command: %s', ' '.join(cmd))
        logging.debug('Failed return code: %s', result.returncode)
        logging.debug('Failed stdout: %s', result.stdout)
        logging.debug('Failed stderr: %s', result.stderr)
        if ignored is None or result.returncode not in ignored:
            result.check_returncode()
        logging.debug('Ignoring failure to run command: %s', cmd)

    return result.stdout
