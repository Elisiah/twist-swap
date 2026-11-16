# edits to build script to test shifting CT1 by 4MB

import os

# outputs
BASE_ROM_PATH = "build/chameleontwist.jp.base.z64" 
BASE_SYMBOLS_PATH = "build/base/undefined_syms.txt"

# the switcher
SWITCHER_C_SOURCE = "swap/c/swap.c"                    
SWITCHER_C_OBJECT = "build/swap/swap.c.o"
SWITCHER_C_ENTRY_SOURCE = "swap/c/swap_entry.s"        
SWITCHER_C_ENTRY_OBJECT = "build/swap/swap_entry.s.o"

# the asset pool is what takes up the space, but roughly 300Kb is never used
# so I'll steal from that to make space for the game swapping.c code
POOL_SOURCE = "asm/data/assets0Bss.bss.s"
SHRUNK_POOL_SOURCE = "build/swap/assets0Bss.bss.s"
SHRUNK_POOL_OBJECT = "build/swap/assets0Bss.bss.s.o"
VANILLA_POOL_SIZE = 0x154020
SWAP_RESERVE = 0x1000

# vanilla CT1 addresses that have to move
VANILLA_ENTRY = 0x80025C00    # .entry
VANILLA_ZBUFFER = 0x80000400  # gfxZBuffer


def add_args(parser):
    parser.add_argument(
        "--base",
        default=None,
    )
    parser.add_argument(
        "--swap",
        action="store_true",
    )


def finish_args(args, add_define):
    if args.swap and args.base is None:
        args.base = "0x400000"          # the merge always puts CT1 4 MB up
    if args.base is not None:
        args.shift = True


def base_offset(args):
    return int(args.base, 0) if (args is not None and args.base is not None) else 0


def want_swap(args):
    return args is not None and args.swap


def patch_ld(ld, ld_path, base_off, swap):
    if base_off:
        for segment, vanilla_address in ((".entry", VANILLA_ENTRY), (".main", VANILLA_ENTRY + 0x50)):
            old_line = f"    {segment} 0x{vanilla_address:08X} : AT("
            ld = ld.replace(old_line, f"    {segment} 0x{vanilla_address + base_off:08X} : AT(", 1)

    if swap:
        main_code_start = "        main_TEXT_START = .;\n"
        pool_line = "        build/asm/data/assets0Bss.bss.s.o(.bss);\n"

        placed = (f"        {SWITCHER_C_ENTRY_OBJECT}(.text .data .bss);\n"
                  f"        {SWITCHER_C_OBJECT}(.text .data .rodata .bss COMMON);\n")
        ld = ld.replace(main_code_start, main_code_start + placed, 1)

        ld = ld.replace(pool_line, f"        {SHRUNK_POOL_OBJECT}(.bss);\n", 1)

        # fail the build if CT1 goes past its 4MB
        ct1_ram_end = 0x80400000 + base_off
        ld = ld.replace("\n    /DISCARD/ :",
                        f"\n    ASSERT(assets0_BSS_END <= 0x{ct1_ram_end:08X}, \"CT1 too big\")\n    /DISCARD/ :", 1)
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


def add_objects(build, o_files, swap):
    if not swap:
        return
    from pathlib import Path

    # ensure space for frambuff
    pool_text = open(POOL_SOURCE, encoding="utf-8").read()
    old_space = f".space 0x{VANILLA_POOL_SIZE:X}"
    pool_text = pool_text.replace(old_space, f".space 0x{VANILLA_POOL_SIZE - SWAP_RESERVE:X}")
    pool_text = pool_text.replace("dlabel gFrameBuffers", ".balign 64\ndlabel gFrameBuffers")
    os.makedirs(os.path.dirname(SHRUNK_POOL_SOURCE), exist_ok=True)
    open(SHRUNK_POOL_SOURCE, "w", encoding="utf-8").write(pool_text)
    build(Path(SHRUNK_POOL_OBJECT), [Path(SHRUNK_POOL_SOURCE)], "s_file")
    o_files.append(SHRUNK_POOL_OBJECT)

    build(Path(SWITCHER_C_ENTRY_OBJECT), [Path(SWITCHER_C_ENTRY_SOURCE)], "s_file")
    build(Path(SWITCHER_C_OBJECT), [Path(SWITCHER_C_SOURCE)], "O2_cc")
    o_files += [SWITCHER_C_ENTRY_OBJECT, SWITCHER_C_OBJECT]


def add_z64(build, pre_elf_path, base_off):
    from pathlib import Path
    build(Path(BASE_ROM_PATH), [Path(pre_elf_path)], "make_z64_base")
