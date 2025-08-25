# DHKE.py

from Crypto.Random import get_random_bytes

p = 12980392895343054703014536073914488856684431224038760889795797821148268281653185633271150095369558651013705762317569403202651829160514973546664152667905529
g = 97

class DHKE:
    def __init__(self, p, g):
        self.p = p
        self.g = g
        self.private_key = None
        self.public_key = None
        self.shared_secret = None

    def generate_private_key(self):
        self.private_key = get_random_bytes(32)
        return self.private_key
    
    def generate_public_key(self):
        if self.private_key is None:
            raise ValueError("Private key not generated.")
        private_key_int = int.from_bytes(self.private_key, byteorder='big')
        self.public_key = pow(self.g, private_key_int, self.p)
        return self.public_key

    def compute_shared_secret(self, other_public_key):
        if self.private_key is None:
            raise ValueError("Private key not generated.")
        private_key_int = int.from_bytes(self.private_key, byteorder='big')
        self.shared_secret = pow(other_public_key, private_key_int, self.p)
        return self.shared_secret
