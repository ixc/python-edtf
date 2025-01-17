"""Utilities to derive an EDTF string from an (English) natural language string."""

import re
from datetime import datetime
from typing import Optional

from dateutil.parser import ParserError, parse

from edtf import appsettings

# two dates where every digit of an ISO date representation is different,
# and one is in the past and one is in the future.
# This is used in the dateutil parse to detect which elements weren't parsed.
DEFAULT_DATE_1 = datetime(1234, 1, 1, 0, 0)
DEFAULT_DATE_2 = datetime(5678, 10, 10, 0, 0)

LONG_YEAR_RE = re.compile(r"y(-?)([1-9]\d\d\d\d+)")
CENTURY_RE = re.compile(r"(\d{1,2})(c\.?|(st|nd|rd|th) century)\s?(ad|ce|bc|bce)?")
CENTURY_RANGE = re.compile(r"\b(\d\d)(th|st|nd|rd|)-(\d\d)(th|st|nd|rd) [cC]")
CE_RE = re.compile(r"(\d{1,4}) (ad|ce|bc|bce)")
ONE_DIGIT_PARTIAL_FIRST = re.compile(r"\d\D\b")
TWO_DIGIT_PARTIAL_FIRST = re.compile(r"\d\d\b")
PARTIAL_CHECK = re.compile(r"\b\d\d\d\d$")
SLASH_YEAR = re.compile(r"(\d\d\d\d)/(\d\d\d\d)")
BEFORE_CHECK = re.compile(r"\b(?:before|earlier|avant)\b")
AFTER_CHECK = re.compile(r"\b(after|since|later|aprés|apres)\b")
APPROX_CHECK = re.compile(
    r"\b(?:ca?\.? ?\d{4}|circa|approx|approximately|around|about|~\d{3,4})|^~"
)
UNCERTAIN_CHECK = re.compile(r"\b(?:uncertain|possibly|maybe|guess|\d{3,4}\?)")
UNCERTAIN_REPL = re.compile(r"(\d{4})\?")
MIGHT_BE_CENTURY = re.compile(r"(\d{2}00)s")
MIGHT_BE_DECADE = re.compile(r"(\d{3}0)s")

APPROX_CENTURY_RE = re.compile(
    r"\b(ca?\.?) ?(\d{1,2})(c\.?|(st|nd|rd|th) century)\s?(ad|ce|bc|bce)?"
)
UNCERTAIN_CENTURY_RE = re.compile(
    r"(\d{1,2})(c\.?|(st|nd|rd|th) century)\s?(ad|ce|bc|bce)?\?"
)

APPROX_CE_RE = re.compile(r"\b(ca?\.?) ?(\d{1,4}) (ad|ce|bc|bce)")
UNCERTAIN_CE_RE = re.compile(r"(\d{1,4}) (ad|ce|bc|bce)\?")

MENTIONS_YEAR = re.compile(r"\byear\b.+(in|during)\b")
MENTIONS_MONTH = re.compile(r"\bmonth\b.+(in|during)\b")
MENTIONS_DAY = re.compile(r"\bday\b.+(in|during)\b")

# Set of RE rules that will cause us to abort text processing, since we know
# the results will be wrong.
REJECT_RULES = re.compile(r".*dynasty.*")  # Don't parse '23rd Dynasty' to 'uuuu-uu-23'


# @functools.lru_cache
def text_to_edtf(text: str) -> Optional[str]:
    """
    Generate EDTF string equivalent of a given natural language date string.
    """
    if not text:
        return None

    t = text.lower()

    # try parsing the whole thing
    result: Optional[str] = text_to_edtf_date(t)

    if not result:
        # split by list delims and move fwd with the first thing that returns a non-empty string.
        # TODO: assemble multiple dates into a {} or [] structure.
        for split in [",", ";", "or"]:
            for list_item in t.split(split):
                # try parsing as an interval - split by '-'
                toks: list[str] = list_item.split("-")

                if len(toks) == 2:
                    d1 = toks[0].strip()
                    d2 = toks[1].strip()

                    # match looks from the beginning of the string, search
                    # looks anywhere.

                    if re.match(
                        ONE_DIGIT_PARTIAL_FIRST, d2
                    ):  # 1-digit year partial e.g. 1868-9
                        if re.search(
                            PARTIAL_CHECK, d1
                        ):  # TODO: evaluate it and see if it's a year
                            d2 = d1[-4:-1] + d2
                    elif re.match(
                        TWO_DIGIT_PARTIAL_FIRST, d2
                    ):  # 2-digit year partial e.g. 1809-10
                        if re.search(PARTIAL_CHECK, d1):
                            d2 = d1[-4:-2] + d2
                    else:
                        century_range_match = re.search(CENTURY_RANGE, f"{d1}-{d2}")
                        if century_range_match:
                            g = century_range_match.groups()
                            d1 = f"{g[0]}C"
                            d2 = f"{g[2]}C"

                    r1 = text_to_edtf_date(d1)
                    r2 = text_to_edtf_date(d2)

                    if r1 and r2:
                        result = f"{r1}/{r2}"
                        return result

                # is it an either/or year "1838/1862" - that has a different
                # representation in EDTF. If it's 'both', then we use {}. If
                # it's 'or' then we use []. Assuming the latter for now.
                # This whole section could be more friendly.

                else:
                    int_match = re.search(SLASH_YEAR, list_item)
                    if int_match:
                        return f"[{int_match.group(1)}, {int_match.group(2)}]"

                result = text_to_edtf_date(list_item)
                if result:
                    break
            if result:
                break

    is_before = re.findall(BEFORE_CHECK, t)
    is_after = re.findall(AFTER_CHECK, t)

    if is_before:
        result = f"/{result}"
    elif is_after:
        result = f"{result}/"

    return result


