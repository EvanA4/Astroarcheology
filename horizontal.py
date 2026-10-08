import astropy.units as u
from astropy.time import Time
from astropy.coordinates import EarthLocation, AltAz, get_body


def get_horizontal(name: str, t: Time):
    site = EarthLocation(lat=37 * u.deg, lon=-122 * u.deg)
    planet = get_body(name, t, location=site)
    altaz = planet.transform_to(
        AltAz(obstime=t, location=site, pressure=0 * u.hPa)
    )
    return [
        float(altaz.az.to_value(u.rad)),
        float(altaz.alt.to_value(u.rad)),
        float(altaz.distance.to_value(u.au)),
    ]


t = Time.now()
horizontal = get_horizontal('Sun', t)
print(horizontal)