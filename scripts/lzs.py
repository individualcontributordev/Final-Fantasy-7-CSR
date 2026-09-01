"""Encode and decode FF7 field LZS streams.

The raw codec follows the Okumura-style 4096-byte LZSS ring used by ff7tk.
FIELD/*.DAT wraps that stream with a little-endian compressed-payload length;
the ``*_with_header`` functions consume and produce that envelope. Input and
output are bytes only, with no file or disc mutation. Compression is
deterministic for this implementation but LZS encodings are not unique, so
callers verify decompressed semantics rather than compressed byte identity.
``find_literal_body_offset`` is intentionally fail-closed when a requested
decompressed byte came from a shared back-reference.
"""

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


def find_literal_body_offset(body: bytes, dec_offset: int) -> int:
	"""Find the offset within a raw LZS payload (no header) of the literal
	byte that produced decompressed output byte `dec_offset`.

	Raises ValueError if that output byte was produced by a back-reference
	match instead of a literal (i.e. it cannot be patched in place without
	possibly also touching other decompressed bytes that share the same
	match run).
	"""
	i = 0
	n = len(body)
	first_byte = 0
	out_pos = 0
	while i < n:
		first_byte >>= 1
		if (first_byte & 256) == 0:
			if i >= n:
				break
			first_byte = body[i] | 0xFF00
			i += 1
		if i >= n:
			break
		if first_byte & 1:
			if out_pos == dec_offset:
				return i
			i += 1
			out_pos += 1
		else:
			if i + 1 >= n:
				break
			b1 = body[i]
			b2 = body[i + 1]
			i += 2
			offset = b1 | ((b2 & 0xF0) << 4)
			end = (b2 & 0x0F) + 2 + offset
			run_len = end - offset + 1
			if out_pos <= dec_offset < out_pos + run_len:
				raise ValueError(
					f"decompressed offset {dec_offset} is inside a back-reference "
					f"match run, not a literal byte -- cannot patch in place"
				)
			out_pos += run_len
	raise ValueError(f"decompressed offset {dec_offset} not reached (stream length {out_pos})")



def compress_all(data: bytes) -> bytes:
	"""Compress FF7 LZS using the same binary-tree LZSS algorithm as ff7tk.

	Ring buffer/tree layout matches LZS.cpp exactly:
	  N = 4096 (ring buffer size), F = 18 (max match length), THRESHOLD = 2.
	  NIL = N is used as the "not in tree" sentinel for lson/rson/dad.
	  text_buf is sized N + F + (N - F - 1) = 4113 so that text_buf[r+i] for
	  r in [0, N) and i in [0, F) never goes out of range, and so that the
	  s < F - 1 buffer-wraparound mirror (text_buf[s + N] = c) fits too.
	"""
	N = 4096
	F = 18
	THRESHOLD = 2
	NIL = N

	text_buf = bytearray(N + F + N)  # generous; only ~4113 bytes are ever touched
	lson = [NIL] * (N + 1)
	rson = [NIL] * (N + 1 + 256)
	dad = [NIL] * (N + 1)

	state = {"match_length": 0, "match_position": 0}

	def insert_node(r: int) -> None:
		cmp = 1
		key = r
		p = N + 1 + text_buf[key]
		rson[r] = NIL
		lson[r] = NIL
		state["match_length"] = 0
		while True:
			if cmp >= 0:
				if rson[p] != NIL:
					p = rson[p]
				else:
					rson[p] = r
					dad[r] = p
					return
			else:
				if lson[p] != NIL:
					p = lson[p]
				else:
					lson[p] = r
					dad[r] = p
					return
			i = 1
			while i < F:
				cmp = text_buf[key + i] - text_buf[p + i]
				if cmp != 0:
					break
				i += 1
			if i > state["match_length"]:
				state["match_position"] = p
				state["match_length"] = i
				if i >= F:
					break
		dad[r] = dad[p]
		lson[r] = lson[p]
		rson[r] = rson[p]
		dad[lson[p]] = r
		dad[rson[p]] = r
		if rson[dad[p]] == p:
			rson[dad[p]] = r
		else:
			lson[dad[p]] = r
		dad[p] = NIL  # remove p

	def delete_node(p: int) -> None:
		if dad[p] == NIL:
			return
		if rson[p] == NIL:
			q = lson[p]
		elif lson[p] == NIL:
			q = rson[p]
		else:
			q = lson[p]
			if rson[q] != NIL:
				while rson[q] != NIL:
					q = rson[q]
				rson[dad[q]] = lson[q]
				dad[lson[q]] = dad[q]
				lson[q] = lson[p]
				dad[lson[p]] = q
			rson[q] = rson[p]
			dad[rson[p]] = q
		dad[q] = dad[p]
		if rson[dad[p]] == p:
			rson[dad[p]] = q
		else:
			lson[dad[p]] = q
		dad[p] = NIL

	n = len(data)
	if n == 0:
		return b""

	for i in range(N + 1, N + 1 + 256):
		rson[i] = NIL
	for i in range(N):
		dad[i] = NIL

	code_buf = bytearray(17)
	code_buf[0] = 0
	code_buf_ptr = 1
	mask = 1

	s = 0
	r = 4078
	for i in range(r):
		text_buf[i] = 0

	pos = 0
	length = 0
	while length < F and pos < n:
		text_buf[r + length] = data[pos]
		pos += 1
		length += 1
	if length == 0:
		return b""

	for i in range(1, F + 1):
		insert_node(r - i)
	insert_node(r)

	out = bytearray()
	while True:
		match_length = state["match_length"]
		match_position = state["match_position"]
		if match_length > length:
			match_length = length
		if match_length <= THRESHOLD:
			match_length = 1
			code_buf[0] |= mask
			code_buf[code_buf_ptr] = text_buf[r]
			code_buf_ptr += 1
		else:
			code_buf[code_buf_ptr] = match_position & 0xFF
			code_buf_ptr += 1
			code_buf[code_buf_ptr] = ((match_position >> 4) & 0xF0) | ((match_length - (THRESHOLD + 1)) & 0x0F)
			code_buf_ptr += 1

		mask = (mask << 1) & 0xFF
		if mask == 0:
			out.extend(code_buf[:code_buf_ptr])
			code_buf[0] = 0
			code_buf_ptr = 1
			mask = 1

		last_match_length = match_length
		i = 0
		while i < last_match_length and pos < n:
			c = data[pos]
			pos += 1
			delete_node(s)
			text_buf[s] = c
			if s < F - 1:
				text_buf[s + N] = c
			s = (s + 1) & (N - 1)
			r = (r + 1) & (N - 1)
			insert_node(r)
			i += 1
		while i < last_match_length:
			i += 1
			delete_node(s)
			s = (s + 1) & (N - 1)
			r = (r + 1) & (N - 1)
			length -= 1
			if length:
				insert_node(r)

		if length <= 0:
			break

	if code_buf_ptr > 1:
		out.extend(code_buf[:code_buf_ptr])

	return bytes(out)


def compress_all_with_header(data: bytes) -> bytes:
	"""u32le compressed size + LZS payload (FIELD/*.DAT style)."""
	body = compress_all(data)
	return struct.pack("<I", len(body)) + body
