# ruff: noqa: E402 I001

# It's recommended to `enablePackrat()` immediately after importing pyparsing
# https://github.com/pyparsing/pyparsing/wiki/Performance-Tips

import pyparsing
from edtf.appsettings import DEBUG_PYPARSING

pyparsing.ParserElement.enablePackrat()

from pyparsing import (
    Combine,
    NotAny,
    OneOrMore,
    Opt,
    Optional,
    ParseException,
    Regex,
    Word,
    ZeroOrMore,
    nums,
    oneOf,
)
from pyparsing import Literal as L


from edtf.parser.edtf_exceptions import EDTFParseException

# (* ************************** Level 0 *************************** *)
from edtf.parser.parser_classes import (
    UA,
    Consecutives,
    Date,
    DateAndTime,
    EarlierConsecutives,
    ExponentialYear,
    Interval,
    LaterConsecutives,
    Level1Interval,
    Level2Interval,
    Level2Season,
    LongYear,
    MultipleDates,
    OneOfASet,
    PartialUncertainOrApproximate,
    PartialUnspecified,
    Season,
    UncertainOrApproximate,
    Unspecified,
)

oneThru12 = oneOf([f"{i:02}" for i in range(1, 13)])
oneThru13 = oneOf([f"{i:02}" for i in range(1, 14)])
oneThru23 = oneOf([f"{i:02}" for i in range(1, 24)])
zeroThru23 = oneOf([f"{i:02}" for i in range(0, 24)])
oneThru29 = oneOf([f"{i:02}" for i in range(1, 30)])
oneThru30 = oneOf([f"{i:02}" for i in range(1, 31)])
oneThru31 = oneOf([f"{i:02}" for i in range(1, 32)])
oneThru59 = oneOf([f"{i:02}" for i in range(1, 60)])
zeroThru59 = oneOf([f"{i:02}" for i in range(0, 60)])

digit = Word(nums, exact=1)
positiveDigit = Word(nums, exact=1, excludeChars="0")
positiveInteger = Combine(positiveDigit + ZeroOrMore(digit))

second = zeroThru59
minute = zeroThru59
hour = zeroThru23
day = oneThru31("day")

month = oneThru12("month")
monthDay = (
    (oneOf("01 03 05 07 08 10 12")("month") + "-" + oneThru31("day"))
    ^ (oneOf("04 06 09 11")("month") + "-" + oneThru30("day"))
    ^ (L("02")("month") + "-" + oneThru29("day"))
)

# Significant digits suffix
significantDigits = "S" + Word(nums)("significant_digits")

# 4 digits, 0 to 9
positiveYear = Word(nums, exact=4)

# Negative version of positive year, but "-0000" is illegal
negativeYear = NotAny(L("-0000")) + ("-" + positiveYear)

year = Combine(positiveYear ^ negativeYear)("year") + Optional(significantDigits)
# simple version for Consecutives
year_basic = Combine(positiveYear ^ negativeYear)("year")

yearMonth = year + "-" + month
yearMonthDay = year + "-" + monthDay  # o hai iso date

date = Combine(year ^ yearMonth ^ yearMonthDay)("date")
Date.set_parser(date)

zoneOffsetHour = oneThru13
zoneOffset = L("Z") ^ (
    Regex("[+-]")
    + (zoneOffsetHour + Optional(":" + minute) ^ L("14:00") ^ ("00:" + oneThru59))
)

baseTime = Combine(hour + ":" + minute + ":" + second ^ "24:00:00")

time = Combine(baseTime + Optional(zoneOffset))("time")

dateAndTime = date + "T" + time
DateAndTime.set_parser(dateAndTime)

l0Interval = date("lower") + "/" + date("upper")
Interval.set_parser(l0Interval)

level0Expression = date ^ dateAndTime ^ l0Interval


# (* ************************** Level 1 *************************** *)

# (* ** Auxiliary Assignments for Level 1 ** *)
UASymbol = Combine(oneOf("? ~ %"))
UA.set_parser(UASymbol)

seasonNumber = oneOf("21 22 23 24")

# (* *** Season (unqualified) *** *)
season = year + "-" + seasonNumber("season")
Season.set_parser(season)

