from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from libs.layer import apply_layer, build_layer
from repair_mode2_edc import SECTOR, generate_mode2_form1_edc_ecc, repair


def mode2_sector(*, form2: bool) -> bytearray:
    sector = bytearray(SECTOR)
    sector[0:12] = b"\x00" + (b"\xff" * 10) + b"\x00"
    sector[15] = 2
    if form2:
        sector[18] = 0x20
        sector[22] = 0x20
    return sector


class LayerTests(unittest.TestCase):
    def test_round_trip_preserves_grown_image_length(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = root / "original.bin"
            modified = root / "modified.bin"
            original.write_bytes(bytes(SECTOR))

            expected = bytearray(SECTOR * 2)
            expected[100:104] = b"TEST"
            modified.write_bytes(expected)

            layer = build_layer(
                original,
                modified,
                layer_id="test",
                description="test",
            )
            actual = bytearray(original.read_bytes())
            apply_layer(actual, layer)

            self.assertEqual(actual, expected)


class RepairTests(unittest.TestCase):
    def test_changed_form2_payload_is_untouched(self) -> None:
        pristine_sector = mode2_sector(form2=True)
        image_sector = bytearray(pristine_sector)
        image_sector[2200:2204] = b"XA!!"

        repaired = self.repair(bytes(pristine_sector), bytes(image_sector))

        self.assertEqual(repaired, image_sector)

    def test_appended_form2_sector_is_untouched(self) -> None:
        pristine_sector = mode2_sector(form2=False)
        generate_mode2_form1_edc_ecc(pristine_sector)
        form2 = mode2_sector(form2=True)
        form2[100:104] = b"XA!!"

        repaired = self.repair(bytes(pristine_sector), bytes(pristine_sector + form2))

        self.assertEqual(repaired[SECTOR:], form2)

    def test_appended_form1_sector_gets_fresh_footer(self) -> None:
        pristine_sector = mode2_sector(form2=False)
        generate_mode2_form1_edc_ecc(pristine_sector)
        appended = mode2_sector(form2=False)
        appended[24:28] = b"DATA"

        expected = bytearray(appended)
        generate_mode2_form1_edc_ecc(expected)
        repaired = self.repair(bytes(pristine_sector), bytes(pristine_sector + appended))

        self.assertEqual(repaired[SECTOR:], expected)

    def repair(self, pristine_data: bytes, image_data: bytes) -> bytes:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pristine = root / "pristine.bin"
            image = root / "image.bin"
            output = root / "output.bin"
            pristine.write_bytes(pristine_data)
            image.write_bytes(image_data)
            repair(pristine, image, output)
            return output.read_bytes()


if __name__ == "__main__":
    unittest.main()
