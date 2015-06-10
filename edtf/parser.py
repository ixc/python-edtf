from pyparsing import Literal, ParseException, Optional, OneOrMore, Word, \
    ZeroOrMore, Regex

# (* ************************** Level 0 *************************** *)


oneThru12 = Literal("01") ^ "02" ^ "03" ^ "04" ^ "05" ^ "06" ^ "07" ^ "08" ^ \
    "09" ^ "10" ^ "11" ^ "12"
oneThru13 = oneThru12 ^ "13"
oneThru23 = oneThru13 ^ "14" ^ "15" ^ "16" ^ "17" ^ "18" ^ "19" ^ "20" ^ \
    "21" ^ "22" ^ "23"
zeroThru23 = Literal("00") ^ oneThru23
oneThru29 = oneThru23 ^ "24" ^ "25" ^ "26" ^ "27" ^ "28" ^ "29"
oneThru30 = oneThru29 ^ "30"
oneThru31 = oneThru30 ^ "31"
oneThru59 = oneThru31 ^ "32" ^ "33" ^ "34" ^ "35" ^ "36" ^ "37" ^ "38" ^ \
    "39" ^ "40" ^ "41" ^ "42" ^ "43" ^ "44" ^ "45" ^ "46" ^ "47" ^ "48" ^ \
    "49" ^ "50" ^ "51" ^ "52" ^ "53" ^ "54" ^ "55" ^ "56" ^ "57" ^ "58" ^ "59"
zeroThru59 = Literal("00") ^ oneThru59

positiveDigit = Literal("1") ^ "2" ^ "3" ^ "4" ^ "5" ^ "6" ^ "7" ^ "8" ^ "9"
digit = positiveDigit ^ "0"

second = zeroThru59("second")
minute = zeroThru59
hour = zeroThru23
day = oneThru31

month = oneThru12
monthDay = \
    (
        (Literal("01") ^ "03" ^ "05" ^ "07" ^ "08" ^ "10" ^ "12") + "-"
        + oneThru31
    ) \
    ^ ((Literal("04") ^ "06" ^ "09" ^ "11") + "-" + oneThru30) \
    ^ ("02-" + oneThru29)

positiveYear = (positiveDigit + digit + digit + digit) \
    ^ (digit + positiveDigit + digit + digit) \
    ^ (digit + digit + positiveDigit + digit) \
    ^ (digit + digit + digit + positiveDigit)

negativeYear = "-" + positiveYear

year = positiveYear ^ negativeYear ^ "0000"


yearMonth = year + "-" + month
yearMonthDay = year + "-" + monthDay

date = year ^ yearMonth ^ yearMonthDay

zoneOffsetHour = oneThru13
zoneOffset = Literal("Z") ^ (Literal("+") ^ "-") ^ (
    (zoneOffsetHour + Optional(":" + minute)) ^
    "14:00" ^
    ("00:" + oneThru59)
)

baseTime = hour + ":" + minute + ":" + second ^ "24:00:00"

time = baseTime + Optional(zoneOffset)

dateAndTime = date + "T" + time

L0Interval = date + "/" + date

level0Expression = date ^ dateAndTime ^ L0Interval


# (* ************************** Level 1 *************************** *)

# (* ** Auxiliary Assignments for Level 1 ** *)
UASymbol = (Literal("?") ^ "~" ^ "?~")
seasonNumber = Literal("21") ^ "22" ^ "23" ^ "24"

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
oneThru3 = Literal("1") ^ "2" ^ "3"

dayWithU = oneThru31 \
    ^ ("u" + digitOrU) \
    ^ (oneThru3 + "u")

monthWithU = oneThru12 ^ "0u" ^ "1u" ^ ("u" + digitOrU)

yearWithU = (Literal("u") + digitOrU + digitOrU + digitOrU) \
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
dateTimeString = level0Expression ^ level1Expression ^ level2Expression


if __name__ == "__main__":
    tests = """\
2001-02-03
2008-12
2008
-0999
0000
2001-02-03T09:30:01
2001-01-01T10:10:10Z
2004-01-01T10:10:10+05:00
1964/2008
2004-06/2008-08
2004-02-01/2004-02-08
2004-02-01/2005-02
2004-02-01/2005
2005/2006-02
1984?
2004-06?
2004-06-11^
1984~
1984?~
199u
19uu
1999-uu
1999-01-uu
1999-uu-uu
unknown/2006
2004-06-01/unknown
2004-01-01/open
1984~/2004-06
1984/2004-06~
1984~/2004~
1984?/2004?~
1984-06?/2004-08?
1984-05-02?/2004-08-08~
1984-06-02?/2004-08-08~
1986-06-02?/unknown
y170000002
y-170000002
2001-21
2003-22
2000-23
2010-24
2004?-06-11
2004-06~-11
2004-(06)?-11
2004-06-(11)~
2004-(06)?~
2004-(06-11)?
2004-?06-(11)~
(2004-(06)~)?
2004?-(06)?~
(2004)?-05-04~
(2011)-06-04~
2011-23~
156u-12-25
15uu-12-25
15uu-12-uu
1560-uu-25
[1667,1668, 1670..1672]
[..1760-12-03]
[1760-12..]
[1760-01, 1760-02, 1760-12..]
[1667, 1760-12]
{1667,1668, 1670..1672}
{1960, 1961-12}
196x
19xx
2004-05-(01)~/2004-05-(20)~
2004-05-uu/2004-08-03
y17e7
y-17e7
y17101e4p3""".splitlines()
    for s in tests:
        try:
            print(s, dateTimeString.parseString(s, parseAll=True))
        except ParseException as pe:
            print(s, pe)