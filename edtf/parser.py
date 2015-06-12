from pyparsing import Literal as L, ParseException, Optional, OneOrMore, \
    ZeroOrMore, Regex, Or, Combine

# (* ************************** Level 0 *************************** *)
from edtf._level_0 import Date, DateAndTime

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

date = Combine(year ^ yearMonth ^ yearMonthDay)
Date.set_parser(date)

zoneOffsetHour = oneThru13
zoneOffset = Combine(L("Z") ^ \
    (
        (L("+") ^ "-") + (
            (zoneOffsetHour + Optional(":" + minute)) ^
            "14:00" ^
            ("00:" + oneThru59)
        )
    ))("timezone")

baseTime = Combine(hour + ":" + minute + ":" + second ^ "24:00:00")

time = Combine(baseTime + Optional(zoneOffset))

dateAndTime = date("date") + "T" + time("time")
DateAndTime.set_parser(dateAndTime)

L0Interval = date("date1") + "/" + date("date2")

# register_parser_class(date, Date)
# register_parser_class(dateAndTime, DateAndTime)
# register_parser_class(L0Interval, Level0Interval)

level0Expression = date ^ dateAndTime ^ L0Interval


# (* ************************** Level 1 *************************** *)

# (* ** Auxiliary Assignments for Level 1 ** *)
UASymbol = (L("?")("uncertain") ^ L("~")("approximate") ^ L("?~")("uncertain_and_approximate"))
seasonNumber = L("21") ^ "22" ^ "23" ^ "24"

# (* *** Season (unqualified) *** *)
season = year + "-" + seasonNumber

dateOrSeason = date ^ season

# (* *** Long Year - Simple Form *** *)

longYearSimple = "y" + Optional("-") + \
                 positiveDigit + digit + digit + digit + OneOrMore(digit)


# (* *** L1Interval *** *)
L1Start = (dateOrSeason + Optional(UASymbol)) ^ "unknown"
L1End = L1Start ^ "open"
L1Interval = L1Start + "/" + L1End

# (* *** unspecified *** *)
yearWithOneOrTwoUnspecifedDigits = digit + digit + (digit ^ 'u') + 'u'
monthUnspecified = year + "-uu"
dayUnspecified = yearMonth + "-uu"
dayAndMonthUnspecified = year + "-uu-uu"

unspecified = yearWithOneOrTwoUnspecifedDigits \
    ^ monthUnspecified \
    ^ dayUnspecified \
    ^ dayAndMonthUnspecified

# (* *** uncertainOrApproxDate *** *)

uncertainOrApproxDate = date + UASymbol

level1Expression = uncertainOrApproxDate \
    ^ unspecified \
    ^ L1Interval \
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

yearMonthWithU = ((year ^ yearWithU) + "-" + monthWithU) \
    ^ (yearWithU + "-" + month)


monthDayWithU = ((month ^ monthWithU) + "-" + dayWithU) \
    ^ (monthWithU + "-" + day)

yearMonthDayWithU = ((yearWithU ^ year) + "-" + monthDayWithU) \
    ^ (yearWithU + "-" + monthDay)

internalUnspecified = yearWithU ^ yearMonthWithU ^ yearMonthDayWithU


# (* ** Internal Uncertain or Approximate** *)

IUABase = \
    (year + UASymbol + "-" + month + Optional("-(" + day + ")" + UASymbol)) \
    ^ (year + UASymbol + "-" + monthDay + Optional(UASymbol)) \
    ^ (
        year + Optional(UASymbol) + "-(" + month + ")" + UASymbol +
        Optional("-(" + day + ")" + UASymbol)
    ) \
    ^ (
        year + Optional(UASymbol) + "-(" + month + ")" + UASymbol +
        Optional("-" + day)
    ) \
    ^ (yearMonth + UASymbol + "-(" + day + ")" + UASymbol) \
    ^ (yearMonth + UASymbol + "-" + day) \
    ^ (yearMonth + "-(" + day + ")" + UASymbol) \
    ^ (year + "-(" + monthDay + ")" + UASymbol) \
    ^ (season + UASymbol) \

internalUncertainOrApproximate = IUABase ^ ("(" + IUABase + ")" + UASymbol)

dateWithInternalUncertainty = internalUncertainOrApproximate \
    ^ internalUnspecified

qualifyingString = Regex(r'\S')  # any nonwhitespace char

# (* ** SeasonQualified ** *)
seasonQualifier = qualifyingString
seasonQualified = season + "^" + seasonQualifier

# (* ** Long Year - Scientific Form ** *)
positiveInteger = positiveDigit + ZeroOrMore(digit)
longYearScientific = "y" + Optional("-") + positiveInteger + "e" + \
    positiveInteger + Optional("p" + positiveInteger)


# (* ** L2Interval ** *)
L2Interval = (dateOrSeason + "/" + dateWithInternalUncertainty) \
    ^ (dateWithInternalUncertainty + "/" + dateOrSeason) \
    ^ (dateWithInternalUncertainty + "/" + dateWithInternalUncertainty)

# (* ** Masked precision ** *)
maskedPrecision = digit + digit + ((digit + "x") ^ "xx")

# (* ** Inclusive list and choice list** *)
consecutives = (yearMonthDay + ".." + yearMonthDay) \
    ^ (yearMonth + ".." + yearMonth) \
    ^ (year + ".." + year)

listElement = date \
    ^ dateWithInternalUncertainty \
    ^ uncertainOrApproxDate \
    ^ unspecified \
    ^ consecutives

earlier = ".." + date
later = date + ".."

listContent = (earlier + ZeroOrMore("," + listElement)) \
    ^ (Optional(earlier + ",") + ZeroOrMore(listElement + ",") + later) \
    ^ (listElement + OneOrMore("," + listElement)) \
    ^ consecutives

choiceList = "[" + listContent + "]"
inclusiveList = "{" + listContent + "}"

level2Expression = internalUncertainOrApproximate \
    ^ internalUnspecified \
    ^ choiceList \
    ^ inclusiveList \
    ^ maskedPrecision \
    ^ L2Interval \
    ^ longYearScientific \
    ^ seasonQualified

# putting it all together
parser = level0Expression("level0") ^ level1Expression("level1") ^ level2Expression("level2")


class EDTFParser(object):
    def __init__(self, str, parseAll=True):
        try:
            self.p = parser.parseString(str, parseAll=parseAll)
        except ParseException as pe:
            raise pe

    @property
    def level(self):
        k = self.p.keys()
        if "level0" in k:
            return 0
        elif "level1" in k:
            return 1
        elif "level2" in k:
            return 2
        assert False
