# -*- coding: utf-8 -*-
"""
This is a script that parses EAF files and counts segments of the 'MusicBurst'
tier, and segments of the 'Source' tier annotated with the value '1'. It takes a
set of EAF files as input, and produces a CSV file as output, with columns for
file name, total file length (from beginning of the recording to the end of the
last annotated segment; the original WAV file may be longer), number of segments
in the 'MusicBurst' tier, total length of time of 'MusicBurst' tier segments
summed, number of segments in the 'Source' tier annotated with the value '1',
and the total length of those segments.
"""

import argparse
import csv
import logging
import os
import sys
import warnings

from collections import defaultdict

# pympi-ling is required for parsing of EAF files
import pympi

from musicburst import __version__

__author__ = "Michael Richters"
__copyright__ = "Michael Richters"
__license__ = "MIT"

# ==============================================================================
# Constants
music_tier_name = 'MusicBurst'
source_tier_name = 'Source'

# ==============================================================================
class OutputRecord:
    """Represents a row of the data table to be written to the output file"""
    data_labels = ['total time',
                   'music segments', 'music time',
                   'singing segments', 'singing time']
    header = ['filename']
    header.extend(data_labels)

    def __init__(self, filename):
        self.filename = os.path.basename(filename).replace('.eaf', '')
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

# ------------------------------------------------------------------------------
class Error(Exception):
    """Base class for errors in this module"""
    pass

class InputError(Error):
    """Exception raised for errors that occur when reading input

    Attributs:
        message (string): an description of the error condition
    """
    def __init__(self, message):
        self.message = message

# ==============================================================================
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
        description="Generate summary of MusicBurst  tier data in EAF file(s)"
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
        default = 'musicburst-counts.csv',
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

# ==============================================================================
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

# ==============================================================================
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

# ==============================================================================
def collect_music_data(eaf_file):
    """Collect data from an EAF file

    Args:
      eaf_file (string): filename of an EAF file to analyze

    Returns:
      :obj:`OutputRecord`: record containing the output data
    """
    logging.info("Processing {}".format(eaf_file))
    file_id = os.path.basename(eaf_file).replace('.eaf', '')

    eaf = pympi.Elan.Eaf(eaf_file)
    warnings.filterwarnings('default')

    tier_names = eaf.get_tier_names()
    logging.debug('All tiers: {}'.format(list(tier_names)))

    output_record = OutputRecord(eaf_file)

    if music_tier_name not in tier_names:
        raise InputError("Missing {} tier in file {}"
                         .format(music_tier_name, eaf_file))

    for record in eaf.get_annotation_data_for_tier(music_tier_name):
        (start, end, value) = record[:3]
        logging.debug("{} segment: {}"
                      .format(music_tier_name, (start, end, value)))
        output_record.data['music segments'] += 1
        output_record.data['music time'] += (end - start)

    if source_tier_name not in tier_names:
        logging.warning("Missing source tier in file {}".format(eaf_file))
    else:
        for record in eaf.get_annotation_data_for_tier('Source'):
            (start, end, value) = record[:3]
            logging.debug("{} segment: {}"
                          .format(source_tier_name, (start, end, value)))
            if value != '1':
                continue
            output_record.data['singing segments'] += 1
            output_record.data['singing time'] += (end - start)

    (start, end) = eaf.get_full_time_interval()
    output_record.data['total time'] = (end - start)

    return output_record

# ==============================================================================
def main(args):
    """Command-line interface function for the script to parse EAF files for
    segments in the 'MusicBurst' tier and 'Source' tier. Calls
    ``collect_music_data()`` for each EAF file specified on the command line,
    and writes the data to a specified CSV output file.

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
        try:
            output_record = collect_music_data(eaf_file)
        except InputError as err:
            logging.warning(err.message)
            continue

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
