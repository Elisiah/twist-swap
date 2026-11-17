#ifndef SWAP_H
#define SWAP_H

#include <ultra64.h>

enum { GAME_CT1, GAME_CT2 };

// in swap_entry.s
extern void Swap_EnterCold(u32 entryAddress);             // boot a game at entryAddress

#endif
