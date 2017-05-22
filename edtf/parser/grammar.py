from pyparsing import Literal as L, ParseException, Optional, OneOrMore, \
    ZeroOrMore, Regex, Or, Combine

# (* ************************** Level 0 *************************** *)
from parser_classes import Date, DateAndTime, Interval, UncertainOrApproximate, \
    Unspecified, Level1Interval, LongYear, Season, \
    PartialUncertainOrApproximate, UA, PartialUnspecified, OneOfASet, \
    Consecutives, EarlierConsecutives, LaterConsecutives, MultipleDates, \
    MaskedPrecision, Level2Interval, ExponentialYear

from edtf_exceptions import EDTFParseException

oneThru12 = L("01") ^ "02" ^ "03" ^ "04" ^ "05" ^ "06" ^ "07" ^ "08" ^ \
    "09" ^ "10" ^ "11" ^ "12"
oneThru13 = oneThru12 ^ "13"
oneThru23 = oneThru13 ^ "14" ^ "15" ^ "16" ^ "17" ^ "18" ^ "19" ^ "20" ^ \
    "21" ^ "22" ^ "23"
zeroThru23 = L("00") ^ oneThru23
oneThru29 = oneThru23 ^ "24" ^ "25" ^ "26" ^ "27" ^ "28" ^ "29"
oneThru30 = oneThru29 ^ "30"
oneThru31 = oneThru30 ^ "31"
oneThru59 = oneThru31 ^ "32" ^ "33" ^ "34" ^ "35" ^ "36" ^ "37" ^ "38" ^ \
    "39" ^ "40" ^ "41" ^ "42" ^ "43" ^ "44" ^ "45" ^ "46" ^ "47" ^ "48" ^ \
    "49" ^ "50" ^ "51" ^ "52" ^ "53" ^ "54" ^ "55" ^ "56" ^ "57" ^ "58" ^ "59"
zeroThru59 = L("00") ^ oneThru59

positiveDigit = L("1") ^ "2" ^ "3" ^ "4" ^ "5" ^ "6" ^ "7" ^ "8" ^ "9"
digit = positiveDigit ^ "0"

second = zeroThru59
minute = zeroThru59
hour = zeroThru23
day = oneThru31("day")

month = oneThru12("month")
monthDay = \
    (
        (L("01") ^ "03" ^ "05" ^ "07" ^ "08" ^ "10" ^ "12")("month") + "-"
        + oneThru31("day")
    ) \
    ^ ((L("04") ^ "06" ^ "09" ^ "11")("month") + "-" + oneThru30("day")) \
    ^ (L("02")("month") + "-" + oneThru29("day"))

positiveYear = (
    (positiveDigit + digit + digit + digit)
    ^ (digit + positiveDigit + digit + digit)
    ^ (digit + digit + positiveDigit + digit)
    ^ (digit + digit + digit + positiveDigit)
) #4 digits, at least one of which is positive

negativeYear = ("-" + positiveYear)

year = Combine(positiveYear ^ negativeYear ^ L("0000"))("year")

yearMonth = year + "-" + month
yearMonthDay = year + "-" + monthDay  # o hai iso date

date = Combine(year ^ yearMonth ^ yearMonthDay)("date")
Date.set_parser(date)

