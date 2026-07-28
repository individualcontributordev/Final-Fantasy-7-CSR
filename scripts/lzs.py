"""FF7 LZS decompress (Okumura / ff7tk LZS::decompressAllWithHeader)."""

from __future__ import annotations

import struct


def decompress_all(data: bytes) -> bytes:
	"""Decompress raw LZS payload (no 4-byte size header)."""
	out = bytearray()
	text_buf = bytearray(4096)
	cur = 4078
	i = 0
	n = len(data)
	first_byte = 0

	while i < n:
		first_byte >>= 1
		if (first_byte & 256) == 0:
			if i >= n:
				break
			first_byte = data[i] | 0xFF00
			i += 1
		if i >= n:
			break
		if first_byte & 1:
			b = data[i]
			i += 1
			text_buf[cur] = b
			out.append(b)
			cur = (cur + 1) & 4095
		else:
			if i + 1 >= n:
				break
			b1 = data[i]
			b2 = data[i + 1]
			i += 2
			offset = b1 | ((b2 & 0xF0) << 4)
			end = (b2 & 0x0F) + 2 + offset
			for pos in range(offset, end + 1):
				b = text_buf[pos & 4095]
				text_buf[cur] = b
				out.append(b)
				cur = (cur + 1) & 4095

	return bytes(out)


def decompress_all_with_header(data: bytes) -> bytes:
	"""PSX FIELD/*.DAT style: u32le compressed size, then LZS bytes."""
	if len(data) < 4:
		raise ValueError("LZS header truncated")
	(lzs_size,) = struct.unpack_from("<I", data, 0)
	if lzs_size <= 0 or 4 + lzs_size > len(data):
		raise ValueError(f"bad LZS size {lzs_size} for file of {len(data)}")
	return decompress_all(data[4 : 4 + lzs_size])
