#include "swap.h"

// Set Ct2 addresses since Ct1 is shifting
#define CT2_EXCEPTION_HANDLER 0x800D80A0 // __osException

// ct1's exception handler
extern void __osException(void);

// shared with swap_entry.s
s32 gSwapActiveGame = GAME_CT1; // current game
u32 gSwapGameHandlers[2] = { (u32)__osException, CT2_EXCEPTION_HANDLER };
