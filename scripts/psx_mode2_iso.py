"""Minimal MODE2/2352 ISO9660 helpers for FF7 FIELD.BIN extract / pad-inject.

Emulators usually tolerate stale sector EDC/ECC (same as ff7tk). We only rewrite
Form 1 user data (2048 bytes per sector) and pad shorter replacements with zeros.
"""

from __future__ import annotations

from dataclasses import dataclass

SECTOR = 2352
USER = 2048
USER_OFF = 24  # sync(12) + header(4) + subheader(8)


@dataclass(frozen=True)
class IsoFile:
    path: str
    lba: int
    size: int
    dir_lba: int = -1
    rec_offset: int = -1


def _user(img: memoryview | bytes | bytearray, lba: int) -> bytes:
    off = lba * SECTOR + USER_OFF
    if off + USER > len(img):
        raise ValueError(f"LBA {lba} past end of image")
    return bytes(img[off : off + USER])


def _write_user(img: bytearray, lba: int, data: bytes) -> None:
    if len(data) != USER:
        raise ValueError(f"sector user data must be {USER} bytes")
    off = lba * SECTOR + USER_OFF
    if off + USER > len(img):
        raise ValueError(f"LBA {lba} past end of image")
    img[off : off + USER] = data


def _u32_le(b: bytes, i: int) -> int:
    return b[i] | (b[i + 1] << 8) | (b[i + 2] << 16) | (b[i + 3] << 24)


def _iso_name(raw: bytes) -> str:
    # "FIELD.BIN;1" or "FIELD" directory
    name = raw.split(b";", 1)[0].decode("ascii", errors="replace").strip()
    return name.upper()


