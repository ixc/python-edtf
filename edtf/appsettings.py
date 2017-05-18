from django.conf import settings

EDTF = getattr(settings, 'EDTF', {})

# Sources for `icekit.plugins.FileSystemLayoutPlugin`.



SEASON_MONTHS_RANGE = EDTF.get('SEASON_MONTHS_RANGE', {
        # season id: [earliest_month, last_month]
        21: [3, 5],
        22: [6, 8],
        23: [9, 11],
        # winter in the northern hemisphere wraps the end of the year, so
        # Winter 2010 could wrap into 2011.
        # For simplicity, we assume it falls at the end of the year, esp since the
        # spec says that sort order goes spring > summer > autumn > winter
        24: [12, 12],
    }
)

DAY_FIRST = EDTF.get('DAY_FIRST', False)  # Americans!

SEASONS = EDTF.get('SEASONS', {
    21: "spring",
    22: "summer",
    23: "autumn",
    24: "winter",
})
INVERSE_SEASONS = EDTF.get('INVERSE_SEASONS', {v: k for k, v in SEASONS.items()})
# also need to interpret `fall`
INVERSE_SEASONS['fall'] = 23

# changing this will break tests
PADDING_MULTIPLIER = EDTF.get('PADDING_MULTIPLIER', 1.0)

