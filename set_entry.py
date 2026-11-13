# Write the moved CT1's entry point into its ROM header (shifted 4MB higher)
with open("build/chameleontwist.jp.base.z64", "r+b") as rom:
    rom.seek(8)
    rom.write((0x80425C00).to_bytes(4, "big"))
