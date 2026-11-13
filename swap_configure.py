# edits to build script to test shifting CT1 by 4MB

import os

# outputs
BASE_ROM_PATH = "build/chameleontwist.jp.base.z64" 
BASE_SYMBOLS_PATH = "build/base/undefined_syms.txt"

# vanilla CT1 addresses that have to move
VANILLA_ENTRY = 0x80025C00    # .entry
VANILLA_ZBUFFER = 0x80000400  # gfxZBuffer


def add_args(parser):
    parser.add_argument(
        "--base",
        default=None,
    )


def finish_args(args, add_define):
    if args.base is not None:
        args.shift = True


def base_offset(args):
    return int(args.base, 0) if (args is not None and args.base is not None) else 0


def patch_ld(ld, ld_path, base_off):
    if base_off:
        # move the two set addresses so the rest follow
        for segment, vanilla_address in ((".entry", VANILLA_ENTRY), (".main", VANILLA_ENTRY + 0x50)):
            old_line = f"    {segment} 0x{vanilla_address:08X} : AT("
            ld = ld.replace(old_line, f"    {segment} 0x{vanilla_address + base_off:08X} : AT(", 1)
    return ld


def patch_ldflags(ldflags, base_off):
    if not base_off:
        return ldflags
    symbols_text = open("undefined_syms.txt", encoding="utf-8").read()
    old_line = f"gfxZBuffer = 0x{VANILLA_ZBUFFER:08X};"
    symbols_text = symbols_text.replace(old_line, f"gfxZBuffer = 0x{VANILLA_ZBUFFER + base_off:08X}; /* --base */")
    os.makedirs(os.path.dirname(BASE_SYMBOLS_PATH), exist_ok=True)
    open(BASE_SYMBOLS_PATH, "w", encoding="utf-8").write(symbols_text)
    return ldflags.replace("-T undefined_syms.txt", f"-T {BASE_SYMBOLS_PATH}")


def add_rules(ninja, mips, tools_dir):
    ninja.rule(
        "make_z64_base",
        command=f"({mips}-objcopy -O binary $in $out) && python3 swap/set_entry.py && ({tools_dir}/n64crc/n64crc.exe $out)",
        description="Making rebased z64",
    )


def add_z64(build, pre_elf_path, base_off):
    from pathlib import Path
    build(Path(BASE_ROM_PATH), [Path(pre_elf_path)], "make_z64_base")
