from datetime import date


class ParserObject(object):
    """
    Object to attact to a parser to become instantiated when the parser
    completes.
    """
    parser = None

    @classmethod
    def set_parser(cls, p):
        cls.parser = p
        p.addParseAction(cls.parse_action)

    @classmethod
    def parse_action(cls, toks):
        kwargs = toks.asDict()
        try:
            return cls(**kwargs) # replace the token list with the class
        except Exception as e:
            if isinstance(e, NotImplementedError):
                raise(e)
            print "trying to %s.__init__(**%s)" % (cls.__name__, kwargs)
            print e
            import pdb; pdb.set_trace()

    @classmethod
    def parse(cls, s):
        return cls.parser.parseString(s)[0]

    def __repr__(self):
        return "%s: '%s'" % (type(self).__name__, unicode(self))

    def __init__(self, *args, **kwargs):
        str = "%s.__init__(*%s, **%s)" % (
            type(self).__name__,
            args, kwargs,
        )
        raise NotImplementedError("%s is not implemented." % str)

    def __unicode__(self):
        raise NotImplementedError


# (* ************************** Level 0 *************************** *)


class Date(ParserObject):

    def set_year(self, y):
        if y is None:
            raise AttributeError("Year must not be None")
        self._year = y
    def get_year(self):
        return self._year
    year = property(get_year, set_year)

    def set_month(self, m):
        self._month = m
        if m == None:
            self.day = None
    def get_month(self):
        return self._month
    month = property(get_month, set_month)

    def __init__(self, year=None, month=None, day=None, **kwargs):
        for param in ('date', 'lower', 'upper'):
            if param in kwargs:
                self.__init__(**kwargs[param])
                return

        self.year = year
        self.month = month
        self.day = day

    def __unicode__(self):
        r = self.year
        if self.month:
            r += u"-%s" % self.month
            if self.day:
                r += u"-%s" % self.day
        return r

    def as_iso(self, default=date.max):
        return u"%s-%02d-%02d" % (
            self.year,
            int(self.month or default.month),
            int(self.day or default.day),
        )


class DateAndTime(ParserObject):
    def __init__(self, date, time):
        self.date = date
        self.time = time

    def __unicode__(self):
        return self.as_iso()

    def as_iso(self):
        return self.date.as_iso()+"T"+self.time


class Interval(ParserObject):
    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper

    def __unicode__(self):
        return u"%s/%s" % (self.lower, self.upper)


# (* ************************** Level 1 *************************** *)

class UA(ParserObject):
    @classmethod
    def parse_action(cls, toks):
        args = toks.asList()
        return cls(*args)

    def __init__(self, *args):
        assert len(args)==1
        ua = args[0]

        self.is_uncertain = "?" in ua
        self.is_approximate = "~" in ua

    def __unicode__(self):
        d = ""
        if self.is_uncertain:
            d += "?"
        if self.is_approximate:
            d += "~"
        return d


class UncertainOrApproximate(ParserObject):
    def __init__(self, date, ua):
        self.date = date
        self.ua = ua

    def __unicode__(self):
        if self.ua:
            return u"%s%s" % (self.date, self.ua)
        else:
            return unicode(self.date)


class Unspecified(Date):
    pass


class Level1Interval(Interval):
    def __init__(self, lower, upper):
        self.lower = UncertainOrApproximate(**lower)
        self.upper = UncertainOrApproximate(**upper)


class LongYear(ParserObject):
    def __init__(self, year):
        self.year = year

    def __unicode__(self):
        return "y%s" % self.year


class Season(ParserObject):
    def __init__(self, year, season, **kwargs):
        self.year = year
        self.season = season

    def __unicode__(self):
        return "%s-%s" % (self.year, self.season)

# (* ************************** Level 2 *************************** *)

class PartialUncertainOrApproximate(ParserObject):
    def __init__(
        self, year=None, month=None, day=None,
        year_ua = False, month_ua = False, day_ua = False,
        year_month_ua = False, month_day_ua = False,
        ssn=None, season_ua=False, all_ua=False
    ):
        self.year = year
        self.month = month
        self.day = day

        self.year_ua = year_ua
        self.month_ua = month_ua
        self.day_ua = day_ua

        self.year_month_ua = year_month_ua
        self.month_day_ua = month_day_ua

        self.season = ssn
        self.season_ua = season_ua

        self.all_ua = all_ua

    def __unicode__(self):

        if self.season_ua:
            return "%s%s" % (self.season, self.season_ua)

        if self.year_ua:
            y = "%s%s" % (self.year, self.year_ua)
        else:
            y = unicode(self.year)

        if self.month_ua:
            m = "(%s)%s" % (self.month, self.month_ua)
        else:
            m = unicode(self.month)

        if self.day:
            if self.day_ua:
                d = "(%s)%s" % (self.day, self.day_ua)
            else:
                d = unicode(self.day)
        else:
            d = None

        if self.year_month_ua: # year/month approximate. No brackets needed.
            ym = "%s-%s%s" % (y, m, self.year_month_ua)
            if d:
                result = "%s-%s" % (ym, d)
            else:
                result = ym
        elif self.month_day_ua:
            if self.year_ua: # we don't need the brackets round month and day
                result = "%s-%s-%s%s" % (y, m, d, self.month_day_ua)
            else:
                result = "%s-(%s-%s)%s" % (y, m, d, self.month_day_ua)
        else:
            if d:
                result = "%s-%s-%s" % (y, m, d)
            else:
                result = "%s-%s" % (y, m)

        if self.all_ua:
            result = "(%s)%s" % (result, self.all_ua)

        return result


class PartialUnspecified(Unspecified):
    pass

class Consecutives(Interval):
    # Treating Consecutive ranges as intervals where one bound is optional
    def __init__(self, lower=None, upper=None):
        self.lower = lower
        self.upper = upper

    def __unicode__(self):
        return u"%s..%s" % (self.lower or '', self.upper or '')


class EarlierConsecutives(Consecutives):
    pass


class LaterConsecutives(Consecutives):
    pass


class OneOfASet(ParserObject):
    @classmethod
    def parse_action(cls, toks):
        args = [t for t in toks.asList() if isinstance(t, ParserObject)]
        return cls(*args)

    def __init__(self, *args):
        self.objects = args

    def __unicode__(self):
        return u"[%s]" % (", ".join([unicode(o) for o in self.objects]))


class MultipleDates(ParserObject):
    @classmethod
    def parse_action(cls, toks):
        args = [t for t in toks.asList() if isinstance(t, ParserObject)]
        return cls(*args)

    def __init__(self, *args):
        self.objects = args

    def __unicode__(self):
        return u"{%s}" % (", ".join([unicode(o) for o in self.objects]))


class MaskedPrecision(Date):
    pass


class Level2Interval(Level1Interval):
    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper

class ExponentialYear(LongYear):
    def __init__(self, base, exponent, precision=None):
        self.base = base
        self.exponent = exponent
        self.precision = precision

    def get_year(self):
        if self.precision:
            return '%se%sp%s' % (self.base, self.exponent, self.precision)
        else:
            return '%se%s' % (self.base, self.exponent)
    year = property(get_year)
