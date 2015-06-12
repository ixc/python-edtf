from datetime import date
import re
from dateutil.relativedelta import relativedelta
from edtf_exceptions import ParseError
from edtf_date import EDTFDate, PRECISION_DAY, PRECISION_MONTH, \
    PRECISION_SEASON, PRECISION_YEAR, PRECISION_DECADE, PRECISION_CENTURY, \
    PRECISION_MILLENIUM


class EDTFInterval(object):
    """
    An interval of two EDTFDates, or 'unknown'/'open'
    """

    def __init__(self, text=None):
        # after init, start and end will always be
        # 'unknown', 'open' or an EDTFDate
        self.start = None
        self.end = None

        if not text:
            text = "open/open"
        self.parse_text(text)

    def parse_text(self, text):
        parts = re.match(r'([^/]+)/([^/]+)', text)
        if parts:
            self.start = self.parse_part(parts.group(1))
            self.end = self.parse_part(parts.group(2))
        else:
            raise ParseError("An interval needs to contain a '/'")

    @staticmethod
    def parse_part(part):
        if part in ['open', 'unknown']:
            return part
        return EDTFDate(part)

    def __unicode__(self):
        return u"%s/%s" % (self.start, self.end)

    @staticmethod
    def _get_unknown_offset(precision):
        if precision == PRECISION_DAY:
            return relativedelta(months=1)
        if precision == PRECISION_MONTH:
            return relativedelta(years=1)
        if precision == PRECISION_SEASON:
            return relativedelta(months=18)
        if precision == PRECISION_YEAR:
            return relativedelta(years=5)
        if precision == PRECISION_DECADE:
            return relativedelta(years=25)
        if precision == PRECISION_CENTURY:
            return relativedelta(years=250)
        if precision == PRECISION_MILLENIUM:
            return relativedelta(years=2500)

    def start_date_earliest(self):
        if self.start in ['open', 'unknown'] \
                and self.end in ['open', 'unknown']:
            return date.min

        if self.start == "unknown":
            return self.end.date_earliest() - \
                self._get_unknown_offset(self.end.precision)
        elif self.start == "open":
            return date.min
        else:
            return self.start.date_earliest()

    def start_date_latest(self):
        if self.start in ['open', 'unknown'] \
                and self.end in ['open', 'unknown']:
            return date.max

        if self.start == "unknown":
            return self.end.date_latest()
        elif self.start == "open":
            return self.end.date_latest()
        else:
            return self.start.date_latest()

    def end_date_earliest(self):
        if self.start in ['open', 'unknown'] \
                and self.end in ['open', 'unknown']:
            return date.min

        if self.end == "unknown":
            return self.start.date_earliest()
        elif self.end == "open":
            return self.start.date_earliest()
        else:
            return self.end.date_earliest()

    def end_date_latest(self):
        if self.start in ['open', 'unknown'] \
                and self.end in ['open', 'unknown']:
            return date.max

        if self.end == "unknown":
            return self.start.date_latest() + \
                self._get_unknown_offset(self.start.precision)
        elif self.end == "open":
            return date.max
        else:
            return self.end.date_latest()

    def sort_date_earliest(self):
        if self.start not in ['unknown', 'open']:
            return self.start.sort_date_earliest()
        elif self.end not in ['unknown', 'open']:
            return self.end.sort_date_earliest()
        else: # both sides are unknown/open
            return date.min


    def sort_date_latest(self):
        if self.end not in ['unknown', 'open']:
            return self.end.sort_date_latest()
        elif self.start not in ['unknown', 'open']:
            return self.start.sort_date_latest()
        else: # both sides are unknown/open
            return date.max
