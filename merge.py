# add ct2 rom as arg for editing addresses pre-swaps

import struct
import subprocess
import sys

CT1_ROM_PATH = "build/chameleontwist.jp.base.z64"
OUTPUT_PATH = "build/ctswap.z64"
CRC_TOOL = "tools/n64crc/n64crc.exe"           
CT2_ROM_OFFSET = 0x01000000                    # Move ct2 to 16MB

CT2_CODE_RAM_START = 0x80025C00
CODE_ROM_START = 0x1000

def ct2_rom_offset(ram_address):
    return ram_address - CT2_CODE_RAM_START + CODE_ROM_START


def patch_word(rom, offset, new):
    rom[offset:offset + 4] = struct.pack(">I", new)


def main():
    ct1 = bytearray(open(CT1_ROM_PATH, "rb").read())
    ct2 = bytearray(open(sys.argv[1], "rb").read())

    # cheaper to put it at 16 MB as a hack so the game's OR reads work as ADD offsets
    patch_word(ct2, ct2_rom_offset(0x800DC630), 0x3C08B100)
    patch_word(ct2, ct2_rom_offset(0x800DE94C), 0x3C09B100)
    # osCartRomInit
    patch_word(ct2, ct2_rom_offset(0x800E4330), 0x3C0FB100)

    merged = ct1 + bytes(CT2_ROM_OFFSET - len(ct1)) + ct2
    open(OUTPUT_PATH, "wb").write(merged)
    subprocess.run([CRC_TOOL, OUTPUT_PATH])


if __name__ == "__main__":
    main()
