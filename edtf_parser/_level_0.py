from datetime import date


class ParserObject(object):
    parser = None

    @classmethod
    def set_parser(cls, p):
        cls.parser = p
        p.addParseAction(cls.parse_action)

    @classmethod
    def parse_action(cls, toks):
        pass

    @classmethod
    def parse(cls, s):
        return cls.parser.parseString(s)[0]

    def __repr__(self):
        return "%s: %s" % (self.__class__, unicode(self))


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

    @classmethod
    def parse_action(cls, toks):
        return cls(**toks.asDict())

    def __init__(self, year=None, month=None, day=None):
        self.year = year
        self.month = month
        self.day = day

    def __unicode__(self):
        r = self.year
        if self.month:
            r += "-%s" % self.month
            if self.day:
                r += "-%s" % self.day

        return r

    def as_iso(self, default=date.max):
        return u"%s-%02d-%02d" % (
            self.year,
            int(self.month or default.month),
            int(self.day or default.day),
        )


class DateAndTime(ParserObject):
    @classmethod
    def parse_action(cls, toks):
        return cls(**toks.asDict())

    def __init__(self, date=None, time=None):
        self.date = date
        self.time = time

    def __unicode__(self):
        return self.date.as_iso()+"T"+self.time
