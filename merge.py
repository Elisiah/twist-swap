# add ct2 rom as arg for editing addresses pre-swaps

import re
import struct
import subprocess
import sys

CT1_ROM_PATH = "build/chameleontwist.jp.base.z64"
CT1_MAP_PATH = "build/chameleontwist.jp.map"
OUTPUT_PATH = "build/ctswap.z64"
CRC_TOOL = "tools/n64crc/n64crc.exe"           
CT2_ROM_OFFSET = 0x01000000                    # Move ct2 to 16MB

CT2_CODE_RAM_START = 0x80025C00
CODE_ROM_START = 0x1000
REGISTER_K0 = 26

def ct2_rom_offset(ram_address):
    return ram_address - CT2_CODE_RAM_START + CODE_ROM_START


def patch_word(rom, offset, new):
    rom[offset:offset + 4] = struct.pack(">I", new)


# lui/addiu pair for an address
def encode_load_address(register, address):
    high_half = ((address + 0x8000) >> 16) & 0xFFFF
    low_half = address & 0xFFFF
    lui = 0x3C000000 | (register << 16) | high_half
    addiu = 0x24000000 | (register << 21) | (register << 16) | low_half
    return lui, addiu


def read_map_symbols(path):
    symbols = {}
    for line in open(path, encoding="utf-8"):
        match = re.match(r"\s+0x([0-9a-f]+)\s+([A-Za-z_]\w*)(?: = .*)?\s*$", line)
        if match:
            symbols.setdefault(match.group(2), int(match.group(1), 16))
    return symbols


def main():
    ct1 = bytearray(open(CT1_ROM_PATH, "rb").read())
    ct2 = bytearray(open(sys.argv[1], "rb").read())

    symbols = read_map_symbols(CT1_MAP_PATH)
    stub_lui, stub_addiu = encode_load_address(REGISTER_K0, symbols["Swap_Exception"])

    # lui/addiu $k0, jr $k0 - swap jump
    stub_offset = symbols["__osExceptionPreamble"] - symbols["main_VRAM"] + symbols["main_ROM_START"]
    patch_word(ct1, stub_offset, stub_lui)
    patch_word(ct1, stub_offset + 4, stub_addiu)

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
