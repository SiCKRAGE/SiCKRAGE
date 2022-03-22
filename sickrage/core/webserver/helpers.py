import datetime
import os

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509 import ExtensionNotFound
from cryptography.x509.oid import NameOID

import sickrage


def create_https_certificates(ssl_cert, ssl_key):
    """This function takes a domain name as a parameter and then creates a certificate and key with the
    domain name(replacing dots by underscores), finally signing the certificate using specified CA and
    returns the path of key and cert files. If you are yet to generate a CA then check the top comments"""

    # Generate our key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )

    name = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, 'SiCKRAGE')
    ])

    # path_len=0 means this cert can only sign itself, not other certs.
    basic_contraints = x509.BasicConstraints(ca=True, path_length=0)
    now = datetime.datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(key.public_key())
            .serial_number(1000)
            .not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(days=10 * 365))
            .add_extension(basic_contraints, False)
            # .add_extension(san, False)
            .sign(key, hashes.SHA256(), default_backend())
    )
    cert_pem = cert.public_bytes(encoding=serialization.Encoding.PEM)
    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    with open(ssl_key, 'wb') as key_out:
        key_out.write(key_pem)

    with open(ssl_cert, 'wb') as cert_out:
        cert_out.write(cert_pem)

    return True


def is_certificate_valid(cert_file):
    if not os.path.exists(cert_file):
        return

    with open(cert_file, 'rb') as f:
        cert_pem = f.read()

    cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    issuer = cert.issuer.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0]
    subject = cert.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)[0]

    if 'ZeroSSL' not in issuer.value:
        return False

    if subject.value != f'*.{sickrage.app.config.general.server_id}.sickrage.direct':
        return False

    try:
        ext = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        sans = ext.get_values_for_type(x509.DNSName)

        domains = [f'*.{sickrage.app.config.general.server_id}.sickrage.direct']

        for domain in sans:
            if domain not in domains:
                return False
    except ExtensionNotFound:
        return False

    return True


def certificate_needs_renewal(cert_file):
    if not os.path.exists(cert_file):
        return

    with open(cert_file, 'rb') as f:
        cert_pem = f.read()

    cert_info = x509.load_pem_x509_certificate(cert_pem, default_backend())
    expiry_date = cert_info.not_valid_after
    time_left = expiry_date.date() - datetime.date.today()

    return time_left.days < 1
