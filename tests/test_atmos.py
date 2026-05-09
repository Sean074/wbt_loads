import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src import atmos


def test_tas_to_cas_sea_level():
    # At sea level TAS = EAS = CAS for any speed
    v_tas = 100.0
    cas = atmos.tas_to_cas(v_tas, h_m=0.0)
    assert math.isclose(cas, v_tas, rel_tol=1e-6)


def test_tas_to_cas_at_altitude():
    # At 10 000 m, Mach ~0.5: CAS < TAS and CAS > 0
    h_m = 10_000.0
    a_m_s = atmos.speed_of_sound(h_m)
    v_tas = 0.5 * a_m_s
    cas = atmos.tas_to_cas(v_tas, h_m)
    assert cas > 0.0
    assert cas < v_tas


def test_tas_to_cas_compressibility():
    # CAS > EAS at altitude (compressibility correction)
    h_m = 8_000.0
    v_eas = 120.0
    v_tas = atmos.eas_to_tas(v_eas, h_m)
    cas = atmos.tas_to_cas(v_tas, h_m)
    assert cas > v_eas
