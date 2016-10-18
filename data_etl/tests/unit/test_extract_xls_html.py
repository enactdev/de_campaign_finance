import unittest

from etl import extract_xls_html as etl

TEST_CONTRIBUTIONS_LIST = (
    "<HTML>"
        "<HEAD><STYLE>.HDR { background-color:bisque;font-weight:bold;border: 1px solid #666666} .TEXT{ mso-number-format:\@;border: 1px solid #666666} </STYLE></HEAD>"
        "<BODY>"
            "<TABLE border=1>"
                "<TR style='font-family:arial' bgcolor='#EAF2FF'>"
                    "<TD><B>Contribution Date</B></TD>"
                    "<TD><B>Contributor Name</B></TD>"
                    "<TD><B>Contributor Address</B></TD>"
                "</TR>"
                "<TR>"
                    "<TD>2/2/2004</TD>"
                    "<TD>Inc, Caldera   Management</TD>"
                    "<TD>4260 Hwy 1, Rehoboth, DE 19971</TD>"
                "</TR>"
                "<TR>"
                    "<TD>9/22/2004</TD>"
                    "<TD>Conset-vancy/LLC, Rehoboth   Bay</TD>"
                    "<TD>1207 Delaware AveWilinin too/DE 19806, DE</TD>"
                "</TR>"
                "<TR>"
                    "<TD>9/17/2004</TD>"
                    "<TD>lingua, James.A</TD>"
                    "<TD>28 The Circle.Georgetown/DE 19947, DE</TD>"
                "</TR>"
            "</TABLE>"
        "</BODY>"
    "</HTML>"
)


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
