#include "swap.h"
#include <PR/R4300.h> // register header
#include <PR/rcp.h>   // IO write and read

// Set Ct2 addresses since Ct1 is shifting
#define CT2_EXCEPTION_HANDLER 0x800D80A0 // __osException
#define CT2_ENTRY_ADDRESS     0x80025C00 // code entry
#define CT2_ROM_OFFSET        0x01000000 // move ct2 later than ct1 in rom so ct1 boots
#define BOOT_COPY_SIZE        0x100000   // IPL3 to copy the game's first 1 MB of code

// ct1's exception handler
extern void __osException(void);

// shared with swap_entry.s
s32 gSwapActiveGame = GAME_CT1; // current game
u32 gSwapGameHandlers[2] = { (u32)__osException, CT2_EXCEPTION_HANDLER };

s32 gSwapRefreshesUntilBoot = 1200; // 20s

void Swap_ColdBootCT2(void) {
    gSwapActiveGame = GAME_CT2;

    // ct1 - pirawdma.c
    // DMA CT2's first 1 MB of code into its RAM
    IO_WRITE(PI_DRAM_ADDR_REG, K0_TO_PHYS(CT2_ENTRY_ADDRESS));                
    IO_WRITE(PI_CART_ADDR_REG, PI_DOM1_ADDR2 + CT2_ROM_OFFSET + 0x1000);      // code starts 0x1000
    IO_WRITE(PI_WR_LEN_REG, BOOT_COPY_SIZE - 1);
    while (IO_READ(PI_STATUS_REG) & (PI_STATUS_DMA_BUSY | PI_STATUS_IO_BUSY)) {
        // busy wait
    }

    Swap_EnterCold(CT2_ENTRY_ADDRESS);
}
