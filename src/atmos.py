import math
import numpy as np

G_M_S2      = 9.80665
RHO_0_KG_M3 = 1.2250
P_0_PA      = 101325.0
T_0_K       = 288.15
GAMMA       = 1.4

_L_K_M   = -0.0065   # lapse rate K/m (troposphere)
_H_TROP  = 11000.0   # tropopause altitude, m
_T_TROP  = T_0_K + _L_K_M * _H_TROP
_P_TROP  = P_0_PA * (_T_TROP / T_0_K) ** (G_M_S2 / (-_L_K_M * 287.058))
_RHO_TROP = RHO_0_KG_M3 * (_T_TROP / T_0_K) ** (G_M_S2 / (-_L_K_M * 287.058) - 1)

_R_AIR   = 287.058   # specific gas constant for dry air, J/(kg·K)
_A_0_M_S = math.sqrt(GAMMA * _R_AIR * T_0_K)  # sea-level speed of sound, m/s

H_MAX_M  = 15545.0   # maximum valid altitude, m (~51 000 ft)


def _check_altitude(h_m: float) -> None:
    if not (0.0 <= h_m <= H_MAX_M):
        raise ValueError(f"Altitude {h_m:.1f} m is outside valid range 0 – {H_MAX_M:.0f} m")


def temperature(h_m: float) -> float:
    _check_altitude(h_m)
    if h_m <= _H_TROP:
        return T_0_K + _L_K_M * h_m
    return _T_TROP


def pressure(h_m: float) -> float:
    _check_altitude(h_m)
    if h_m <= _H_TROP:
        t = temperature(h_m)
        return P_0_PA * (t / T_0_K) ** (G_M_S2 / (-_L_K_M * _R_AIR))
    return _P_TROP * math.exp(-G_M_S2 * (h_m - _H_TROP) / (_R_AIR * _T_TROP))


def density(h_m: float) -> float:
    _check_altitude(h_m)
    return pressure(h_m) / (_R_AIR * temperature(h_m))


def speed_of_sound(h_m: float) -> float:
    _check_altitude(h_m)
    return math.sqrt(GAMMA * _R_AIR * temperature(h_m))


def eas_to_tas(v_eas_m_s: float, h_m: float) -> float:
    _check_altitude(h_m)
    rho = density(h_m)
    return v_eas_m_s * math.sqrt(RHO_0_KG_M3 / rho)


def tas_to_cas(v_tas_m_s: float, h_m: float) -> float:
    _check_altitude(h_m)
    p    = pressure(h_m)
    mach = v_tas_m_s / speed_of_sound(h_m)
    q_c  = p * ((1.0 + 0.2 * mach ** 2) ** 3.5 - 1.0)
    return _A_0_M_S * math.sqrt(5.0 * ((q_c / P_0_PA + 1.0) ** (2.0 / 7.0) - 1.0))


def dynamic_pressure(v_tas_m_s: float, h_m: float) -> float:
    _check_altitude(h_m)
    rho = density(h_m)
    return 0.5 * rho * v_tas_m_s ** 2
