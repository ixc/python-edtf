import unittest
from parser import Date, DateAndTime, dateAndTime


class TestLevel0(unittest.TestCase):

    def test_date(self):
        e = Date.parse("1900")
        self.assertEqual(e.year, "1900")
        self.assertEqual(e.month, None)
        self.assertEqual(e.day, None)
        self.assertEqual(unicode(e), "1900")

        e.year = "2015"
        self.assertEqual(unicode(e), "2015")
        self.assertEqual(e.as_iso(), "2015-12-31")

        e.month = "04"
        self.assertEqual(unicode(e), "2015-04")
        self.assertEqual(e.as_iso(), "2015-04-31")
        e.day = "04"
        self.assertEqual(unicode(e), "2015-04-04")
        self.assertEqual(e.as_iso(), "2015-04-04")
        e.month = None
        self.assertEqual(unicode(e), "2015")
        self.assertEqual(e.as_iso(), "2015-12-31")

    def test_date_and_time(self):
        e = DateAndTime.parse("1970-01-12T10:32:24")
        self.assertEqual(unicode(e), "1970-01-12T10:32:24")

if __name__ == '__main__':
    unittest.main()