zoneOffsetHour = oneThru13
zoneOffset = L("Z") ^ \
    (
        (L("+") ^ "-") + (
            (zoneOffsetHour + Optional(":" + minute)) ^
            "14:00" ^
            ("00:" + oneThru59)
        )
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
UASymbol = Combine(L("?") ^ L("~") ^ L("?~"))
UA.set_parser(UASymbol)

seasonNumber = L("21") ^ "22" ^ "23" ^ "24"

# (* *** Season (unqualified) *** *)
season = year + "-" + seasonNumber("season")
Season.set_parser(season)

dateOrSeason = date("") ^ season

# (* *** Long Year - Simple Form *** *)

longYearSimple = "y" + Combine(
    Optional("-") + positiveDigit + digit + digit + digit + OneOrMore(digit)
)("year")
LongYear.set_parser(longYearSimple)

# (* *** L1Interval *** *)
uaDateOrSeason = dateOrSeason + Optional(UASymbol)
l1Start = uaDateOrSeason ^ "unknown"
# bit of a kludge here to get the all the relevant tokens into the parse action
# cleanly otherwise the parameter names are overlapped.
def f(toks):
    try:
        return {'date': toks[0], 'ua': toks[1]}
    except IndexError:
        return {'date': toks[0], 'ua': None}
l1Start.addParseAction(f)
l1End = uaDateOrSeason ^ "unknown" ^ "open"
l1End.addParseAction(f)

level1Interval = l1Start("lower") + "/" + l1End("upper")
Level1Interval.set_parser(level1Interval)

# (* *** unspecified *** *)
yearWithOneOrTwoUnspecifedDigits = Combine(digit + digit + (digit ^ 'u') + 'u')("year")
monthUnspecified = year + "-" + Combine("uu")("month")
dayUnspecified = yearMonth + "-" + Combine("uu")("day")
dayAndMonthUnspecified = year + "-" + Combine("uu")("month") + "-" + Combine("uu")("day")

unspecified = yearWithOneOrTwoUnspecifedDigits \
    ^ monthUnspecified \
    ^ dayUnspecified \
    ^ dayAndMonthUnspecified
Unspecified.set_parser(unspecified)

# (* *** uncertainOrApproxDate *** *)

uncertainOrApproxDate = date('date') + UASymbol("ua")
UncertainOrApproximate.set_parser(uncertainOrApproxDate)

level1Expression = uncertainOrApproxDate \
    ^ unspecified \
    ^ level1Interval \
    ^ longYearSimple \
    ^ season

# (* ************************** Level 2 *************************** *)

# (* ** Internal Unspecified** *)

positiveDigitOrU = positiveDigit ^ "u"
digitOrU = positiveDigitOrU ^ "0"
oneThru3 = L("1") ^ "2" ^ "3"

dayWithU = oneThru31 \
    ^ ("u" + digitOrU) \
    ^ (oneThru3 + "u")

monthWithU = oneThru12 ^ "0u" ^ "1u" ^ ("u" + digitOrU)

yearWithU = (L("u") + digitOrU + digitOrU + digitOrU) \
    ^ (digitOrU + "u" + digitOrU + digitOrU) \
    ^ (digitOrU + digitOrU + "u" + digitOrU) \
    ^ (digitOrU + digitOrU + digitOrU + "u")

yearMonthWithU = (Combine(year("") ^ yearWithU)("year") + "-" + monthWithU("month")) \
    ^ (yearWithU("year") + "-" + month)

monthDayWithU = (Combine(month("") ^ monthWithU)("month") + "-" + Combine(dayWithU)("day")) \
    ^ (monthWithU("month") + "-" + day)

yearMonthDayWithU = (Combine(yearWithU ^ year(""))("year") + "-" + monthDayWithU) \
    ^ (yearWithU("year") + "-" + monthDay)

partialUnspecified = yearWithU ^ yearMonthWithU ^ yearMonthDayWithU
PartialUnspecified.set_parser(partialUnspecified)

# (* ** Internal Uncertain or Approximate** *)

# this line is out of spec, but the given examples (e.g. '(2004)?-06-04~')
# appear to require it.
year_with_brackets = year ^ ("(" + year + ")")

# second clause below needed Optional() around the "year_ua" UASymbol, for dates
# like '(2011)-06-04~' to work.

IUABase = \
    (year_with_brackets + UASymbol("year_ua") + "-" + month + Optional("-(" + day + ")" + UASymbol("day_ua"))) \
    ^ (year_with_brackets + Optional(UASymbol)("year_ua") + "-" + monthDay + Optional(UASymbol)("month_day_ua")) \
    ^ (
        year_with_brackets + Optional(UASymbol)("year_ua") + "-(" + month + ")" + UASymbol("month_ua") +
        Optional("-(" + day + ")" + UASymbol("day_ua"))
    ) \
    ^ (
        year_with_brackets + Optional(UASymbol)("year_ua") + "-(" + month + ")" + UASymbol("month_ua") +
        Optional("-" + day)
    ) \
    ^ (yearMonth + UASymbol("year_month_ua") + "-(" + day + ")" + UASymbol("day_ua")) \
    ^ (yearMonth + UASymbol("year_month_ua") + "-" + day) \
    ^ (yearMonth + "-(" + day + ")" + UASymbol("day_ua")) \
    ^ (year + "-(" + monthDay + ")" + UASymbol("month_day_ua")) \
    ^ (season("ssn") + UASymbol("season_ua"))

partialUncertainOrApproximate = IUABase ^ ("(" + IUABase + ")" + UASymbol("all_ua"))
PartialUncertainOrApproximate.set_parser(partialUncertainOrApproximate)

dateWithInternalUncertainty = partialUncertainOrApproximate \
                              ^ partialUnspecified

qualifyingString = Regex(r'\S')  # any nonwhitespace char

# (* ** SeasonQualified ** *)
seasonQualifier = qualifyingString
seasonQualified = season + "^" + seasonQualifier

# (* ** Long Year - Scientific Form ** *)
positiveInteger = Combine(positiveDigit + ZeroOrMore(digit))
longYearScientific = "y" + Combine(Optional("-") + positiveInteger)("base") + "e" + \
    positiveInteger("exponent") + Optional("p" + positiveInteger("precision"))
ExponentialYear.set_parser(longYearScientific)

# (* ** level2Interval ** *)
level2Interval = (dateOrSeason("lower") + "/" + dateWithInternalUncertainty("upper")) \
                 ^ (dateWithInternalUncertainty("lower") + "/" + dateOrSeason("upper")) \
                 ^ (dateWithInternalUncertainty("lower") + "/" + dateWithInternalUncertainty("upper"))
Level2Interval.set_parser(level2Interval)

# (* ** Masked precision ** *)
maskedPrecision = Combine(digit + digit + ((digit + "x") ^ "xx"))("year")
MaskedPrecision.set_parser(maskedPrecision)

# (* ** Inclusive list and choice list** *)
consecutives = (yearMonthDay("lower") + ".." + yearMonthDay("upper")) \
    ^ (yearMonth("lower") + ".." + yearMonth("upper")) \
    ^ (year("lower") + ".." + year("upper"))
Consecutives.set_parser(consecutives)

listElement = date \
    ^ dateWithInternalUncertainty \
    ^ uncertainOrApproxDate \
    ^ unspecified \
    ^ consecutives

earlier = ".." + date("upper")
EarlierConsecutives.set_parser(earlier)
later = date("lower") + ".."
LaterConsecutives.set_parser(later)

listContent = (earlier + ZeroOrMore("," + listElement)) \
    ^ (Optional(earlier + ",") + ZeroOrMore(listElement + ",") + later) \
    ^ (listElement + OneOrMore("," + listElement)) \
    ^ consecutives

choiceList = "[" + listContent + "]"
OneOfASet.set_parser(choiceList)

inclusiveList = "{" + listContent + "}"
MultipleDates.set_parser(inclusiveList)

level2Expression = partialUncertainOrApproximate \
                   ^ partialUnspecified \
                   ^ choiceList \
                   ^ inclusiveList \
                   ^ maskedPrecision \
                   ^ level2Interval \
                   ^ longYearScientific \
                   ^ seasonQualified

# putting it all together
edtfParser = level0Expression("level0") ^ level1Expression("level1") ^ level2Expression("level2")

def parse_edtf(str, parseAll=True, fail_silently=False):
    try:
        if not str:
            raise ParseException("You must supply some input text")
        p = edtfParser.parseString(str.strip(), parseAll)
        if p:
            return p[0]
    except ParseException as e:
        if fail_silently:
            return None
        raise EDTFParseException(e)
