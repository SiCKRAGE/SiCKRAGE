import base64
import os
import zlib

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key

import sickrage


def initialize():
    private_key_filename = os.path.join(sickrage.app.data_dir, 'privatekey.pem')
    private_key = load_private_key(private_key_filename)
    if not private_key:
        save_private_key(private_key_filename, generate_private_key())


def generate_private_key():
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )


def verify_public_key(public_key, private_key):
    try:
        decrypt_string(encrypt_string(b'sickrage', public_key), private_key) == b'sickrage'
    except ValueError:
        return False
    return True


def load_public_key(filename):
    if not os.path.exists(filename):
        return

    try:
        with open(filename, 'rb') as fd:
            public_key = load_pem_public_key(fd.read(), default_backend())
        return public_key
    except Exception:
        return


def load_private_key(filename):
    if not os.path.exists(filename):
        return

    try:
        with open(filename, 'rb') as fd:
            private_key = load_pem_private_key(fd.read(), None, default_backend())
        return private_key
    except Exception:
        return


def save_public_key(filename, public_key):
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    with open(filename, 'wb') as fd:
        fd.write(pem)


def save_private_key(filename, private_key):
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    with open(filename, 'wb') as fd:
        fd.write(pem)


def encrypt_file(filename, public_key):
    chunk_size = 245
    offset = 0
    end_loop = False
    encrypted = b""

    with open(filename, 'rb') as fd:
        blob = zlib.compress(fd.read())

    while not end_loop:
        chunk = blob[offset:offset + chunk_size]

        if len(chunk) % chunk_size != 0:
            end_loop = True
            chunk += b" " * (chunk_size - len(chunk))

        encrypted += public_key.encrypt(
            chunk,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        offset += chunk_size

    with open(filename, 'wb') as fd:
        fd.write(base64.b64encode(encrypted))


def decrypt_file(filename, private_key):
    chunk_size = 512
    offset = 0
    decrypted = b""

    with open(filename, 'rb') as fd:
        encrypted_blob = base64.b64decode(fd.read())

    while offset < len(encrypted_blob):
        chunk = encrypted_blob[offset: offset + chunk_size]

        decrypted += private_key.decrypt(
            chunk,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        offset += chunk_size

    with open(filename, 'wb') as fd:
        fd.write(zlib.decompress(decrypted))


def encrypt_string(string, public_key):
    chunk_size = 245
    offset = 0
    end_loop = False
    encrypted = b""

    blob = zlib.compress(string)
    while not end_loop:
        chunk = blob[offset:offset + chunk_size]

        if len(chunk) % chunk_size != 0:
            end_loop = True
            chunk += b" " * (chunk_size - len(chunk))

        encrypted += public_key.encrypt(
            chunk,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        offset += chunk_size

    return base64.b64encode(encrypted)


def decrypt_string(string, private_key):
    chunk_size = 512
    offset = 0
    decrypted = b""

    encrypted_blob = base64.b64decode(string)
    while offset < len(encrypted_blob):
        chunk = encrypted_blob[offset: offset + chunk_size]

        decrypted += private_key.decrypt(
            chunk,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        offset += chunk_size

    return zlib.decompress(decrypted)