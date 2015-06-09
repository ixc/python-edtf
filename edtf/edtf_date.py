from datetime import date
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
import re
import calendar
import edtf_exceptions
ParseError = edtf_exceptions.ParseError

PRECISION_MILLENIUM = "millenium"
PRECISION_CENTURY = "century"
PRECISION_DECADE = "decade"
PRECISION_YEAR = "year"
PRECISION_MONTH = "month"
PRECISION_SEASON = "season"
PRECISION_DAY = "day"

EARLIEST = 'earliest'
LATEST = 'latest'

SEASONS = {
    21: "spring",
    22: "summer",
    23: "autumn",
    24: "winter",
}
INV_SEASONS = {v: k for k, v in SEASONS.items()}
INV_SEASONS['fall'] = 23
SEASON_MONTHS_RANGE = {
    21: [3, 5],
    22: [6, 8],
    23: [9, 11],
    # winter in the northern hemisphere wraps the end of the year, so
    # Winter 2010 could wrap into 2011.
    # For simplicity, we assume it falls at the end of the year, esp since the
    # spec says that sort order goes spring > summer > autumn > winter
    24: [12, 12],
}

SHORT_YEAR_RE = r'(-?)([\du])([\dxu])([\dxu])([\dxu])'
LONG_YEAR_RE = r'y(-?)([1-9]\d\d\d\d+)'


def padded_string(val):
    #val is either None, 'uu' or an integer.
    if not val:
        return "xx"
    if val == 'uu':
        return val
    return "%02d" % val


