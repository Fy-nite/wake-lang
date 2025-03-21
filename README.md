# Wake Language

Wake is a high-level language that compiles to MicroASM, combining readability with low-level control.

## Overview

Wake is designed to provide a more readable syntax for MicroASM programming without sacrificing power and control. It serves as an intermediate layer between high-level languages and machine code, making assembly programming more accessible while maintaining performance.

## Features

- Clean, C-like syntax for assembly programming
- Direct mapping to MicroASM instructions
- Support for functions, control flow, and data structures
- AST-based compilation for robust error handling and optimization
- Straightforward access to all CPU registers and instructions

## Installation

1. Clone the repository:
   ```
   git clone https://git.carsoncoder.com/Wake-lang.git
   cd Wake-lang
   ```

2. Ensure you have Python 3.7+ installed.

3. No additional dependencies are required to run the compiler.

## Usage

### Basic Compilation

To compile a Wake file to MicroASM:

```
python compiler.py myprogram.wake
```

This will generate `myprogram.masm`.

### Specifying Output File

```
python compiler.py myprogram.wake -o output.masm
```

### Wake Language Syntax

#### Including Files
```
#include "filename"
#M_include "masm_header.h"
```

#### Defining Functions
```
void main() {
    // Function body
}
```

#### Basic Instructions
```
void main() {
    mov(RAX, 10);        // Move value 10 to RAX register
    add(RAX, 5);         // Add 5 to RAX
    mov(RBX, RAX);       // Copy RAX to RBX
    
    db($100, "Hello");   // Define byte string at address $100
    call("printf");       // Call the printf function
    
    hlt();               // Halt execution
}
```

#### Control Flow
```
void checkValue() {
    mov(RAX, 10);
    cmp(RAX, 5);
    je("equal", "notEqual");
}

void equal() {
    out(1, "Values are equal");
    hlt();
}

void notEqual() {
    out(1, "Values are not equal");
    hlt();
}
```

## Instruction Reference

Wake supports the following instructions, each mapping directly to a MicroASM instruction:

### Data Movement
- `mov(dest, src)` - Move data between registers or set register value

### Arithmetic Operations
- `add(dest, src)` - Addition
- `sub(dest, src)` - Subtraction
- `mul(dest, src)` - Multiplication
- `div(dest, src)` - Division
- `inc(dest)` - Increment

### Logic and Bitwise Operations
- `and(dest, src)` - Bitwise AND
- `or(dest, src)` - Bitwise OR
- `xor(dest, src)` - Bitwise XOR
- `not(dest)` - Bitwise NOT
- `shl(dest, count)` - Shift left
- `shr(dest, count)` - Shift right

### Control Flow
- `jmp(label)` - Unconditional jump
- `cmp(a, b)` - Compare values
- `je(trueLabel, falseLabel)` - Jump if equal
- `jne(trueLabel, falseLabel)` - Jump if not equal
- `jl(trueLabel, falseLabel)` - Jump if less
- `jg(trueLabel, falseLabel)` - Jump if greater

### Stack Operations
- `push(value)` - Push onto stack
- `pop(dest)` - Pop from stack

### I/O Operations
- `out(port, value)` - Output to port
- `cout(port, value)` - Output character to port

### Memory
- `db(address, "string")` - Define string at address

### Program Control
- `hlt()` - Halt execution
- `exit(code)` - Exit with code

## Advanced Features

### Memory Addressing
Wake supports various memory addressing modes through MicroASM:

```
void memoryExample() {
    // Memory operations will be expanded in future versions
    mov(RAX, [RBX]);     // Move value at address in RBX to RAX
}
```

### MNI (Micro Native Interface)
Wake programs can interface with native system calls through MicroASM's MNI:

```
void systemInteraction() {
    // To be implemented in future versions
}
```

## Examples

### Hello World
```
// hello.wake - Simple Hello World program

void main() {
    db($100, "Hello, World!");
    mov(RAX, $100);
    out(1, RAX);
    hlt();
}
```

### Simple Counter
```
// counter.wake - Counts from 1 to 10

void main() {
    mov(R1, 1);         // Counter
    mov(R2, 10);        // Limit
    
    call("loop");
    hlt();
}

void loop() {
    out(1, R1);         // Print current count
    inc(R1);            // Increment counter
    cmp(R1, R2);        // Compare to limit
    jle("loop", "done"); // Loop if less than or equal
    call("done");
}

void done() {
    db($200, "Counting complete");
    mov(RAX, $200);
    out(1, RAX);
    hlt();
}
```

## Contributing

Contributions to Wake are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by the elegance of C and the power of Assembly language
- Thanks to all contributors who have helped shape this project
