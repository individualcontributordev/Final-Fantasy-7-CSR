"""Calculate PSX MODE2 Form 1 EDC/ECC for in-memory raw sectors.

Form 1 sectors are 2352 bytes: 12 sync, 4 address/mode, 8 duplicated XA
subheader, 2048 user bytes, 4 EDC bytes, and 276 P/Q ECC bytes. Form 2 uses
the sector budget for a larger 2336-byte payload and must not receive Form 1
ECC; ``repair_sector_edc_ecc`` therefore leaves Form 2 unchanged.

Functions mutate caller-provided bytearrays and write no files. The algorithm
is the Neill Corlett ECM/CD-XA layout used by the staged builders; callers must
still preserve sync/header/subheader bytes and verify image alignment.
"""

# Pre-computed EDC CRC table (polynomial 0xD8018001)
_EDC_TABLE = None

def _init_edc_table():
    """Initialize EDC CRC lookup table."""
    global _EDC_TABLE
    if _EDC_TABLE is not None:
        return

    _EDC_TABLE = []
    for i in range(256):
        edc = i
        for _ in range(8):
            edc = (edc >> 1) ^ (0xD8018001 if (edc & 1) else 0)
        _EDC_TABLE.append(edc)


def compute_edc(data: bytes) -> int:
    """
    Compute EDC (CRC-32) for Mode 2 Form 1 sector data.

    Args:
        data: Data to compute EDC for (header + subheader + user data)

    Returns:
        32-bit EDC value
    """
    _init_edc_table()

    edc = 0
    for byte_val in data:
        edc = (edc >> 8) ^ _EDC_TABLE[(edc ^ byte_val) & 0xFF]
    return edc


# Precomputed Galois-field tables for ECC P/Q parity generation.
_ECC_F_LUT = None
_ECC_B_LUT = None


def _init_ecc_tables():
    """Initialize the GF(256) forward/backward LUTs used by the ECC RS code."""
    global _ECC_F_LUT, _ECC_B_LUT
    if _ECC_F_LUT is not None:
        return
    _ECC_F_LUT = [0] * 256
    _ECC_B_LUT = [0] * 256
    for i in range(256):
        j = ((i << 1) ^ (0x11D if i & 0x80 else 0)) & 0xFF
        _ECC_F_LUT[i] = j
        _ECC_B_LUT[i ^ j] = i


def _ecc_writepq(sector: bytearray, major_count: int, minor_count: int,
                  major_mult: int, minor_inc: int, ecc_dest_off: int) -> None:
    """Port of Neill Corlett's ecm.c ecc_writepq(). `address` is always the
    4-byte zero-address (Mode 2 Form 1 uses zeroaddress, not the real header),
    and `data` is sector[16:] (subheader+data+EDC+, for Q, the just-written P
    parity). Writes P or Q parity bytes at sector[2076+ecc_dest_off:...].
    """
    size = major_count * minor_count
    for major in range(major_count):
        index = (major >> 1) * major_mult + (major & 1)
        ecc_a = 0
        ecc_b = 0
        for _minor in range(minor_count):
            temp = 0 if index < 4 else sector[16 + (index - 4)]
            index += minor_inc
            if index >= size:
                index -= size
            ecc_a ^= temp
            ecc_b ^= temp
            ecc_a = _ECC_F_LUT[ecc_a]
        ecc_a = _ECC_B_LUT[_ECC_F_LUT[ecc_a] ^ ecc_b]
        sector[2076 + ecc_dest_off + major] = ecc_a
        sector[2076 + ecc_dest_off + major + major_count] = ecc_a ^ ecc_b


def compute_ecc(sector: bytearray):
    """
    Compute and write ECC (P and Q parity) for Mode 2 Form 1 sector.

    Faithful port of the CD-XA Mode 2 Form 1 ECC algorithm from ecm.c
    (Neill Corlett), also used by mkpsxiso. Modifies sector in-place,
    writing 276 bytes of ECC starting at offset 2076: P parity (172 bytes)
    at 2076, Q parity (104 bytes) at 2248. Q parity's read window naturally
    extends into the just-written P parity bytes -- this is intentional and
    matches the spec (Q covers header+subheader+data+EDC+P).

    Args:
        sector: 2352-byte Mode 2 Form 1 sector (will be modified)
    """
    _init_ecc_tables()
    _ecc_writepq(sector, 86, 24, 2, 86, 0x000)  # P -> sector[2076:2248]
    _ecc_writepq(sector, 52, 43, 86, 88, 0x0AC)  # Q -> sector[2248:2352]


def repair_sector_edc_ecc(sector: bytearray):
    """
    Recalculate and fix EDC/ECC for a Mode 2 Form 1 sector.
    
    Modifies sector in-place.
    
    Args:
        sector: 2352-byte Mode 2 Form 1 sector (will be modified)
    """
    # The XA submode Form bit is authoritative here: generating P/Q parity for
    # a Form 2 data/movie sector would overwrite part of its payload.
    if len(sector) != 2352:
        return
    
    # Mode 2 Form 1 check: subheader[2] & 0x20 == 0
    if sector[16 + 2] & 0x20:
        return  # Mode 2 Form 2, no EDC/ECC
    
    # Compute EDC for bytes 16-2071 (subheader + data only -- sync/header is
    # excluded per CD-XA Mode2 Form1, and the 4 EDC bytes at 2072 must not be
    # included since we're about to overwrite them). Verified against
    # pristine-disc sector 0's already-valid EDC.
    edc_data = sector[16:2072]
    edc = compute_edc(edc_data)
    
    # Write EDC (little-endian)
    sector[2072:2076] = edc.to_bytes(4, 'little')
    
    # Compute and write ECC
    compute_ecc(sector)


def repair_image_edc_ecc(img: bytearray):
    """
    Repair EDC/ECC for all Mode 2 Form 1 sectors in a disc image.
    
    Modifies image in-place.
    
    Args:
        img: PSX disc image (will be modified)
    """
    sector_size = 2352
    total_sectors = len(img) // sector_size
    
    for sector_num in range(total_sectors):
        offset = sector_num * sector_size
        sector = img[offset:offset + sector_size]
        repair_sector_edc_ecc(sector)
