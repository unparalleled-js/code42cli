import csv
import click

from code42cli.errors import BadFileError


def read_csv_arg(headers):
    """Helper for defining arguments that read from a csv file. Automatically converts 
    the file name provided on command line to a list of csv rows (passed to command 
    function as `csv_rows` param).
    """
    return click.argument(
        "csv_rows",
        metavar="CSV_FILE",
        type=click.File("r"),
        callback=lambda ctx, arg: read_csv(arg, headers=headers),
    )


def read_csv(file, headers=None):
    """Helper to read a csv file object into dict rows, automatically removing header row
    if it exists.
    """
    reader = csv.DictReader(file, fieldnames=headers)
    first_row = next(reader)
    # skip first row if it's the header
    if tuple(first_row.keys()) == tuple(first_row.values()):
        return list(reader)
    else:
        return [first_row, *list(reader)]


def read_flat_file(file):
    return [row.strip() for row in file]


read_flat_file_arg = click.argument(
    "file_rows", metavar="FILE", type=click.File("r"), callback=read_flat_file
)


class CliFileReader(object):
    _ROWS_COUNT = -1

    def __init__(self, file_path):
        self.file_path = file_path

    def __call__(self, *args, **kwargs):
        pass

    def get_rows_count(self):
        if self._ROWS_COUNT == -1:
            self._ROWS_COUNT = sum(1 for _ in open(self.file_path))
        if self._ROWS_COUNT == 0:
            raise BadFileError(u"Given empty file {}.".format(self.file_path))
        return self._ROWS_COUNT


class CSVReader(CliFileReader):
    """A generator that yields header keys mapped to row values from a csv file."""

    def __init__(self, file_path):
        with open(file_path) as f:
            try:
                self.has_header = csv.Sniffer().has_header(next(f))
            except StopIteration:
                raise BadFileError(u"Given empty file {}.".format(file_path))
        super(CSVReader, self).__init__(file_path)

    def __call__(self, *args, **kwargs):
        for row in csv.DictReader(kwargs.get(u"bulk_file")):
            yield row

    def get_rows_count(self):
        rows_count = super(CSVReader, self).get_rows_count()
        return rows_count - 1 if self.has_header else rows_count


class FlatFileReader(CliFileReader):
    """A generator that yields a single-value per row from a file."""

    def __call__(self, *args, **kwargs):
        for row in kwargs[u"bulk_file"]:
            yield row


def create_csv_reader(file_path):
    return CSVReader(file_path)


def create_flat_file_reader(file_path):
    return FlatFileReader(file_path)
