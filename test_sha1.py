from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

def encrypt_aes(key: bytes, data: str) -> str:
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data.encode('utf-8'), AES.block_size))
    iv = base64.b64encode(cipher.iv).decode('utf-8')
    ct = base64.b64encode(ct_bytes).decode('utf-8')
    return iv + ":" + ct

def decrypt_aes(key: bytes, encrypted_data: str) -> str:
    iv, ct = encrypted_data.split(":")
    iv = base64.b64decode(iv)
    ct = base64.b64decode(ct)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(ct), AES.block_size)
    return pt.decode('utf-8')

# Ví dụ sử dụng:
KEY_SHA1 = b'WsCLPSm4V183q2wI1dFkarGZNiZoRIBsmvN16hUn'  # key 16 bytes cho AES-128
data = "this string"

encrypted = encrypt_aes(KEY_SHA1, data)
print("Encrypted:", encrypted)

decrypted = decrypt_aes(KEY_SHA1, encrypted)
print("Decrypted:", decrypted)