# @functools.lru_cache
def text_to_edtf_date(text: str) -> Optional[str]:
    """
    Return EDTF string equivalent of a given natural language date string.

    The approach here is to parse the text twice, with different default
    dates. Then compare the results to see what differs - the parts that
    differ are undefined.
    """
    if not text:
        return None

    t = text.lower()
    result: str = ""

    if re.match(REJECT_RULES, t):
        return None

    # matches on '1800s'. Needs to happen before is_decade.
    could_be_century: list = re.findall(MIGHT_BE_CENTURY, t)
    # matches on '1800s' and '1910s'. Removes the 's'.
    # Needs to happen before is_uncertain because e.g. "1860s?"
    t, is_decade = re.subn(MIGHT_BE_DECADE, r"\1", t)

    # detect approximation signifiers
    # a few 'circa' abbreviations just before the year
    is_approximate = re.findall(APPROX_CHECK, t)
    # the word 'circa' anywhere

    # detect uncertainty signifiers
    t, is_uncertain = re.subn(UNCERTAIN_REPL, r"\1", t)
    is_uncertain = is_uncertain or re.findall(UNCERTAIN_CHECK, t)

    # detect century forms
    is_century = re.findall(CENTURY_RE, t)

    # detect CE/BCE year form
    is_ce = re.findall(CE_RE, t)
    if is_century:
        result = f"{int(is_century[0][0]) - 1:02d}XX"
        is_approximate = is_approximate or re.findall(APPROX_CENTURY_RE, t)
        is_uncertain = is_uncertain or re.findall(UNCERTAIN_CENTURY_RE, t)

        try:
            if is_century[0][-1] in ("bc", "bce"):
                result = f"-{result}"
        except IndexError:
            pass

    elif is_ce:
        result = f"{int(is_ce[0][0]):04d}"
        is_approximate = is_approximate or re.findall(APPROX_CE_RE, t)
        is_uncertain = is_uncertain or re.findall(UNCERTAIN_CE_RE, t)

        try:
            if is_ce[0][-1] in ("bc", "bce"):
                result = f"-{result}"
        except IndexError:
            pass

    else:
        # try dateutil.parse
        try:
            # parse twice, using different defaults to see what was
            # parsed and what was guessed.
            dt1 = parse(
                t,
                dayfirst=appsettings.DAY_FIRST,
                yearfirst=False,
                fuzzy=True,  # force a match, even if it's default date
                default=DEFAULT_DATE_1,
            )

            dt2 = parse(
                t,
                dayfirst=appsettings.DAY_FIRST,
                yearfirst=False,
                fuzzy=True,  # force a match, even if it's default date
                default=DEFAULT_DATE_2,
            )

        except ParserError:
            return
        except Exception:
            return

        if dt1.date() == DEFAULT_DATE_1.date() and dt2.date() == DEFAULT_DATE_2.date():
            # couldn't parse anything - defaults are untouched.
            return None

        date1 = dt1.isoformat()[:10]
        date2 = dt2.isoformat()[:10]

        # guess precision of 'unspecified' characters to use
        mentions_year = re.findall(MENTIONS_YEAR, t)
        mentions_month = re.findall(MENTIONS_MONTH, t)
        mentions_day = re.findall(MENTIONS_DAY, t)

        for i, char in enumerate(date1):
            # if the given year could be a century (e.g. '1800s') then use
            # approximate/uncertain markers to decide whether we treat it as
            # a century or a decade.
            if i == 2 and could_be_century and not (is_approximate or is_uncertain):
                result += "X"
            elif i == 3 and is_decade:
                if mentions_year:
                    result += "X"  # year precision
                else:
                    result += "X"  # decade precision
            elif char == date2[i]:
                # since both attempts at parsing produced the same result
                # it must be parsed value, not a default
                result += char
            else:
                # different values were produced, meaning that it's likely
                # a default. Use 'unspecified'
                result += "X"

        # strip off unknown chars from end of string - except the first 4

        for i in reversed(range(len(result))):
            if result[i] not in ("X", "-"):
                smallest_length = 4

                if mentions_month:
                    smallest_length = 7
                if mentions_day:
                    smallest_length = 10

                limit = max(smallest_length, i + 1)
                result = result[:limit]
                break

        # check for seasons
        if "spring" in t:
            result = result[:4] + "-21" + result[7:]
        elif "summer" in t:
            result = result[:4] + "-22" + result[7:]
        elif "autumn" in t or "fall" in t:
            result = result[:4] + "-23" + result[7:]
        elif "winter" in t:
            result = result[:4] + "-24" + result[7:]

            # end dateutil post-parsing

    if is_uncertain and is_approximate:
        result += "%"
    else:
        if is_uncertain:
            result += "?"
        if is_approximate:
            result += "~"

    # weed out bad parses
    if result.startswith("XX-XX"):
        return None

    return result
