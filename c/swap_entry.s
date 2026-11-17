# use k0,k1 free addresses to not overwrite the stored hardware registers (so write this in asm not c)

.include "macro.inc"

.set noat       # $at will hold game values
.set noreorder

.section .text, "ax"

# every exception lands here
glabel Swap_Exception
    # ct1 - exceptasm.s
    mfc0    $k0, $13                        # what caused the exception
    andi    $k0, $k0, 0x7C                  # will contain 0 on interr
    bnez    $k0, Swap_Chain                 # branch back to game to handle if not interr
    nop

    # is it a screen refresh?
    lui     $k0, 0xA430                     
    lw      $k0, 0x8($k0)                   
    andi    $k0, $k0, 0x08                  
    beqz    $k0, Swap_Chain                 # return all non screen updates to game
    nop

    # return handling to game if not ready to swap
    la      $k1, gSwapRefreshesUntilBoot
    lw      $k0, 0($k1)
    addiu   $k0, $k0, -1
    sw      $k0, 0($k1)
    bnez    $k0, Swap_Chain               
    nop

    # else: swap to ct2
    la      $sp, sSwapStack + 0x400         
    j       Swap_ColdBootCT2               
    nop

# jump to the running the right game's handler
glabel Swap_Chain
    lw      $k0, gSwapActiveGame        # 0 = CT1, 1 = CT2
    sll     $k0, $k0, 2                 # each table entry is a 4-byte address
    la      $k1, gSwapGameHandlers
    addu    $k0, $k0, $k1               # entry addr
    lw      $k0, 0x0($k0)               # handler address
    jr      $k0                         # go to real exception handler
    nop

# cold load game from passed entry
glabel Swap_EnterCold
    li      $t0, 0x34000002                  # copy the cpu settings ipl3 uses
    mtc0    $t0, $12                         # write cpu settings
    mtc0    $a0, $14                         # address for exception return
    nop                                      # give writes time to land
    nop
    eret                                     # jump to game and re-enable interrupt handling

# 1KB stack for the C code
.section .bss
.balign 16
glabel sSwapStack
    .space 0x400
