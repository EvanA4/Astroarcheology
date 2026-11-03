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


def zodiac_sign(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    t = Time(dt)
    ecliptic_frame = GeocentricTrueEcliptic(equinox=t, obstime=t)

    # Use the selected JPL ephemeris for the Sun's position.
    with solar_system_ephemeris.set(EPHEMERIS):
        sun = get_body("sun", t)
        sun_ecliptic = sun.transform_to(ecliptic_frame)

    longitude = sun_ecliptic.lon.deg % 360
    return ZODIAC_SIGNS[int(longitude // 30)]


if __name__ == "__main__":
    dt = datetime.now(timezone.utc)
    sign = zodiac_sign(dt)
    print(f"Current Time:  {dt}")
    print(f"Sign:          {sign}")
