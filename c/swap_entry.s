# use k0,k1 free addresses to not overwrite the stored hardware registers (so write this in asm not c)

.include "macro.inc"

.set noat       # $at will hold game values
.set noreorder

.section .text, "ax"

# every exception lands here, TODO: write this
glabel Swap_Exception

# jump to the running the right game's handler
glabel Swap_Chain
    lw      $k0, gSwapActiveGame        # 0 = CT1, 1 = CT2
    sll     $k0, $k0, 2                 # each table entry is a 4-byte address
    la      $k1, gSwapGameHandlers
    addu    $k0, $k0, $k1               # entry addr
    lw      $k0, 0x0($k0)               # handler address
    jr      $k0                         # go to real exception handler
    nop
