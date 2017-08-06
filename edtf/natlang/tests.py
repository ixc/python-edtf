import unittest
from en import text_to_edtf

# where examples are tuples, the second item is the normalised output
EXAMPLES = (
    ('active late 17th-19th centuries', '16xx/18xx'), # ignoring 'late' for now
    ('active 17-19th Centuries', '16xx/18xx'), # ignoring 'late' for now

    ('', None),
    ('this isn\'t a date', None),
    ('90', '1990'),  # implied century
    ('1860', '1860'),
    ('the year 1800', '1800'),
    ('the year 1897', '1897'),
    ('January 2008', '2008-01'),
    ('January 12, 1940', '1940-01-12'),

    # uncertain/approximate
    ('1860?', '1860?'),
    ('1862 (uncertain)', '1862?'),
    ('maybe 1862', '1862?'),
    ('1862 maybe', '1862?'),
    ('1862 guess', '1862?'),
    ('uncertain: 1862', '1862?'),
    ('uncertain: Jan 18 1862', '1862-01-18?'),
    ('~ Feb 1812', '1812-02~'),
    ('circa Feb 1812', '1812-02~'),
    ('Feb 1812 approx', '1812-02~'),
    ('c1860', '1860~'),  # different abbreviations
    ('c.1860', '1860~'),  # with or without .
    ('ca1860', '1860~'),
    ('ca.1860', '1860~'),
    ('c 1860', '1860~'),  # with or without space
    ('c. 1860', '1860~'),
    ('ca. 1860', '1860~'),
    ('approx 1860', '1860~'),
    ('1860 approx', '1860~'),
    ('1860 approximately', '1860~'),
    ('approximately 1860', '1860~'),
    ('about 1860', '1860~'),
    ('about Spring 1849', '1849-21~'),
    ('notcirca 1860', '1860'),  # avoid words containing circa
    ('attica 1802', '1802'),
    # avoid false positive circa at the end of preceding word
    ('attic. 1802', '1802'),  # avoid false positive circa

    # masked precision
    ('1860s', '186x'),  # 186x has decade precision, 186u has year precision.

    # masked precision + uncertainty
    ('ca. 1860s', '186x~'),
    ('c. 1860s', '186x~'),
    ('Circa 1840s', '184x~'),
    ('circa 1840s', '184x~'),
    ('ca. 1860s?', '186x?~'),
    ('uncertain: approx 1862', '1862?~'),

    # masked precision with first decade (ambiguous)
    ('1800s', '18xx'),  # without additional uncertainty, use the century
    ('2000s', '20xx'),  # without additional uncertainty, use the century
    ('c1900s', '190x~'),  # if there's additional uncertainty, use the decade
    ('c1800s?', '180x?~'),  # if there's additional uncertainty, use the decade

    # unspecified
    ('January 12', 'uuuu-01-12'),
    ('January', 'uuuu-01'),
    ('10/7/2008', '2008-10-07'),
    ('7/2008', '2008-07'),

    # seasons
    ('Spring 1872', '1872-21'),
    ('Summer 1872', '1872-22'),
    ('Autumn 1872', '1872-23'),
    ('Fall 1872', '1872-23'),
    ('Winter 1872', '1872-24'),

    # before/after
    ('earlier than 1928', 'unknown/1928'),
    ('before 1928', 'unknown/1928'),
    ('after 1928', '1928/unknown'),
    ('later than 1928', '1928/unknown'),
    ('before January 1928', 'unknown/1928-01'),
    ('before 18 January 1928', 'unknown/1928-01-18'),

    # before/after approx
    ('before approx January 18 1928', 'unknown/1928-01-18~'),
    ('before approx January 1928', 'unknown/1928-01~'),
    ('after approx January 1928', '1928-01~/unknown'),
    ('after approx Summer 1928', '1928-22~/unknown'),

    # before/after and uncertain/unspecificed
    ('after about the 1920s', '192x~/unknown'),
    ('before about the 1900s', 'unknown/190x~'),
    ('before the 1900s', 'unknown/19xx'),

    # unspecified
    # ('decade in 1800s', '18ux'), #too esoteric
    # ('decade somewhere during the 1800s', '18ux'), #lengthier. Keywords are 'in' or 'during'
    ('year in the 1860s', '186u'),
    # 186x has decade precision, 186u has year precision.
    ('year in the 1800s', '18xu'),
    ('year in about the 1800s', '180u~'),
    ('month in 1872', '1872-uu'),
    ('day in Spring 1849', '1849-21-uu'),
    ('day in January 1872', '1872-01-uu'),
    ('day in 1872', '1872-uu-uu'),
    ('birthday in 1872', '1872'),
    # avoid false positive at end of preceding word

    # centuries
    ('1st century', '00xx'),
    ('10c', '09xx'),
    ('19th century', '18xx'),
    ('19th century?', '18xx?'),
    ('before 19th century', 'unknown/18xx'),
    ('19c', '18xx'),
    ('15c.', '14xx'),
    ('ca. 19c', '18xx~'),
    ('~19c', '18xx~'),
    ('about 19c', '18xx~'),
    ('19c?', '18xx?'),
    ('c.19c?', '18xx?~'),

    # BC/AD
    ('1 AD', '0001'),
    ('17 CE', '0017'),
    ('127 CE', '0127'),
    ('1270 CE', '1270'),
    ('c1 AD', '0001~'),
    ('c17 CE', '0017~'),
    ('c127 CE', '0127~'),
    ('c1270 CE', '1270~'),
    ('c64 BCE', '-0064~'),
    ('2nd century bc', '-01xx'),  # -200 to -101
    ('2nd century bce', '-01xx'),
    ('2nd century ad', '01xx'),
    ('2nd century ce', '01xx'),

    # c-c-c-combo
    # just showing off now...
    ('a day in about Spring 1849?', '1849-21-uu?~'),

    # simple ranges. Not all of these results are correct EDTF, but
    # this is as good as the EDTF implementation and simple natural
    # language parser we have.
    ('1851-1852', '1851/1852'),
    ('1851-1852; printed 1853-1854', '1851/1852'),
    ('1851-52', '1851/1852'),
    ('1852 - 1860', '1852/1860'),
    ('1856-ca. 1865', '1856/1865~'),
    ('1857-mid 1860s', '1857/186x'),
    ('1858/1860', '[1858, 1860]'),
    ('1860s-1870s', '186x/187x'),
    ('1861, printed 1869', '1861'),
    ('1910-30', '1910/1930'),
    ('active 1910-30', '1910/1930'),
    ('1861-67', '1861/1867'),
    ('1861-67 (later print)', '1861/1867'),
    ('1863 or 1864', '1863'),
    ('1863, printed 1870', '1863'),
    ('1863, printed ca. 1866', '1863'),
    ('1864 or 1866', '1864'),
    ('1864, printed ca. 1864', '1864'),
    ('1864-1872, printed 1870s', '1864/1872'),
    ('1868-1871?', '1868/1871?'),
    ('1869-70', '1869/1870'),
    ('1870s, printed ca. 1880s', '187x'),
    ('1900-1903, cast before 1929', '1900/1903'),
    ('1900; 1973', '1900'),
    ('1900; printed 1912', '1900'),
    ('1915 late - autumn 1916', '1915/1916-23'),

    ('1915, from Camerawork, October 1916', '1915'), # should be {1915, 1916-10}
    ('1920s -early 1930s', '192x/193x'),
    ('1930s, printed early 1960s', '193x'), # should be something like {193x, 196x},
    # though those forms aren't explicitly supported in the spec.
    ('1932, printed 1976 by Gunther Sander', '1932'), # should be {1932, 1976}
    ('1938, printed 1940s-1950s', '1938'), # should be something like {1938, 194x-195x}



    # for these to work we need to recast is_uncertain and is_approximate
    # such that they work on different parts. Probably worth rolling our own
    # dateparser at this point.
    # ('July in about 1849', '1849~-07'),
    # ('a day in July in about 1849', '1849~-07-uu'),
    # ('a day in Spring in about 1849', '1849~-21-uu'),
    # ('a day in about July? in about 1849', '1849~-07?~-uu'),
    # ('a day in about Spring in about 1849', '1849~-21~-uu'),
    # ('maybe January in some year in about the 1830s', '183u~-01?'),
    # ('about July? in about 1849', '1849~-07?~'),
)

class TestLevel0(unittest.TestCase):

    def test_natlang(self):
        """
        For each of the examples, establish that:
            - the unicode of the parsed object is acceptably equal to the EDTF string
            - the parsed object is a subclass of EDTFObject
        :return: 
        """
        for i, o in EXAMPLES:
            e = text_to_edtf(i)
            print "%s => %s" % (i, e)
            self.assertEqual(e, o)



if __name__ == '__main__':
    unittest.main()
