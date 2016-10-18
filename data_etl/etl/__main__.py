import argparse
import json
import sys

from etl import extract_xls_html as etl


def main(input_file, output_file):
    data = etl.extract_data_from_html(input_file.read())
    for row in data:
        output_file.write(json.dumps(row) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument(
        'outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
    args = parser.parse_args(sys.argv[1:])
    main(args.infile, args.outfile)