class EDTFDate(object):

    def __init__(self, text=None):
        # self.day can be None (not used), 'uu' (used but not specified) or
        # a positive integer <= 31 (not checking calendar validity yet)
        self.day = None
        # self.month can be None (not used), 'uu' (used but not specified) or
        # a positive integer <= 12
        self.month = None
        # self.year is always a 4/5-digit string (optional -)
        self.year = 'uuuu'  # uuuu = unspecified year
        self._is_long_year = False
        self.is_uncertain = False
        self.is_approximate = False

        self._parsed_year = None
        self._year = None
        self._month = None
        self._day = None

        if not text:
            text = date.today().isoformat()
        self.parse_text(text)

    @property
    def precision(self):
        if self.day:
            return PRECISION_DAY
        elif self.month:
            if self.month in SEASONS:
                return PRECISION_SEASON
            return PRECISION_MONTH

        if self._is_long_year:
            return PRECISION_YEAR

        if self._single_year != 'x':
            return PRECISION_YEAR
        elif self._decade != 'x':
            return PRECISION_DECADE
        elif self._century != 'x':
            return PRECISION_CENTURY
        return PRECISION_MILLENIUM

    def get_is_negative(self):
        return bool(self._parsed_year.group(1))

    def set_is_negative(self, val):
        if self._is_long_year:
            index = 1
        else:
            index = 0

        if val:
            if self.year[index] != "-":
                self.year = self.year[:index] + "-" + self.year[index:]
        else:
            if self.year[index] == "-":
                self.year = self.year[:index] + self.year[index+1:]

    is_negative = property(get_is_negative, set_is_negative)

    @property
    def _millenium(self):
        return self._parsed_year.group(2)

    @property
    def _century(self):
        return self._parsed_year.group(3)

    @property
    def _decade(self):
        return self._parsed_year.group(4)

    @property
    def _single_year(self):
        return self._parsed_year.group(5)

    def get_year(self):
        return self._year

    def set_year(self, val):
        val = str(val)

        self._parsed_year = re.match(SHORT_YEAR_RE, val)
        if self._parsed_year:
            self._is_long_year = False
        else:
            self._parsed_year = re.match(LONG_YEAR_RE, val)
            if self._parsed_year:
                self._is_long_year = True
            else:
                raise ParseError(
                    "years must have 4 digits (or 'x' or 'u' in place of "
                    "rightmost digits) (and an optional '-' sign)"
                )
        self._year = self._parsed_year.group(0)

    year = property(get_year, set_year)

    def get_month(self):
        return self._month

    def set_month(self, val):
        if not val:
            self._month = None
            # day goes too
            self._day = None
        elif val == "uu":
            self._month = val
            #it's OK for day not to be unknown
        else:
            try:
                i = int(val)
                assert i > 0
                assert i <= 12 or i in SEASONS.keys()
                self._month = i
            except:
                raise AttributeError(
                    "I don't know what to do with a month value of '%s'. "
                    "Month must be None, 'uu', or an integer between 1 and 12"
                    % val
                )

    month = property(get_month, set_month)

    @property
    def month_string(self):
        return padded_string(self.month)

    def get_season(self):
        return SEASONS.get(self.month)

    def set_season(self, val):
        season = INV_SEASONS.get(val)
        if not season:
            raise AttributeError(
                "season must be one of %s" % (INV_SEASONS.keys())
            )
        else:
            self.month = season

    season = property(get_season, set_season)

    def get_day(self):
        return self._day

    def set_day(self, val):
        if not val:
            self._day = None
        elif val == "uu":
            self._day = val
        else:
            try:
                i = int(val)
                assert i > 0
                assert i <= 31
                self._day = i
            except:
                raise AttributeError(
                    "day must be None, 'uu', or an integer between 1 and 31."
                )

    day = property(get_day, set_day)

    @property
    def day_string(self):
        return padded_string(self.day)

    def isoish_string(self):
        precision = self.precision

        if precision == PRECISION_DAY:
            result = u"{}-{}-{}".format(
                self.year,
                self.month_string,
                self.day_string,
            )
        elif precision in [PRECISION_MONTH, PRECISION_SEASON]:
            result = u"{}-{}".format(
                self.year,
                self.month_string,
            )
        else:
            result = self.year

        return result

    def __unicode__(self):
        result = self.isoish_string()

        if self.is_uncertain:
            result += "?"
        if self.is_approximate:
            result += "~"

        return result

    def parse_text(self, text):
        try:
            year_text = re.match(r'-?[\dxu]{4}', text)
        except TypeError:
            raise ParseError("'%s' doesn't seem to be a valid string" % text)
        if year_text:
            yt = year_text.group(0)
            self.year = yt
        else:
            long_year = re.match(LONG_YEAR_RE, text)
            if long_year:
                yt = long_year.group(0)
                self.year = yt
            else:
                raise ParseError(
                    "text to parse ('%s') does not contain a year section"
                    % text
                )

        text, self.is_approximate = re.subn(r'~$', '', text)  # ~ at the end
        text, self.is_uncertain = re.subn(r'\?$', '', text)  # ? at the end

        remainder = text[len(yt)+1:]
        month_string = remainder[:2]
        self.month = month_string

        day_string = remainder[3:5]
        self.day = day_string

    def _precise_year(self, lean):
        if lean == EARLIEST:
            return re.sub(r'[xu]', r'0', self.year)
        else:
            return re.sub(r'[xu]', r'9', self.year)

    def _precise_month(self, lean):
        if not self.month or self.month == 'uu':
            return 1 if lean == EARLIEST else 12
        else:
            return self.month

    def _precise_day(self, lean):
        if not self.day or self.day == 'uu':
            if lean == EARLIEST:
                return 1
            else:
                return self._days_in_month(
                    self._precise_year(LATEST), self._precise_month(LATEST)
                )
        else:
            return self.day

    def _month_of_season(self, lean):
        rng = SEASON_MONTHS_RANGE.get(self.month, [self.month, self.month])
        if lean == EARLIEST:
            return rng[0]
        else:
            return rng[1]

    def _adjust_for_precision(self, dt, multiplier=1.0):
        precision = self.precision
        if self.is_approximate or self.is_uncertain:
            multiplier = multiplier
            if self.is_approximate and self.is_uncertain:
                multiplier *= 2.0

            if precision == PRECISION_DAY:
                return dt + relativedelta(days=int(1*multiplier))
            elif precision == PRECISION_MONTH:
                return dt + relativedelta(days=int(16*multiplier))
            elif precision == PRECISION_SEASON:
                return dt + relativedelta(weeks=int(12*multiplier))
            elif precision == PRECISION_YEAR:
                return dt + relativedelta(months=int(6*multiplier))
            elif precision == PRECISION_DECADE:
                return dt + relativedelta(years=int(5*multiplier))
            elif precision == PRECISION_CENTURY:
                return dt + relativedelta(years=int(50*multiplier))
            elif precision == PRECISION_MILLENIUM:
                return dt + relativedelta(years=int(500*multiplier))

        return dt

    @staticmethod
    def _days_in_month(yr, month):
        return calendar.monthrange(int(yr), int(month))[1]

    def sort_date(self, lean=LATEST):
        """
        Use sort_date to return the date that a human might use when sorting
        imprecise dates. For now, we'll assume that imprecise dates come after
        more precise dates - thus the date 201x will come after items
        with more precise years.

        Uncertainty and approximation information is ignored, just as a human
        would.
        """

        precision = self.precision

        parts = {
            'year': self._precise_year(lean),
            'month': 1 if lean == EARLIEST else 12,
            'day': 1 if lean == EARLIEST else 31,
        }

        if precision == PRECISION_DAY:
            parts['month'] = self._precise_month(lean)
            parts['day'] = self._precise_day(lean)

        elif precision == PRECISION_MONTH:
                parts['month'] = self._precise_month(lean)
                if lean == EARLIEST:
                    parts['day'] = 1
                else:
                    parts['day'] = self._days_in_month(
                        self._precise_year(lean), self._precise_month(lean)
                    )
        elif precision == PRECISION_SEASON:
                parts['month'] = self._month_of_season(lean)
                if lean == EARLIEST:
                    parts['day'] = 1
                else:
                    parts['day'] = self._days_in_month(
                        self._precise_year(lean), self._month_of_season(lean)
                    )

        isoish = u"%(year)s-%(month)02d-%(day)02d" % parts

        _min = date.min.isoformat()  # parser ignores the '-' sign in the year
        if isoish < _min:
            return date.min

        try:
            dt = parse(
                isoish,
                fuzzy=True,
                yearfirst=True,
                dayfirst=False,
                default=date.max if lean == LATEST else date.min
            )
        except ValueError:  # year is out of range
            if self.is_negative:
                return date.min
            else:
                return date.max

        return dt

    def latest_date(self):
        """
        Return the latest actual date this could reasonably be. Useful for
        returning dates that overlap a query.

        If a date is approximate or uncertain, we add a bit of padding - about
        half the precision in each direction. If it is both approximate and
        uncertain, we add 1 x the precision in each direction.
        """
        dt = self.sort_date(LATEST)
        return self._adjust_for_precision(dt, 1.0)

    def earliest_date(self):
        dt = self.sort_date(EARLIEST)
        return self._adjust_for_precision(dt, -1.0)
