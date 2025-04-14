# Wake Language Reference

This document details the syntax and instructions available in the Wake language, which compiles to MicroASM.

## Overview

Wake provides a C-like syntax layer over MicroASM, aiming for better readability while retaining low-level control. It translates Wake function calls directly into MicroASM instructions.

## Basic Syntax

### Comments

Single-line comments start with `//`.

```wake
// This is a comment
mov(RAX, 1); // This is an inline comment
```

### Function Definition

Functions are defined using the `void` keyword, followed by the function name, parentheses `()`, and a body enclosed in curly braces `{}`.

```wake
void myFunction() {
    // Instructions go here
    ret(); // Return from function
}
```

### Includes

Wake supports two types of includes:

1.  **Wake Includes (`#include`)**: Processes the specified `.wake` file recursively, incorporating its tokens into the current compilation unit. The compiler searches for the file relative to the current file and in configured search paths.

    ```wake
    #include "utils.wake"
    ```

2.  **MicroASM Includes (`#M_include`)**: Passes the include directive directly to the MicroASM compiler without processing the included file's content in Wake. This is useful for including MicroASM header files or libraries.

    ```wake
    #M_include "stdio.print" // Will become #include "stdio.print" in the .masm output
    ```

## Instruction Reference

Wake instructions map directly to MicroASM instructions. They are called like functions with arguments enclosed in parentheses.

### Data Movement

*   **`mov(dest, src)`**
    *   MicroASM: `MOV dest src`
    *   Copies data from `src` to `dest`. `dest` and `src` can be registers (e.g., `RAX`) or immediate values.
    *   Example: `mov(RAX, 10); mov(RBX, RAX);`

### Arithmetic Operations

*   **`add(dest, src)`**
    *   MicroASM: `ADD dest src`
    *   Adds `src` to `dest`.
    *   Example: `add(R1, 5);`
*   **`sub(dest, src)`**
    *   MicroASM: `SUB dest src`
    *   Subtracts `src` from `dest`.
    *   Example: `sub(R1, R2);`
*   **`mul(dest, src)`**
    *   MicroASM: `MUL dest src`
    *   Multiplies `dest` by `src`.
    *   Example: `mul(R1, 2);`
*   **`div(dest, src)`**
    *   MicroASM: `DIV dest src`
    *   Divides `dest` by `src`.
    *   Example: `div(R1, R3);`
*   **`inc(dest)`**
    *   MicroASM: `INC dest`
    *   Increments `dest` by 1.
    *   Example: `inc(RAX);`

### Logic and Bitwise Operations

*   **`and(dest, src)`**
    *   MicroASM: `AND dest src`
    *   Performs bitwise AND.
    *   Example: `and(R1, R2);`
*   **`or(dest, src)`**
    *   MicroASM: `OR dest src`
    *   Performs bitwise OR.
    *   Example: `or(R1, R2);`
*   **`xor(dest, src)`**
    *   MicroASM: `XOR dest src`
    *   Performs bitwise XOR.
    *   Example: `xor(R1, R1); // Zeroes R1`
*   **`not(dest)`**
    *   MicroASM: `NOT dest`
    *   Performs bitwise NOT.
    *   Example: `not(R1);`
*   **`shl(dest, count)`**
    *   MicroASM: `SHL dest count`
    *   Shifts `dest` left by `count` bits.
    *   Example: `shl(RAX, 2);`
*   **`shr(dest, count)`**
    *   MicroASM: `SHR dest count`
    *   Shifts `dest` right by `count` bits.
    *   Example: `shr(RAX, 1);`

### Control Flow

*   **`jmp(label)`**
    *   MicroASM: `JMP #label`
    *   Unconditionally jumps to the specified label (string).
    *   Example: `jmp("loopStart");`
*   **`cmp(a, b)`**
    *   MicroASM: `CMP a b`
    *   Compares `a` and `b`.
    *   Example: `cmp(RAX, 10);`
*   **`je(trueLabel, falseLabel)`**
    *   MicroASM: `JE #trueLabel #falseLabel`
    *   Jumps to `trueLabel` if equal, otherwise jumps to `falseLabel`.
    *   Example: `je("equalCase", "notEqualCase");`
*   **`jne(trueLabel, falseLabel)`**
    *   MicroASM: `JNE #trueLabel #falseLabel`
    *   Jumps to `trueLabel` if not equal, otherwise jumps to `falseLabel`.
    *   Example: `jne("notEqual", "areEqual");`
*   **`jl(trueLabel, falseLabel)`**
    *   MicroASM: `JL #trueLabel #falseLabel`
    *   Jumps to `trueLabel` if less than, otherwise jumps to `falseLabel`.
    *   Example: `jl("lessThan", "greaterOrEqual");`
*   **`jg(trueLabel, falseLabel)`**
    *   MicroASM: `JG #trueLabel #falseLabel`
    *   Jumps to `trueLabel` if greater than, otherwise jumps to `falseLabel`.
    *   Example: `jg("greaterThan", "lessOrEqual");`
*   **`call(label)`**
    *   MicroASM: `CALL #label`
    *   Calls the function/label specified by the string.
    *   Example: `call("myFunction");`
*   **`ret()`**
    *   MicroASM: `RET`
    *   Returns from the current function.
    *   Example: `ret();`

### Stack Operations

*   **`push(value)`**
    *   MicroASM: `PUSH value`
    *   Pushes a register or immediate value onto the stack.
    *   Example: `push(RAX); push(10);`
*   **`pop(dest)`**
    *   MicroASM: `POP dest`
    *   Pops a value from the stack into the destination register.
    *   Example: `pop(RBX);`

### I/O Operations

*   **`out(port, value)`**
    *   MicroASM: `OUT port value`
    *   Outputs a register value or a memory address (like `$100`) to the specified port (1 for stdout, 2 for stderr).
    *   Example: `out(1, RAX); out(1, $100);`
*   **`cout(port, value)`**
    *   MicroASM: `COUT port value`
    *   Outputs the ASCII character corresponding to the value in a register or memory address.
    *   Example: `cout(1, 65); // Outputs 'A'`

### Memory Definition

*   **`db(address, "string")`**
    *   MicroASM: `DB $address "string"`
    *   Defines a byte string at the specified memory address (prefixed with `$`).
    *   Example: `db($500, "Hello Wake!");`

### Program Control

*   **`hlt()`**
    *   MicroASM: `HLT`
    *   Halts program execution.
    *   Example: `hlt();`
*   **`exit(code)`**
    *   MicroASM: `EXIT code`
    *   Exits the program with the specified return code (register or immediate value).
    *   Example: `exit(0); exit(R1);`

## Example Wake Program

```wake
// filepath: example.wake

#include "utils.wake" // Assumes utils.wake defines printMessage and print

void main() {
    db($100, "Hello from main!"); // Define string at address $100
    mov(RAX, $100);          // Move address to RAX

    call("print");             // Call print function (defined in utils.wake)
                               // which likely uses out(1, RAX)

    call("printMessage");      // Call another function from utils.wake

    mov(R1, 5);
    mov(R2, 10);
    cmp(R1, R2);
    jl("isLess", "notLess"); // Jump based on comparison
}

void isLess() {
    db($300, "R1 is less than R2");
    mov(RAX, $300);
    call("print");
    hlt();
}

void notLess() {
    db($400, "R1 is not less than R2");
    mov(RAX, $400);
    call("print");
    hlt();
}

// Assumed content of utils.wake:
// void printMessage() {
//     db($200, "Message from utils!");
//     mov(RAX, $200);
//     out(1, RAX);
//     ret();
// }
// void print() {
//     out(1, RAX); // Prints string at address in RAX
//     ret();
// }

```

This example demonstrates function definition, data definition (`db`), data movement (`mov`), function calls (`call`), comparison (`cmp`), conditional jumps (`jl`), and program termination (`hlt`). It also shows how `#include` can be used to incorporate code from other files.
