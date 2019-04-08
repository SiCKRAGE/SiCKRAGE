import base64
import json
import os
import zlib

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key

import sickrage
from sickrage.core.api import API


def initialize():
    if not API().token:
        return

    public_key_filename = os.path.join(sickrage.app.data_dir, 'sickrage.pub')
    if os.path.exists(public_key_filename):
        sickrage.app.public_key = load_public_key(public_key_filename)
        sickrage.app.log.info("Attempting to load private key from user profile via SiCKRAGE API")
        while True:
            sickrage.app.private_key = load_private_key()
            if sickrage.app.private_key:
                sickrage.app.log.info("Private key loaded from user profile via SiCKRAGE API")
                break
    else:
        sickrage.app.private_key = generate_private_key()
        sickrage.app.public_key = sickrage.app.private_key.public_key()
        sickrage.app.log.info("Attempting to save private key to user profile via SiCKRAGE API")
        while True:
            if save_private_key(sickrage.app.private_key):
                save_public_key(public_key_filename, sickrage.app.public_key)
                sickrage.app.log.info("Private key saved to user profile via SiCKRAGE API")
                break


def generate_private_key():
    return rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )


def load_public_key(filename):
    try:
        with open(filename, 'rb') as fd:
            public_key = load_pem_public_key(fd.read(), default_backend())
        return public_key
    except Exception:
        return


def load_private_key():
    try:
        result = API().download_privatekey()
        private_key = load_pem_private_key(base64.b64decode(result['pem']), None, default_backend())
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


def save_private_key(private_key):
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    try:
        API().upload_privatekey(base64.b64encode(pem))
    except Exception:
        return False

    return True


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
