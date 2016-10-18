from cStringIO import StringIO
import json
import unittest

from etl import __main__ as main

from fixtures import TEST_CONTRIBUTIONS_LIST


class TestMain(unittest.TestCase):
    pass

    def test_main_module(self):

        input_file = StringIO(TEST_CONTRIBUTIONS_LIST)
        output_file = StringIO()
        main.main(input_file, output_file)

        output_file.seek(0)
        output = [
            json.loads(row)
            for row in output_file.readlines()
        ]

        excepted = [
            {"Contribution Date": "2/2/2004", "Contributor Name": "Inc, Caldera   Management", "Contributor Address": "4260 Hwy 1, Rehoboth, DE 19971"},
            {"Contribution Date": "9/22/2004", "Contributor Name": "Conset-vancy/LLC, Rehoboth   Bay", "Contributor Address": "1207 Delaware AveWilinin too/DE 19806, DE"},
            {"Contribution Date": "9/17/2004", "Contributor Name": "lingua, James.A", "Contributor Address": "28 The Circle.Georgetown/DE 19947, DE"}
        ]

        self.assertEqual(output, excepted)