def _parse_dir_records(blob: bytes) -> list[tuple[str, int, int, bool, int]]:
    """Return (name, lba, size, is_dir, rec_offset) for records in a directory extent.

    rec_offset is the byte offset of the record within this extent blob, needed
    to patch the record's size field in place later (see patch_dir_record_size).
    """
    out: list[tuple[str, int, int, bool, int]] = []
    i = 0
    while i < len(blob):
        length = blob[i]
        if length == 0:
            # move to next sector boundary inside this extent blob
            nxt = ((i // USER) + 1) * USER
            if nxt <= i:
                break
            i = nxt
            continue
        if i + length > len(blob):
            break
        rec = blob[i : i + length]
        flags = rec[25]
        name_len = rec[32]
        if name_len == 1 and rec[33] in (0x00, 0x01):
            i += length
            continue
        name = _iso_name(rec[33 : 33 + name_len])
        lba = _u32_le(rec, 2)
        size = _u32_le(rec, 10)
        is_dir = bool(flags & 0x02)
        out.append((name, lba, size, is_dir, i))
        i += length
    return out


def _read_extent(img: memoryview | bytes | bytearray, lba: int, size: int) -> bytes:
    remaining = size
    sector = lba
    chunks: list[bytes] = []
    while remaining > 0:
        user = _user(img, sector)
        take = min(USER, remaining)
        chunks.append(user[:take])
        remaining -= take
        sector += 1
    return b"".join(chunks)


def _list_dir(img: memoryview | bytes | bytearray, lba: int, size: int):
    return _parse_dir_records(_read_extent(img, lba, size))


def patch_dir_record_size(img: bytearray, meta: IsoFile, new_size: int) -> None:
    """Patch a file's directory-record byte-size field (both LE and BE copies) in place.

    ISO9660 directory records never span a sector boundary (encoders pad to the
    next sector rather than split one), so the record lives entirely within one
    2048-byte user-data sector — safe to patch with a single sector read/write.
    """
    if meta.dir_lba < 0 or meta.rec_offset < 0:
        raise ValueError(f"{meta.path}: no directory-record location (use find_file, not list_dir)")
    sector = meta.dir_lba + (meta.rec_offset // USER)
    off = meta.rec_offset % USER
    user = bytearray(_user(img, sector))
    user[off + 10 : off + 14] = new_size.to_bytes(4, "little")
    user[off + 14 : off + 18] = new_size.to_bytes(4, "big")
    _write_user(img, sector, bytes(user))


def find_file(img: bytes | bytearray, path: str) -> IsoFile:
    """Locate a file by ISO path like FIELD/FIELD.BIN (case-insensitive)."""
    parts = [p for p in path.replace("\\", "/").upper().split("/") if p]
    if not parts:
        raise ValueError("empty path")

    if len(img) % SECTOR != 0:
        raise ValueError(f"image size {len(img)} is not a multiple of {SECTOR}")

    pvd = _user(img, 16)
    if pvd[0] != 1 or pvd[1:6] != b"CD001":
        raise ValueError("Primary Volume Descriptor not found at LBA 16")

    root = pvd[156 : 156 + 34]
    dir_lba = _u32_le(root, 2)
    dir_size = _u32_le(root, 10)

    for idx, part in enumerate(parts):
        entries = _list_dir(img, dir_lba, dir_size)
        match = next((e for e in entries if e[0] == part), None)
        if match is None:
            names = ", ".join(e[0] for e in entries[:20])
            raise FileNotFoundError(
                f"missing {part!r} under {'/'.join(parts[:idx]) or '[root]'} "
                f"(saw: {names}{'…' if len(entries) > 20 else ''})"
            )
        name, lba, size, is_dir, rec_offset = match
        is_last = idx == len(parts) - 1
        if is_last:
            if is_dir:
                raise IsADirectoryError(path)
            return IsoFile(
                path="/".join(parts),
                lba=lba,
                size=size,
                dir_lba=dir_lba,
                rec_offset=rec_offset,
            )
        if not is_dir:
            raise NotADirectoryError("/".join(parts[: idx + 1]))
        dir_lba, dir_size = lba, size

    raise FileNotFoundError(path)


def extract_file(img: bytes | bytearray, path: str) -> bytes:
    meta = find_file(img, path)
    return _read_extent(img, meta.lba, meta.size)


def replace_file(img: bytearray, path: str, new_data: bytes) -> IsoFile:
	"""Replace file contents in-place, zero-padded to a whole number of sectors.

	The file keeps its original LBA and allocated sector span. Growth is allowed
	as long as it still fits that span (ceil(new_size / 2048) <= sectors already
	allocated); the directory record's size field (LE + BE) is patched to match
	the new exact byte length whenever it differs from the pristine size. Growth
	past the allocated span is refused — that needs a full ISO rebuild.
	"""
	meta = find_file(img, path)
	old_slots = -(-meta.size // USER)
	new_slots = -(-len(new_data) // USER)
	if new_slots > old_slots:
		raise ValueError(
			f"{path}: new file is {len(new_data)} bytes, needs {new_slots} sectors "
			f"but only {old_slots} are allocated at LBA {meta.lba} "
			"(longer inject not supported — full ISO rebuild required)"
		)
	payload = new_data + (b"\x00" * (new_slots * USER - len(new_data)))

	sector = meta.lba
	for offset in range(0, len(payload), USER):
		_write_user(img, sector, payload[offset : offset + USER])
		sector += 1

	if len(new_data) != meta.size:
		patch_dir_record_size(img, meta, len(new_data))

	return IsoFile(path=meta.path, lba=meta.lba, size=len(new_data), dir_lba=meta.dir_lba, rec_offset=meta.rec_offset)


def list_dir(img: bytes | bytearray, path: str = "") -> list[IsoFile]:
	"""List files (not subdirs) under an ISO directory path ('' = root)."""
	parts = [p for p in path.replace("\\", "/").upper().split("/") if p]

	if len(img) % SECTOR != 0:
		raise ValueError(f"image size {len(img)} is not a multiple of {SECTOR}")

	pvd = _user(img, 16)
	if pvd[0] != 1 or pvd[1:6] != b"CD001":
		raise ValueError("Primary Volume Descriptor not found at LBA 16")

	root = pvd[156 : 156 + 34]
	dir_lba = _u32_le(root, 2)
	dir_size = _u32_le(root, 10)

	for idx, part in enumerate(parts):
		entries = _list_dir(img, dir_lba, dir_size)
		match = next((e for e in entries if e[0] == part), None)
		if match is None:
			raise FileNotFoundError(f"missing directory {part!r} in {path or '[root]'}")
		name, lba, size, is_dir, _rec_offset = match
		if not is_dir:
			raise NotADirectoryError("/".join(parts[: idx + 1]))
		dir_lba, dir_size = lba, size

	prefix = "/".join(parts)
	out: list[IsoFile] = []
	for name, lba, size, is_dir, rec_offset in _list_dir(img, dir_lba, dir_size):
		if is_dir:
			continue
		rel = f"{prefix}/{name}" if prefix else name
		out.append(IsoFile(path=rel, lba=lba, size=size, dir_lba=dir_lba, rec_offset=rec_offset))
	return out


def byte_ranges_overlap(
	records_a: list[dict],
	records_b: list[dict],
) -> list[tuple[int, int, int, int]]:
	"""Return overlapping [start,end) pairs between two ic-layer record lists."""
	def spans(records: list[dict]) -> list[tuple[int, int]]:
		out: list[tuple[int, int]] = []
		for rec in records:
			off = int(rec["offset"])
			n = len(bytes.fromhex(rec["hex"]))
			out.append((off, off + n))
		return sorted(out)

	a = spans(records_a)
	b = spans(records_b)
	hits: list[tuple[int, int, int, int]] = []
	i = j = 0
	while i < len(a) and j < len(b):
		a0, a1 = a[i]
		b0, b1 = b[j]
		lo = max(a0, b0)
		hi = min(a1, b1)
		if lo < hi:
			hits.append((a0, a1, b0, b1))
		if a1 <= b1:
			i += 1
		else:
			j += 1
	return hits
