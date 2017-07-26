"""Utilities to derive an EDTF string from an (English) natural language string."""
from datetime import datetime
from dateutil.parser import parse
import re
from edtf import appsettings


# two dates where every digit of an ISO date representation is different,
# and one is in the past and one is in the future.
# This is used in the dateutil parse to detect which elements weren't parsed.
DEFAULT_DATE_1 = datetime(1234, 01, 01, 0, 0)
DEFAULT_DATE_2 = datetime(5678, 10, 10, 0, 0)

SHORT_YEAR_RE = r'(-?)([\du])([\dxu])([\dxu])([\dxu])'
LONG_YEAR_RE = r'y(-?)([1-9]\d\d\d\d+)'
CENTURY_RE = r'(\d{1,2})(c\.?|(st|nd|rd|th) century)\s?(ad|ce|bc|bce)?'
CE_RE = r'(\d{1,4}) (ad|ce|bc|bce)'

def text_to_edtf(text):
    """
    Generate EDTF string equivalent of a given natural language date string.
    """
    if not text:
        return

    t = text.lower()

    # try parsing the whole thing
    result = text_to_edtf_date(t)

    if not result:
        # split by list delims and move fwd with the first thing that returns a non-empty string.
        # TODO: assemble multiple dates into a {} or [] structure.
        for split in [",", ";", "or"]:
            for list_item in t.split(split):

                # try parsing as an interval - split by '-'
                toks = list_item.split("-")
                if len(toks) == 2:
                    d1 = toks[0].strip()
                    d2 = toks[1].strip()

                    # match looks from the beginning of the string, search
                    # looks anywhere.

                    if re.match(r'\d\D\b', d2):  # 1-digit year partial e.g. 1868-9
                        if re.search(r'\b\d\d\d\d$', d1):  # TODO: evaluate it and see if it's a year
                            d2 = d1[-4:-1] + d2
                    elif re.match(r'\d\d\b', d2):  # 2-digit year partial e.g. 1809-10
                        if re.search(r'\b\d\d\d\d$', d1):
                            d2 = d1[-4:-2] + d2
                    else:
                        century_range_match = re.search(r'\b(\d\d)(th|st|nd|rd|)-(\d\d)(th|st|nd|rd) [cC]', "%s-%s" % (d1,d2))
                        if century_range_match:
                            g = century_range_match.groups()
                            d1 = "%sC" % g[0]
                            d2 = "%sC" % g[2]


                    # import pdb; pdb.set_trace()
                    r1 = text_to_edtf_date(d1)
                    r2 = text_to_edtf_date(d2)

                    if r1 and r2:
                        result = r1 + "/" + r2
                        return result

                # is it an either/or year "1838/1862" - that has a different
                # representation in EDTF. If it's 'both', then we use {}. If
                # it's 'or' then we use []. Assuming the latter for now.
                # This whole section could be more friendly.

                else:
                    int_match = re.search(r"(\d\d\d\d)\/(\d\d\d\d)", list_item)
                    if int_match:
                        return "[%s, %s]" % (int_match.group(1), int_match.group(2))

                result = text_to_edtf_date(list_item)
                if result:
                    break
            if result:
                break

    is_before = re.findall(r'\bbefore\b', t)
    is_before = is_before or re.findall(r'\bearlier\b', t)

    is_after = re.findall(r'\bafter\b', t)
    is_after = is_after or re.findall(r'\bsince\b', t)
    is_after = is_after or re.findall(r'\blater\b', t)

    if is_before:
        result = u"unknown/%s" % result
    elif is_after:
        result = u"%s/unknown" % result

    return result


def text_to_edtf_date(text):
    """
    Return EDTF string equivalent of a given natural language date string.

    The approach here is to parse the text twice, with different default
    dates. Then compare the results to see what differs - the parts that
    differ are undefined.
    """
    if not text:
        return

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

    # detect CE/BCE year form
    is_ce = re.findall(CE_RE, t)
    if is_century:
        result = "%02dxx" % (int(is_century[0][0]) - 1,)
        is_approximate = is_approximate or \
                         re.findall(r'\b(ca?\.?) ?' + CENTURY_RE, t)
        is_uncertain = is_uncertain or re.findall(CENTURY_RE + r'\?', t)

        try:
            is_bc = is_century[0][-1] in ("bc", "bce")
            if is_bc:
                result = "-%s" % result
        except IndexError:
            pass

    elif is_ce:
        result = "%04d" % (int(is_ce[0][0]))
        is_approximate = is_approximate or \
                         re.findall(r'\b(ca?\.?) ?' + CE_RE, t)
        is_uncertain = is_uncertain or re.findall(CE_RE + r'\?', t)

        try:
            is_bc = is_ce[0][-1] in ("bc", "bce")
            if is_bc:
                result = "-%s" % result
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
                default=DEFAULT_DATE_1
            )

            dt2 = parse(
                t,
                dayfirst=appsettings.DAY_FIRST,
                yearfirst=False,
                fuzzy=True,  # force a match, even if it's default date
                default=DEFAULT_DATE_2
            )

        except ValueError:
            return

        if dt1.date() == DEFAULT_DATE_1.date() and \
                dt2.date() == DEFAULT_DATE_2.date():
            # couldn't parse anything - defaults are untouched.
            return

        date1 = dt1.isoformat()[:10]
        date2 = dt2.isoformat()[:10]

        # guess precision of 'unspecified' characters to use
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

    if is_uncertain:
        result += "?"

    if is_approximate:
        result += "~"

    # weed out bad parses
    if result.startswith("uu-uu"):
        return None

    return result
