from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509 import SubjectAlternativeName, UniformResourceIdentifier
import datetime
import pathlib

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "ot-client")])
now = datetime.datetime.now(datetime.timezone.utc)
cert = (
    x509.CertificateBuilder()
    .subject_name(name)
    .issuer_name(name)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(now)
    .not_valid_after(now + datetime.timedelta(days=3650))
    .add_extension(
        SubjectAlternativeName([UniformResourceIdentifier("urn:ot-workbench:client")]),
        critical=False,
    )
    .sign(key, hashes.SHA256())
)
p = pathlib.Path("/app/pki")
p.mkdir(parents=True, exist_ok=True)
(p / "client.pem").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
(p / "client-key.pem").write_bytes(
    key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
)
