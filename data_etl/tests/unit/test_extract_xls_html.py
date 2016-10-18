import unittest

from etl import extract_xls_html as etl
from fixtures import TEST_CONTRIBUTIONS_LIST


class TestExtractHtmlData(unittest.TestCase):

    def test_extracts_headers(self):

        data = etl.extract_data_from_html(TEST_CONTRIBUTIONS_LIST)

        self.assertEqual(
            data.headers,
            ['Contribution Date',
             'Contributor Name',
             'Contributor Address']
        )

    def test_extracts_data_to_py_objs(self):

        data = etl.extract_data_from_html(TEST_CONTRIBUTIONS_LIST)

        self.assertEqual(
            list(data),
            [
                {
                    'Contribution Date': '2/2/2004',
                    'Contributor Name': 'Inc, Caldera   Management',
                    'Contributor Address': '4260 Hwy 1, Rehoboth, DE 19971'
                },
                {
                    'Contribution Date': '9/22/2004',
                    'Contributor Name': 'Conset-vancy/LLC, Rehoboth   Bay',
                    'Contributor Address': '1207 Delaware AveWilinin too/DE 19806, DE',

                },
                {
                    'Contribution Date': '9/17/2004',
                    'Contributor Name': 'lingua, James.A',
                    'Contributor Address': '28 The Circle.Georgetown/DE 19947, DE',

                },
            ]
        )


if __name__ == '__main__':
    unittest.main()
