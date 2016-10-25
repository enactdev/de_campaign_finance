from collections import namedtuple

from bs4 import BeautifulSoup

Data = namedtuple('Data', ['headers'])


class Data(object):

    def __init__(self, html_str):
        self.soup = BeautifulSoup(html_str, 'html.parser')
        self.rows = iter(self.soup.html.body.table.find_all('tr'))
        self.headers = [
            unicode(header.string) for header in
            next(self.rows).find_all('td')
        ]

    def __iter__(self):
        for row in self.rows:
            data = [unicode(col.string) for col in row.find_all('td')]
            yield dict(zip(self.headers, data))


def extract_data_from_html(html_str):
    return Data(html_str)
