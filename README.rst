==========
musicburst
==========

This is a simple tool for extracting data from EAF files for analysis of the
``MusicBurst`` and ``Source`` tiers, and writing the output to a CSV file, with
one row per input file.

Installation
============

Clone the repository, then use ``pip`` to install the ``musicburst`` tool::

  $ git clone https://github.com/gedankenexperimenter/musicburst

  $ cd musicburst

  $ pip install .

On Windows, if you're using `pyenv`, you may also need to run this command in
order to get the `musicburst` command in your path::

  $ pyenv rehash

This should result in a ``musicburst`` command line program becoming available
in your path. In a directory with EAF files containing the target data, then
run::

  $ musicburst *.eaf

The output data will be written to the file ``musicburst-counts.csv``,
containing columns for:

- file name
- total length (until the end of the last annotated segment, which is not
  necessary the total length of the source WAV file)
- number of segments in the ``MusicBurst`` tier
- total length of those ``MusicBurst`` segments
- number of segments of the ``Source`` tier with the annotation ``1``
- total length of those ``Source`` tier segments

Notes
=====

- All time values are in milliseconds.
- Total length of the recording is not available from the EAF file alone. If you
  need the true total length, you'll have to get that from the WAV file.
