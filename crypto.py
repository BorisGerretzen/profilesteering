from enum import Enum

from Pyfhel import Pyfhel

class PrivacySchemes(Enum):
    NONE = 1
    HOMOMORPHIC = 2
    DIFFERENTIAL = 3

PRIVACY_SCHEME = PrivacySchemes.DIFFERENTIAL

HE = Pyfhel()
if PRIVACY_SCHEME == PrivacySchemes.HOMOMORPHIC:
    ckks_params = {
        'scheme': 'CKKS',  # CKKS scheme supports floating point
        'n': 2 ** 14,  # max length of ciphertext is n/2 -> 2**13 = 8192
        'scale': 2 ** 30,  # scale factor for CKKS
        'qi_sizes': [60, 30, 30, 30, 60]  # prime stuff idk
    }
    HE.contextGen(**ckks_params)
    HE.keyGen()
    HE.rotateKeyGen()

DifferentialOptions = {
    "scale": 200,
}
if PRIVACY_SCHEME == PrivacySchemes.DIFFERENTIAL:
    pass