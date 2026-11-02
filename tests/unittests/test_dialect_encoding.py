import unittest
from unittest import mock

from tap_s3_csv import dialect

HEADER = b'DealerCode;AttributeCode;AttributeValue;AttributeValueName;StartDate;EndDate;ID\r\n'


def detect_encoding(lines):
    table = {'delimiter': ';', 'quotechar': '"'}
    stream = mock.Mock()
    stream.iter_lines.return_value = iter(lines)
    with mock.patch('tap_s3_csv.dialect.s3.get_file_handle'), \
            mock.patch('tap_s3_csv.dialect.preprocess.PreprocessStream', return_value=stream):
        dialect.detect_dialect({}, {'key': 'sample.csv'}, table)
    return table['encoding']


class TestDetectEncoding(unittest.TestCase):

    def test_utf8_with_single_accented_char_is_utf8(self):
        # chardet 5.2 guesses Windows-1252 (0.73) for this file, which turned Ö into Ã– (WP-36668)
        row = 'GÖNCZCS2;DOMINO_USR;NYILASNEG;NYILASNEG;10/22/2026;12/31/3000;1756080221'.encode('utf-8')
        self.assertEqual(detect_encoding([HEADER, row]), 'utf-8')

    def test_windows_1252_is_still_detected(self):
        rows = [f'GÖNCZCS{i};PÉCS;café;x;10/22/2026;12/31/3000;{i}\r\n'.encode('cp1252') for i in range(3)]
        encoding = detect_encoding([HEADER] + rows)
        self.assertNotEqual(encoding, 'utf-8')
        self.assertEqual(rows[0].decode(encoding), 'GÖNCZCS0;PÉCS;café;x;10/22/2026;12/31/3000;0\r\n')

    def test_utf16_guess_is_kept(self):
        text = '\ufeffDealerCode;ID\r\nGÖNCZCS2;1\r\n'.encode('utf-16-le')
        self.assertTrue(detect_encoding([text]).lower().startswith('utf-16'))
