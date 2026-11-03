from datetime import datetime, timezone

from astropy.coordinates import (
    GeocentricTrueEcliptic,
    get_body,
    solar_system_ephemeris,
)
from astropy.time import Time


ZODIAC_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)

EPHEMERIS = "de440"


__previous = None


def zodiac_sign(dt: datetime) -> str:
    global __previous
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if __previous is not None and dt == __previous[0]:
        return __previous[1]

    t = Time(dt)
    ecliptic_frame = GeocentricTrueEcliptic(equinox=t, obstime=t)

    # Use the selected JPL ephemeris for the Sun's position.
    with solar_system_ephemeris.set(EPHEMERIS):
        sun = get_body("sun", t)
        sun_ecliptic = sun.transform_to(ecliptic_frame)

    longitude = sun_ecliptic.lon.deg % 360
    output = ZODIAC_SIGNS[int(longitude // 30)]
    __previous = (dt, output)
    return output


if __name__ == "__main__":
    dt = datetime.now(timezone.utc)
    sign = zodiac_sign(dt)
    print(f"Current Time:  {dt}")
    print(f"Sign:          {sign}")