dateOrSeason = date("") ^ season

# (* *** Long Year - Simple Form *** *)

longYearSimple = (
    "Y"
    + Combine(Optional("-") + positiveDigit + digit + digit + digit + OneOrMore(digit))(
        "year"
    )
    + Optional(significantDigits)
)
LongYear.set_parser(longYearSimple)

# (* *** L1Interval *** *)
uaDateOrSeason = dateOrSeason + Optional(UASymbol)


# bit of a kludge here to get the all the relevant tokens into the parse action
# cleanly otherwise the parameter names are overlapped.
def f(toks):
    try:
        return {"date": toks[0], "ua": toks[1]}
    except IndexError:
        return {"date": toks[0], "ua": None}


l1Start = ".." ^ uaDateOrSeason
l1Start.addParseAction(f)
l1End = uaDateOrSeason ^ ".."
l1End.addParseAction(f)

level1Interval = Optional(l1Start)("lower") + "/" + l1End("upper") ^ l1Start(
    "lower"
) + "/" + Optional(l1End("upper"))
Level1Interval.set_parser(level1Interval)

# (* *** unspecified *** *)
yearWithOneOrTwoOrThreeUnspecifedDigits = Combine(
    Optional("-") + digit + (digit ^ "X") + (digit ^ "X") + "X"
)("year")
monthUnspecified = year + "-" + L("XX")("month")
dayUnspecified = yearMonth + "-" + L("XX")("day")
dayAndMonthUnspecified = year + "-" + L("XX")("month") + "-" + L("XX")("day")

unspecified = (
    yearWithOneOrTwoOrThreeUnspecifedDigits
    ^ monthUnspecified
    ^ dayUnspecified
    ^ dayAndMonthUnspecified
) + Optional(UASymbol)("ua")
Unspecified.set_parser(unspecified)

# (* *** uncertainOrApproxDate *** *)

uncertainOrApproxDate = date("date") + UASymbol("ua")
UncertainOrApproximate.set_parser(uncertainOrApproxDate)

level1Expression = (
    uncertainOrApproxDate ^ unspecified ^ level1Interval ^ longYearSimple ^ season
)

# (* ************************** Level 2 *************************** *)

# (* ** Internal Unspecified** *)

digitOrX = Word(nums + "X", exact=1)

# 2-digit day with at least one 'X' present
dayWithX = Combine(("X" + digitOrX) ^ (digitOrX + "X"))("day")

# 2-digit month with at least one 'X' present
monthWithX = Combine(oneOf("0X 1X") ^ ("X" + digitOrX))("month")

# 4-digit year with at least one 'X' present
yearWithX = Combine(
    ("X" + digitOrX + digitOrX + digitOrX)
    ^ (digitOrX + "X" + digitOrX + digitOrX)
    ^ (digitOrX + digitOrX + "X" + digitOrX)
    ^ (digitOrX + digitOrX + digitOrX + "X")
)("year")

yearMonthWithX = (Combine(year("") ^ yearWithX(""))("year") + "-" + monthWithX) ^ (
    yearWithX + "-" + month
)

monthDayWithX = (Combine(month("") ^ monthWithX(""))("month") + "-" + dayWithX) ^ (
    monthWithX + "-" + day
)

yearMonthDayWithX = (
    (
        yearWithX
        + "-"
        + Combine(month("") ^ monthWithX(""))("month")
        + "-"
        + Combine(day("") ^ dayWithX(""))("day")
    )
    ^ (year + "-" + monthWithX + "-" + Combine(day("") ^ dayWithX(""))("day"))
    ^ (year + "-" + month + "-" + dayWithX)
)

partialUnspecified = yearWithX ^ yearMonthWithX ^ yearMonthDayWithX
PartialUnspecified.set_parser(partialUnspecified)

# (* ** Internal Uncertain or Approximate** *)

# group qualification
# qualifier right of a component(date, month, day) applies to all components to the left
group_qual = yearMonth + UASymbol("year_month_ua") + "-" + day ^ year + UASymbol(
    "year_ua"
) + "-" + month + Opt("-" + day)

