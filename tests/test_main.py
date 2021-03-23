"""
Tests for main() function
"""
import pytest

from musicburst.main import main

__author__ = "Michael Richters"
__copyright__ = "Michael Richters"
__license__ = "MIT"

HEADERS = [
    'filename', 'total time',
    'music segments', 'music time',
    'singing segments', 'singing time',
]

def test_main(capsys):
    """CLI Tests"""
    # capsys is a pytest fixture that allows asserts agains stdout/stderr
    # https://docs.pytest.org/en/stable/capture.html
    main(['-o', '-', 'tests/test.eaf'])
    captured = capsys.readouterr()
    csv_output = captured.out.split('\n')
    for line in csv_output:
        print(line)
    assert csv_output[0] == ','.join(HEADERS)
    assert csv_output[1] == "test,7320009,48,638273,18,128369"
