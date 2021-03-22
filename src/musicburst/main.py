# -*- coding: utf-8 -*-

"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following lines in the
``[options.entry_points]`` section in ``setup.cfg``::

    console_scripts =
         fibonacci = musicburst.skeleton:run

Then run ``pip install .`` (or ``pip install -e .`` for editable mode)
which will install the command ``fibonacci`` inside your current environment.

Besides console scripts, the header (i.e. until ``_logger``...) of this file can
also be used as template for Python modules.

Note:
    This skeleton file can be safely removed if not needed!

References:
    - https://setuptools.readthedocs.io/en/latest/userguide/entry_point.html
    - https://pip.pypa.io/en/stable/reference/pip_install
"""

import argparse
import csv
import logging
import os
import re
import sys
import warnings

from collections import defaultdict

# pympi-ling is required for parsing of EAF files
import pympi

from musicburst import __version__

__author__ = "Michael Richters"
__copyright__ = "Michael Richters"
__license__ = "MIT"

_logger = logging.getLogger(__name__)


# ---- Python API ----
# The functions defined in this section can be imported by users in their
# Python scripts/interactive interpreter, e.g. via
# `from musicburst.skeleton import fib`,
# when using this Python module as a library.

# ==============================================================================
class OutputRecord:
    """Represents a row of the data table to be written to the output file"""
    data_labels = ['total time',
                   'music segments', 'music time',
                   'singing segments', 'singing time']
    header = ['filename']
    header.extend(data_labels)

    def __init__(self, filename):
        self.filename = filename
        self.data = defaultdict(int)
        return

    def fmt(self):
        values = [self.filename]
        def _blank_zero(entry):
            value = self.data[entry]
            return '' if value == 0 else value
        data_values = map(_blank_zero, self.data_labels)
        values.extend(data_values)
        return values


# ---- CLI ----
# The functions defined in this section are wrappers around the main Python
# API allowing them to be called directly from the terminal as a CLI
# executable/script.


def parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    progname = os.path.basename(sys.argv[0])

    parser = argparse.ArgumentParser(
        description="Generate summary of MUSICBURST tier data in EAF file(s)"
    )
    parser.add_argument(
        '--version',
        action  = 'version',
        version = "musicburst {ver}".format(ver=__version__),
    )
    parser.add_argument(
        '-v', '--verbose',
        dest    = 'loglevel',
        help    = "set loglevel to INFO",
        action  = 'store_const',
        const   = logging.INFO,
    )
    parser.add_argument(
        '-vv', '--very-verbose',
        dest    = 'loglevel',
        help    = "set loglevel to DEBUG",
        action  = 'store_const',
        const   = logging.DEBUG,
    )
    parser.add_argument(
        '-o', '--output',
        metavar = '<csv_file>',
        type    = argparse.FileType('w'),
        default = 'eaf-counts.csv',
        help    = "Write output to <csv_file> (default: '%(default)s')",
    )
    parser.add_argument(
        '-d', '--delimiter',
        choices = ['tab', 'comma', 'ascii'],
        default = 'comma',
        help    = "Use <delimiter> as CSV output field separator (default: '%(default)s')",
    )
    parser.add_argument(
        'eaf_files',
        metavar = '<eaf_file>',
        nargs   = '+',
        help    = "The name(s) of the EAF file(s) to process",
    )
    return parser.parse_args(args)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "%(levelname)s: %(message)s"
    logging.basicConfig(
        level   = loglevel,
        stream  = sys.stdout,
        format  = logformat,
        datefmt = "%Y-%m-%d %H:%M:%S",
    )


def setup_output(filename, delimiter):
    """Setup CSV output and write header row

    Args:
      :obj:`argparse.Namespace`: command line parameters namespace

    Returns:
      :obj:`csv.writer`: CSV output object
    """

    # Create the CSV writer object as specified by args
    output = csv.writer(filename,
                        delimiter      = delimiter,
                        quoting        = csv.QUOTE_MINIMAL,
                        lineterminator = '\n')
    # Write the header row
    logging.debug("Writing output header")
    output.writerow(OutputRecord.header)
    return output


def main(args):
    """Wrapper allowing :func:`fib` to be called with string arguments in a CLI fashion

    Instead of returning the value from :func:`fib`, it prints the result to the
    ``stdout`` in a nicely formated message.

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--verbose", "42"]``).
    """
    args = parse_args(args)
    setup_logging(args.loglevel)

    # First, set the output delimiter character from args
    output_delimiter = '\t'
    if args.delimiter == 'comma':
        output_delimiter = ','
    elif args.delimiter == 'ascii':
        output_delimiter = '\x1f'

    output = setup_output(args.output, output_delimiter)

    for eaf_file in args.eaf_files:
        logging.info("Processing {}".format(eaf_file))
        filename = os.path.basename(eaf_file).replace('.eaf', '')

        eaf = pympi.Elan.Eaf(eaf_file)
        warnings.filterwarnings('default')

        tier_names = eaf.get_tier_names()
        logging.debug('All tiers: {}'.format(list(tier_names)))

        output_record = OutputRecord(eaf_file)

        if 'MusicBurst' not in tier_names:
            logging.warning("Missing MusicBurst tier in file {}".format(eaf_file))
            continue

        for record in eaf.get_annotation_data_for_tier('MusicBurst'):
            (start, end, value) = record[:3]
            # logging.debug("{}".format(record))
            output_record.data['music segments'] += 1
            output_record.data['music time'] += (end - start)

        if 'Source' not in tier_names:
            logging.warning("Missing source tier in file {}".format(eaf_file))
        else:
            for record in eaf.get_annotation_data_for_tier('Source'):
                (start, end, value) = record[:3]
                logging.debug("{}".format(record))
                if value != '1':
                    continue
                output_record.data['singing segments'] += 1
                output_record.data['singing time'] += (end - start)

        output.writerow(output_record.fmt())

    args.output.close()


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    # ^  This is a guard statement that will prevent the following code from
    #    being executed in the case someone imports this file instead of
    #    executing it as a script.
    #    https://docs.python.org/3/library/__main__.html

    # After installing your project with pip, users can also run your Python
    # modules as scripts via the ``-m`` flag, as defined in PEP 338::
    #
    #     python -m musicburst.skeleton 42
    #
    run()