# component qualification
# qualifier immediate left of a component (date, month, day) applies to that component only
qual_year = year ^ UASymbol("year_ua_b") + year ^ year + UASymbol("year_ua")
qual_month = month ^ UASymbol("month_ua") + month
qual_day = day ^ UASymbol("day_ua") + day

indi_qual = (
    UASymbol("year_ua_b") + year + Opt("-" + qual_month + Opt("-" + qual_day))
    ^ qual_year + "-" + UASymbol("month_ua") + month + Opt("-" + qual_day)
    ^ qual_year + "-" + qual_month + "-" + UASymbol("day_ua") + day
)

partialUncertainOrApproximate = group_qual ^ indi_qual
PartialUncertainOrApproximate.set_parser(partialUncertainOrApproximate)

dateWithInternalUncertainty = partialUncertainOrApproximate ^ partialUnspecified

qualifyingString = Regex(r"\S")  # any nonwhitespace char

# (* ** SeasonQualified ** *)
seasonQualifier = qualifyingString
seasonQualified = season + "^" + seasonQualifier

# (* ** Long Year - Scientific Form ** *)
longYearScientific = (
    "Y"
    + Combine(Optional("-") + positiveInteger)("base")
    + "E"
    + positiveInteger("exponent")
    + Optional(significantDigits)
)
ExponentialYear.set_parser(longYearScientific)

# (* ** level2Interval ** *)
level2Interval = (
    (dateOrSeason("lower") + "/" + dateWithInternalUncertainty("upper"))
    ^ (dateWithInternalUncertainty("lower") + "/" + dateOrSeason("upper"))
    ^ (
        dateWithInternalUncertainty("lower")
        + "/"
        + dateWithInternalUncertainty("upper")
    )
)
Level2Interval.set_parser(level2Interval)

# (* ** Inclusive list and choice list** *)
consecutives = (
    (yearMonthDay("lower") + ".." + yearMonthDay("upper"))
    ^ (yearMonth("lower") + ".." + yearMonth("upper"))
    ^ (
        year_basic("lower") + ".." + year_basic("upper")
    )  # using year_basic because some tests were throwing `'list' object has no attribute 'expandtabs'` - somewhere, pyparsing.parse_string() was being passed a list
)
Consecutives.set_parser(consecutives)

listElement = (
    date
    ^ dateWithInternalUncertainty
    ^ uncertainOrApproxDate
    ^ unspecified
    ^ consecutives
)

earlier = L("..").addParseAction(f)("lower") + date("upper").addParseAction(f)
later = date("lower").addParseAction(f) + L("..").addParseAction(f)("upper")

EarlierConsecutives.set_parser(earlier)
LaterConsecutives.set_parser(later)


listContent = (
    (earlier + ZeroOrMore("," + listElement))
    ^ (Optional(earlier + ",") + ZeroOrMore(listElement + ",") + later)
    ^ (listElement + OneOrMore("," + listElement))
    ^ consecutives
)

choiceList = "[" + listContent + "]"
OneOfASet.set_parser(choiceList)

inclusiveList = "{" + listContent + "}"
MultipleDates.set_parser(inclusiveList)


# (* *** L2 Season *** *)
seasonL2Number = oneOf("21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41")
l2season = year + "-" + seasonL2Number("season")
Level2Season.set_parser(l2season)

level2Expression = (
    partialUncertainOrApproximate
    ^ partialUnspecified
    ^ choiceList
    ^ inclusiveList
    ^ level2Interval
    ^ longYearScientific
    ^ l2season
    ^ seasonQualified
)

# putting it all together
edtfParser = (
    level0Expression("level0") ^ level1Expression("level1") ^ level2Expression("level2")
)


def parse_edtf(input_string, parseAll=True, fail_silently=False, debug=None):
    if debug is None:
        debug = DEBUG_PYPARSING
    if not input_string:
        raise EDTFParseException(input_string)
    try:
        p = edtfParser.parseString(input_string.strip(), parseAll)
        if p:
            return p[0]
    except ParseException as err:
        if fail_silently:
            return None
        if debug:
            raise
        raise EDTFParseException(input_string, err) from None
