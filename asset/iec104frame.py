"""Minimal IEC 60870-5-104 APDU framing primitives.

Covers: reading a complete APDU from a socket, U-frame constants,
and unpacking the fixed ASDU header (type ID, VSQ, COT, CA).
"""
import struct

# U-frames
STARTDT_ACT = bytes([0x68, 0x04, 0x07, 0x00, 0x00, 0x00])
STARTDT_CON = bytes([0x68, 0x04, 0x0B, 0x00, 0x00, 0x00])
STOPDT_ACT  = bytes([0x68, 0x04, 0x13, 0x00, 0x00, 0x00])
STOPDT_CON  = bytes([0x68, 0x04, 0x23, 0x00, 0x00, 0x00])
TESTFR_ACT  = bytes([0x68, 0x04, 0x43, 0x00, 0x00, 0x00])
TESTFR_CON  = bytes([0x68, 0x04, 0x83, 0x00, 0x00, 0x00])


def read_apdu(sock):
    """Read one complete APDU from sock. Returns raw bytes or None on EOF/error."""
    header = _recv_exact(sock, 2)
    if header is None or header[0] != 0x68:
        return None
    length = header[1]
    rest = _recv_exact(sock, length)
    if rest is None:
        return None
    return header + rest


def is_iframe(apdu):
    """True if the APDU is an I-frame (carries an ASDU)."""
    return len(apdu) >= 6 and (apdu[2] & 0x01) == 0


def asdu_header(apdu):
    """Unpack fixed ASDU header from an I-frame.

    Returns (type_id, vsq, cot, ca) or None if too short.
    cot is the full 2-byte cause of transmission (low byte, originator).
    ca  is the 2-byte common address.
    """
    if len(apdu) < 12:
        return None
    # apdu[0:2] = start + length; apdu[2:6] = control field; apdu[6:] = ASDU
    type_id, vsq, cot_lo, cot_hi, ca_lo, ca_hi = struct.unpack_from("<BBBBBB", apdu, 6)
    cot = (cot_hi << 8) | cot_lo
    ca  = (ca_hi  << 8) | ca_lo
    return type_id, vsq, cot, ca


def make_s_frame(rsn):
    """Build a 6-byte S-frame acknowledging all I-frames up to rsn-1."""
    rsn_lo = (rsn & 0x7F) << 1
    rsn_hi = (rsn >> 7) & 0xFF
    return bytes([0x68, 0x04, 0x01, 0x00, rsn_lo, rsn_hi])


def _recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf