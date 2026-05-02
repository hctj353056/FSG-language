# FSG-language - Bootstrap Compiler Project

> FuShangGe - FuYou & LingJing

## Project Overview

FSG (FuShangGe Assembly Language) is an experimental bootstrap compiler project aiming to implement "FSG compiler written in FSG language".

**Core Features:**
- Pure Python implementation with no external dependencies
- Chinese keyword support for programming
- Complete bootstrap process (Stage 0-3)
- Cross-platform compatibility, supports mobile environments

## Quick Start

### Compile FSG Program

```bash
# Using Python compiler
python3 fsg编译器1.py examples/hello.fsg

# Compile to file
python3 fsg编译器1.py compile examples/hello.fsg output.fsgb
```

### Run Compiled Output

```bash
python3 simple_vm.py output.fsgb
```

### Bootstrap Verification

```bash
python3 fsg编译器1.py bootstrap

# Or use verification script
python3 自举验证.py
```

## Project Structure

```
FSG-language/
├── simple_vm.py              # Python Virtual Machine (Stage 0)
├── fsg编译器1.py             # Python Compiler (Stage 1)
├── fsg编译器2_中文版.fsg     # FSG Assembly Compiler (Stage 2)
├── fsg编译器_自举版.fsgb     # Bootstrap Output (Stage 3)
├── 自举验证.py               # Bootstrap Verification Script
├── fsg_lexer.py              # Lexer
├── fsg_ir.py                 # Intermediate Representation
├── interpreter.py            # Interpreter
├── examples/                 # Example Programs
│   ├── hello.fsg             # Hello World
│   ├── factorial.fsg         # Factorial
│   ├── fib.fsg               # Fibonacci
│   └── bubblesort.fsg        # Bubble Sort
├── 早期符语/                  # Early Experimental Code
│   └── 符语.py
└── docs/                     # Documentation
    ├── FSG中文关键字.md      # Keyword Reference
    ├── FSG语言双层词表规范.md
    ├── assembler_spec.md     # Assembler Specification
    ├── bytecode_format.md    # Bytecode Format
    └── vm_instruction_set.md # VM Instruction Set
```

## Bootstrap Process

```
Stage 0: simple_vm.py (Python VM)
         ↓
Stage 1: fsg编译器1.py (Python Compiler)
         ↓ Compile
Stage 2: fsg编译器2_中文版.fsg (FSG Assembly)
         ↓ Compile
Stage 3: fsg编译器_自举版.fsgb (Bootstrap Output)
         ↓ VM Execute
    "FSG v3.0*12345*"
```

## Supported Keywords

### Chinese Keywords

| Chinese | English | Description |
|---------|---------|-------------|
| 载常 | LOADIMM | Load immediate value |
| 打印 | PRINT | Print register value |
| 跳转 | JMP | Unconditional jump |
| 若等跳转 | JE | Jump if equal |
| 若大于跳转 | JG | Jump if greater |
| 比较 | CMP | Compare registers |
| 加 | ADD | Addition |
| 赋值 | MOV | Move/Assign |
| 停止 | HALT | Halt execution |

## Example Program

```fsg
.全局 _start

_start:
    载常 R0, 72
    打印 R0
    载常 R0, 42
    打印 R0
    停止
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| v3.2 | 2026-04-30 | Added built-in command support |
| v3.1 | 2026-04-30 | Fixed jump offset bug |
| v3.0 | 2026-04-30 | Added Chinese keyword support |
| v2.x | - | Early versions |
| v1.x | - | Initial versions |

## Development Guide

### Requirements

- Python >= 3.10
- No external dependencies

### Code Style

Follow PEP 8, supports Chinese variable and function names.

## Authors

- FuYou - Project Designer
- LingJing - AI Assistant

## License

MIT License

---

*FuShangGe · FSG-language Project*
