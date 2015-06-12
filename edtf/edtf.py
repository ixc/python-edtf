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
        Return EDTF string equivalent of a given natural language date string.
        """
        if not text:
            return cls()

        t = text.lower()

        # try parsing the whole thing
        result = EDTFDate.from_natural_text(t)
        if not result:
            # split by list delims and move fwd with the first thing that returns a non-empty string.
            for split in [",", ";", "or"]:
                for list_item in t.split(split):

                    # try parsing as an interval - split by '-'
                    toks = list_item.split("-")
                    if len(toks) == 2:
                        d1 = toks[0].strip()
                        d2 = toks[1].strip()

                        if re.match(r'^\d\D\b', d2): # 1-digit year partial e.g. 1868-9
                            if re.match(r'\b\d\d\d\d$', d1): #TODO: evaluate it and see if it's a year
                                d2 = d1[-4:-1] + d2
                        elif re.match(r'^\d\d\b', d2): # 2-digit year partial e.g. 1809-10
                            if re.match(r'\b\d\d\d\d$', d1):
                                d2 = d1[-4:-2] + d2

                        r1 = EDTFDate.from_natural_text(d1)
                        r2 = EDTFDate.from_natural_text(d2)

                        if r1 and r2:
                            return cls(r1+"/"+r2)

                    elif re.match(r"\d\d\d\d\/\d\d\d\d", t):
                        return cls(t) # already a 2-year interval


                    result = EDTFDate.from_natural_text(list_item)
                    if result:
                        break
                if result:
                    break
            else:
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

