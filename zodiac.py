from datetime import datetime, timezone
from astropy.coordinates import GeocentricTrueEcliptic, get_constellation, get_sun
from astropy.time import Time


def zodiac_constellation(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    sun = get_sun(Time(dt))
    return get_constellation(sun)


SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


def zodiac_sign(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    t = Time(dt)
    ecliptic_frame = GeocentricTrueEcliptic(equinox=t, obstime=t)
    sun_ecliptic = get_sun(t).transform_to(ecliptic_frame)

    longitude = sun_ecliptic.lon.deg % 360
    return SIGNS[int(longitude // 30)]


if __name__ == "__main__":
    dt = datetime.now()
    constellation = zodiac_constellation(dt)
    sign = zodiac_sign(dt)
    print(f"Current Time:  {dt}")
    print(f"Constellation: {constellation}")
    print(f"Sign:          {sign}")