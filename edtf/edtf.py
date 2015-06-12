from datetime import datetime, date
from dateutil.parser import parse
import re
from edtf_date import EDTFDate
from edtf_interval import EDTFInterval


class EDTF(object):
    def __init__(self, text=None):
        self.date_obj = None
        self.parse_text(text)

    @property
    def is_interval(self):
        return isinstance(self.date_obj, EDTFInterval)

    def parse_text(self, text):
        if not text:
            self.date_obj = EDTFDate()
        elif "/" in text:
            self.date_obj = EDTFInterval(text)
        else:
            self.date_obj = EDTFDate(text)

    def __unicode__(self):
        return unicode(self.date_obj)

    def sort_date_earliest(self):
        return self.date_obj.sort_date_earliest()

    def sort_date_latest(self):
        return self.date_obj.sort_date_latest()

    def start_date_earliest(self):
        if self.is_interval:
            return self.date_obj.start_date_earliest()
        else:
            return self.date_obj.date_earliest()

    date_earliest = start_date_earliest

    def start_date_latest(self):
        if self.is_interval:
            return self.date_obj.start_date_latest()
        else:
            return self.date_obj.date_earliest()

    def end_date_earliest(self):
        if self.is_interval:
            return self.date_obj.end_date_earliest()
        else:
            return self.date_obj.date_latest()

    def end_date_latest(self):
        if self.is_interval:
            return self.date_obj.end_date_latest()
        else:
            return self.date_obj.date_latest()

    date_latest = end_date_latest

    @classmethod
    def from_natural_text(cls, text):
        """

        Rough, ready, partial parser for US natural language date text into an
        EDTF date. See http://www.loc.gov/standards/datetime/

        The approach here is to parse the text twice, with different default
        dates. Then compare the results to see what differs - the parts that
        differ are undefined.
        """
        if not text:
            return cls()

        t = text.lower()
        result = EDTFDate.from_natural_text(t)

        if not result:
            return cls()

        is_before = re.findall(r'\bbefore\b', t)
        is_before = is_before or re.findall(r'\bearlier\b', t)

        is_after = re.findall(r'\bafter\b', t)
        is_after = is_after or re.findall(r'\bsince\b', t)
        is_after = is_after or re.findall(r'\blater\b', t)

        if is_before:
            result = u"unknown/%s" % result
        elif is_after:
            result = u"%s/unknown" % result

        return cls(result)