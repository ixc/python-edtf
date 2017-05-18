import re

from datetime import date

from edtf_date import EDTFDate
from edtf_interval import EDTFInterval


class EDTF(object):
    def __init__(self, edtf_text='', natural_text=''):
        """
        :param edtf_text: A valid EDTF string 
        :param natural_text: A natural language representation of the string.
         
        If `natural_text` is given without `edtf_text` then we attempt to parse
        the natural text.
        
        If both are given, `natural_text` is stored but not parsed.
        """
        self.edtf_text = edtf_text
        self.natural_text = natural_text
        self._date_obj = None

        if self.edtf_text:
            self._parse_edtf_text()
        else:
            if self.natural_text:
                self._parse_natural_text()
            else:
                self._parse_edtf_text() # return an empty date object
    @property
    def combined_text(self):
        if self.edtf_text:
            if self.natural_text:
                return u"%s `%s`" % (self.natural_text, self.edtf_text)
            else:
                return u"`%s`" % (self.edtf_text,)
        else:
            if self.natural_text:
                return self.natural_text
            else:
                return u""

    @property
    def display_text(self):
        return self.natural_text or self.edtf_text or ""

    def __unicode__(self):
        return self.display_text

    def __repr__(self):
        if self.natural_text:
            if self.edtf_text:
                return u"EDTF(edtf_text='%s', natural_text='%s')" % (self.edtf_text, self.natural_text)
            else:
                return u"EDTF(natural_text='%s')" % (self.natural_text, )
        else:
            if self.edtf_text:
                return u"EDTF('%s')" % self.edtf_text
            else:
                return u"EDTF()"

    # Comparison operators

    def __eq__(self, other):
        if isinstance(other, EDTF):
            return self.edtf_text == other.edtf_text
        else:
            return False

    def __ne__(self, other):
        if isinstance(other, EDTF):
            return self.edtf_text != other.edtf_text
        else:
            return True

    def __lt__(self, other):
        if isinstance(other, EDTF):
            return self.sort_date_earliest() < other.sort_date_earliest()
        elif isinstance(other, date):
            return self.sort_date_earliest() < other
        else:
            raise TypeError("Trying to compare incomparable types.")

    def __le__(self, other):
        if isinstance(other, EDTF):
            return self.sort_date_earliest() <= other.sort_date_earliest()
        elif isinstance(other, date):
            return self.sort_date_earliest() <= other
        else:
            raise TypeError("Trying to compare incomparable types.")

    def __gt__(self, other):
        if isinstance(other, EDTF):
            return self.sort_date_earliest() > other.sort_date_earliest()
        elif isinstance(other, date):
            return self.sort_date_earliest() > other
        else:
            raise TypeError("Trying to compare incomparable types.")

    def __ge__(self, other):
        if isinstance(other, EDTF):
            return self.sort_date_earliest() >= other.sort_date_earliest()
        elif isinstance(other, date):
            return self.sort_date_earliest() >= other
        else:
            raise TypeError("Trying to compare incomparable types.")

    @property
    def is_interval(self):
        return isinstance(self._date_obj, EDTFInterval)

    def _parse_edtf_text(self):
        if not self.edtf_text:
            self._date_obj = EDTFDate()
        elif "/" in self.edtf_text:
            self._date_obj = EDTFInterval(self.edtf_text)
        else:
            self._date_obj = EDTFDate(self.edtf_text)


    def sort_date_earliest(self):
        if self._date_obj:
            return self._date_obj.sort_date_earliest()

    def sort_date_latest(self):
        if self._date_obj:
            return self._date_obj.sort_date_latest()

    def start_date_earliest(self):
        if self._date_obj:
            if self.is_interval:
                return self._date_obj.start_date_earliest()
            else:
                return self._date_obj.date_earliest()

    date_earliest = start_date_earliest

    def start_date_latest(self):
        if self._date_obj:
            if self.is_interval:
                return self._date_obj.start_date_latest()
            else:
                return self._date_obj.date_earliest()

    def end_date_earliest(self):
        if self._date_obj:
            if self.is_interval:
                return self._date_obj.end_date_earliest()
            else:
                return self._date_obj.date_latest()

    def end_date_latest(self):
        if self._date_obj:
            if self.is_interval:
                return self._date_obj.end_date_latest()
            else:
                return self._date_obj.date_latest()

    date_latest = end_date_latest

    def _parse_natural_text(self):
        """
        Return EDTF string equivalent of a given natural language date string.
        """
        if not self.natural_text:
            return

        t = self.natural_text.lower()

        # try parsing the whole thing
        result = EDTFDate(natural_text=t).edtf_text
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

                        r1 = EDTFDate(natural_text=d1).edtf_text
                        r2 = EDTFDate(natural_text=d2).edtf_text

                        if r1 and r2:
                            self.edtf_text = r1+"/"+r2
                            self._parse_edtf_text()
                            return

                    # is it a year-to-year interval
                    elif re.match(r"\d\d\d\d\/\d\d\d\d", list_item):
                        self.edtf_text = list_item
                        self._parse_edtf_text()
                        return

                    result = EDTFDate(natural_text=list_item).edtf_text
                    if result:
                        break
                if result:
                    break
            else:
                return

        is_before = re.findall(r'\bbefore\b', t)
        is_before = is_before or re.findall(r'\bearlier\b', t)

        is_after = re.findall(r'\bafter\b', t)
        is_after = is_after or re.findall(r'\bsince\b', t)
        is_after = is_after or re.findall(r'\blater\b', t)

        if is_before:
            result = u"unknown/%s" % result
        elif is_after:
            result = u"%s/unknown" % result

        self.edtf_text = result
        self._parse_edtf_text()

    @classmethod
    def from_combined_text(cls, combined_text):
        edtf_only_re = r'`(.+)`'
        combined_re = r'\s*(.*)\s+`(.+)`'
        m = re.match(edtf_only_re, combined_text)
        if m:
            edtf_text = m.group(1)
            return cls(edtf_text=edtf_text)
        else:
            m2 = re.match(combined_re, combined_text)
            if m2:
                natural_text = m2.group(1)
                edtf_text = m2.group(2)
                return cls(edtf_text=edtf_text, natural_text=natural_text)
            else:
                return cls(natural_text=combined_text)
