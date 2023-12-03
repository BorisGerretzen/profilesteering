from Pyfhel import Pyfhel

HE = Pyfhel()
ckks_params = {
    'scheme': 'CKKS', # CKKS scheme supports floating point
    'n': 2**14, # max length of ciphertext is n/2 -> 2**3 = 8192
    'scale': 2**30, # scale factor for CKKS
    'qi_sizes': [60, 30, 30, 30, 60] # prime stuff idk
}
HE.contextGen(**ckks_params)
HE.keyGen()
HE.rotateKeyGen()