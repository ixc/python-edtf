from datetime import datetime, date
from dateutil.parser import parse
import re
from edtf_date import EDTFDate
from edtf_interval import EDTFInterval

# two dates where every digit of an ISO representation is different,
# and one is in the past and one is in the future
DEFAULT_DATE_1 = datetime(1234, 01, 01, 0, 0)
DEFAULT_DATE_2 = datetime(5678, 10, 10, 0, 0)

DAY_FIRST = False  # Americans!

CENTURY_RE = r'(\d{1,2})(c\.?|(st|nd|rd|th) century)'


class EDTF(object):
    def __init__(self, text):
        self.date_obj = None
        if not text:
            text = date.today().isoformat()
        self.parse_text(text)

    @property
    def is_interval(self):
        return isinstance(self.date_obj, EDTFInterval)

    def parse_text(self, text):
        if "/" in text:
            self.date_obj = EDTFInterval(text)
        else:
            self.date_obj = EDTFDate(text)

    def __unicode__(self):
        return unicode(self.date_obj)

    def sort_date(self):
        return self.date_obj.sort_date()

    def start_earliest_date(self):
        if self.is_interval:
            return self.date_obj.start_earliest_date()
        else:
            return self.date_obj.earliest_date()

    earliest_date = start_earliest_date

    def start_latest_date(self):
        if self.is_interval:
            return self.date_obj.start_latest_date()
        else:
            return self.date_obj.earliest_date()

    def end_earliest_date(self):
        if self.is_interval:
            return self.date_obj.end_earliest_date()
        else:
            return self.date_obj.latest_date()

    def end_latest_date(self):
        if self.is_interval:
            return self.date_obj.end_latest_date()
        else:
            return self.date_obj.latest_date()

    latest_date = end_latest_date

    @classmethod
    def from_natural_text(cls, text):
        """

        Rough, ready, partial parser for US natural language date text into an
        EDTF date. See http://www.loc.gov/standards/datetime/

        The approach here is to parse the text twice, with different default
        dates. Then compare the results to see what differs - the parts that
        differ are undefined.
        """

        t = text.lower()
        result = ''

        # matches on '1800s'. Needs to happen before is_decade.
        could_be_century = re.findall(r'(\d{2}00)s', t)
        # matches on '1800s' and '1910s'. Removes the 's'.
        # Needs to happen before is_uncertain because e.g. "1860s?"
        t, is_decade = re.subn(r'(\d{3}0)s', r'\1', t)

        # detect approximation signifiers
        # a few 'circa' abbreviations just before the year
        is_approximate = re.findall(r'\b(ca?\.?) ?\d{4}', t)
        # the word 'circa' anywhere
        is_approximate = is_approximate or re.findall(r'\bcirca\b', t)
        # the word 'approx'/'around'/'about' anywhere
        is_approximate = is_approximate or \
            re.findall(r'\b(approx|around|about)', t)
        # a ~ before a year-ish number
        is_approximate = is_approximate or re.findall(r'\b~\d{4}', t)
        # a ~ at the beginning
        is_approximate = is_approximate or re.findall(r'^~', t)

        # detect uncertainty signifiers
        t, is_uncertain = re.subn(r'(\d{4})\?', r'\1', t)
        # the words uncertain/maybe/guess anywhere
        is_uncertain = is_uncertain or re.findall(
            r'\b(uncertain|possibly|maybe|guess)', t)

        # detect century forms
        is_century = re.findall(CENTURY_RE, t)
        if is_century:
            result = "%02dxx" % (int(is_century[0][0]) - 1,)
            is_approximate = is_approximate or \
                re.findall(r'\b(ca?\.?) ?'+CENTURY_RE, t)
            is_uncertain = is_uncertain or re.findall(CENTURY_RE+r'\?', t)
        else:
            #try dateutil.parse

            try:
                dt1 = parse(
                    t,
                    dayfirst=DAY_FIRST,
                    yearfirst=False,
                    fuzzy=True,  # force a match, even if it's default date
                    default=DEFAULT_DATE_1
                )

                dt2 = parse(
                    t,
                    dayfirst=DAY_FIRST,
                    yearfirst=False,
                    fuzzy=True,  # force a match, even if it's default date
                    default=DEFAULT_DATE_2
                )

            except ValueError:
                return None

            if dt1.date() == DEFAULT_DATE_1.date() and \
                    dt2.date() == DEFAULT_DATE_2.date():
                # couldn't parse anything - defaults are untouched.
                return None

            date1 = dt1.isoformat()[:10]
            date2 = dt2.isoformat()[:10]

            #guess precision of 'unspecified' characters to use
            mentions_year = re.findall(r'\byear\b.+(in|during)\b', t)
            mentions_month = re.findall(r'\bmonth\b.+(in|during)\b', t)
            mentions_day = re.findall(r'\bday\b.+(in|during)\b', t)

            for i in xrange(len(date1)):
                # if the given year could be a century (e.g. '1800s') then use
                # approximate/uncertain markers to decide whether we treat it as
                # a century or a decade.
                if i == 2 and could_be_century and \
                        not (is_approximate or is_uncertain):
                    result += 'x'
                elif i == 3 and is_decade > 0:
                    if mentions_year:
                        result += 'u'  # year precision
                    else:
                        result += 'x'  # decade precision
                elif date1[i] == date2[i]:
                    # since both attempts at parsing produced the same result
                    # it must be parsed value, not a default
                    result += date1[i]
                else:
                    # different values were produced, meaning that it's likely
                    # a default. Use 'unspecified'
                    result += "u"

            # strip off unknown chars from end of string - except the first 4

            for i in reversed(xrange(len(result))):
                if result[i] not in ('u', 'x', '-'):
                    smallest_length = 4

                    if mentions_month:
                        smallest_length = 7
                    if mentions_day:
                        smallest_length = 10

                    limit = max(smallest_length, i+1)
                    result = result[:limit]
                    break

            #check for seasons
            if "spring" in t:
                result = result[:4] + "-21" + result[7:]
            elif "summer" in t:
                result = result[:4] + "-22" + result[7:]
            elif "autumn" in t or "fall" in t:
                result = result[:4] + "-23" + result[7:]
            elif "winter" in t:
                result = result[:4] + "-24" + result[7:]

            # end dateutil post-parsing

        if is_uncertain:
            result += "?"

        if is_approximate:
            result += "~"

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