---
title: Building a CHIP-8 Emulator
date: 2026-06-15
tags: [Emulation, C++]
summary: CHIP-8 is an interpreted language from the mid-1970s and the classic first emulator project: a small spec, well documented, with real games at the end. Here's how I built mine in C++23 with SDL2, OpenGL and ImGui.
reading_time: 8 min read
---
CHIP-8 is an interpreted programming language from the mid-1970s, originally designed to make game development easier on early microcomputers like the COSMAC VIP. It never ran directly on hardware; it was always a virtual machine. That makes it the classic first emulator project: the spec is small, the behaviour is well-documented, and you get something that runs real games at the end of it.

I built mine in C++23 with SDL2, OpenGL, and ImGui for the frontend. This is a walkthrough of the key decisions I made along the way.

## Project structure

The project splits cleanly into two concerns: emulation and display. `cpu.hpp` and `cpu.cpp` contain the CHIP-8 virtual machine: memory, registers, the fetch-execute loop, and every opcode. `display.cpp` handles everything visual: the SDL2/OpenGL window, uploading the display buffer as a GPU texture, and an ImGui-based debug UI.

The core state lives in a `Chip8` struct:

- 4096 bytes of memory
- 16 general-purpose 8-bit registers (V0–VF)
- A 16-bit index register and program counter
- A 16-entry stack with a stack pointer
- Delay and sound timer registers
- A 32×64 boolean array for the display
- 16-key keypad state

## Organising opcodes with enums

Rather than a single flat switch over all 35 opcodes, I used a set of strongly-typed enum classes to represent each instruction family. `OpcodeFamily` covers the top-nibble dispatch (0x0000–0xF000). Nested enums (`SysOpcode`, `AluOpcode`, `MiscOpcode`, `KeyOpcode`) handle the sub-categories within each family.

This makes the decode path read more like the spec and less like a pile of magic numbers. The primary switch routes on the high nibble; nested switches inside each case handle the rest:

```cpp
// extract fields from the 16-bit opcode
uint8_t  x   = (opcode & 0x0F00) >> 8;
uint8_t  y   = (opcode & 0x00F0) >> 4;
uint8_t  nn  =  opcode & 0x00FF;
uint16_t nnn =  opcode & 0x0FFF;
uint8_t  n   =  opcode & 0x000F;

switch (static_cast<OpcodeFamily>(opcode & 0xF000)) {
    case OpcodeFamily::SYS:
        switch (static_cast<SysOpcode>(opcode & 0x00FF)) {
            case SysOpcode::CLS: /* clear screen */ break;
            case SysOpcode::RET: /* return */       break;
        }
        break;
    case OpcodeFamily::ALU:
        switch (static_cast<AluOpcode>(opcode & 0x000F)) { /* ... */ }
        break;
    // ...
}
```

## The fetch-execute cycle

The `emulateCycle()` function runs one CPU tick: fetch the two-byte opcode from memory at the program counter, increment the PC by 2, decode, and execute. Most instructions advance by 2; skip instructions (which conditionally skip the next instruction) advance by 4.

The timers are separate from the CPU speed. In the rendering loop, I decrement delay and sound timers every 16ms, roughly 60 Hz, independently of how many CPU cycles have run that frame.

## Carry flags and VF

VF is the register the spec uses as a flag: carry on addition, borrow on subtraction, collision on drawing. The tricky part is that it's also a general-purpose register, so you have to write the flag after the operation completes, not before, otherwise you corrupt an operand if VF is also VX or VY.

For addition I widen to `uint16_t` to detect the carry without overflow:

```cpp
uint16_t sum = V[x] + V[y];
V[0xF] = sum > 0xFF ? 1 : 0;
V[x] = static_cast<uint8_t>(sum);
```

## Key wait (FX0A)

The key-wait instruction blocks until a key is pressed. I implemented this by returning early from `emulateCycle()` without incrementing the program counter if no key is currently down. The CPU just replays the same instruction on every tick until a keypress comes in. Simple and correct.

## Rendering with SDL2, OpenGL, and ImGui

The display buffer (the 32×64 boolean array) is uploaded to the GPU as an RGBA texture each frame via `glTexImage2D()`. Each pixel maps to a 32-bit colour value: white for set, black for unset. ImGui then draws it at 10× scale using `ImGui::Image()`, giving a crisp 640×320 pixel display.

SDL2 handles windowing, input, and the OpenGL context. VSync is enabled with `SDL_GL_SetSwapInterval(1)`, so the render loop naturally runs at the display refresh rate rather than spinning flat out.

## Debug UI

One of the more useful things about using ImGui is how easy it is to bolt on a live debug panel. Mine has collapsible sections for:

- All 16 registers (V0–VF), PC, I, SP, and the current opcode
- Delay and sound timer values
- The full stack with the current stack pointer highlighted
- Keypad state with colour-coded indicators for pressed keys

This made debugging opcode implementations considerably less painful. Being able to watch the registers update in real time while a ROM runs is much faster than adding print statements.

## Profiling with Valgrind

Once the emulator was running I profiled it with Valgrind's Callgrind tool and visualised the output in KCachegrind. The project is compiled with `-O2` and C++23, with strict warnings enabled (`-Wall -Wextra -Wpedantic -Wconversion -Wsign-conversion -Werror`). The profiling pass was useful for confirming the hot path was where I expected (the fetch-execute loop and texture upload) rather than hiding somewhere in ImGui's draw calls.

## Testing with real ROMs

The best test is just running ROMs. Pong was my first target: it exercises key input, collision detection, and the timer-based paddle speed all at once. The Particle Demo is a good stress test for the drawing path since it hammers XOR rendering continuously.

The source is up on [GitHub](https://github.com/Yates1011/chip-8-emulator) if you want to take a look. CHIP-8 is a genuinely good first emulator: small enough to finish in a weekend, but the problems you hit are exactly the ones you'll face in anything more complex.
