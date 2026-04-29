# FSG汇编 - 中文关键字参考

## 操作码对照表

### 算术指令
| 中文 | 英文 | Opcode | 说明 |
|------|------|--------|------|
| 加 | ADD | 0x20 | Rdest = Ra + Rb |
| 减 | SUB | 0x21 | Rdest = Ra - Rb |
| 乘 | MUL | 0x22 | Rdest = Ra * Rb |
| 除 | DIV | 0x23 | Rdest = Ra / Rb |
| 取反 | NEG | 0x24 | Rdest = -Rsrc |
| 取余 | MOD | 0x25 | Rdest = Ra % Rb |

### 控制流
| 中文 | 英文 | Opcode | 说明 |
|------|------|--------|------|
| 跳转 | JMP | 0x40 | 无条件跳转 |
| 若等跳转 | JE | 0x41 | ZF=1时跳转 |
| 若不等跳转 | JNE | 0x42 | ZF=0时跳转 |
| 若大于跳转 | JG | 0x43 | SF=OF且ZF=0时跳转 |
| 若不小于跳转 | JGE | 0x44 | SF=OF时跳转 |
| 若小于跳转 | JL | 0x45 | SF≠OF时跳转 |
| 若不大于跳转 | JLE | 0x46 | SF≠OF或ZF=1时跳转 |
| 调用 | CALL | 0x47 | 函数调用 |
| 返回 | RET | 0x48 | 函数返回 |

### 数据传输
| 中文 | 英文 | Opcode | 说明 |
|------|------|--------|------|
| 加载 | LOAD | 0x10 | Rdest = [Raddr] |
| 存储 | STORE | 0x11 | [Raddr] = Rsrc |
| 载常 | LOADIMM | 0x12 | Rdest = imm32 |
| 入栈 | PUSH | 0x13 | push R |
| 出栈 | POP | 0x14 | pop R |
| 赋值 | MOV | 0x15 | Rdest = Rsrc |

### I/O
| 中文 | 英文 | Opcode | 说明 |
|------|------|--------|------|
| 打印 | PRINT | 0x50 | print R |
| 打印串 | PRINTS | 0x51 | print string at addr |
| 输入 | INPUT | 0x52 | input -> R |

### 系统
| 中文 | 英文 | Opcode | 说明 |
|------|------|--------|------|
| 停止 | HALT | 0xF0 | 停止执行 |
| 空操作 | NOP | 0xF1 | 空操作 |

## 寄存器
- R0, R1, R2, R3, R4, R5, R6, R7

## 示例程序

```fsg
.全局 _start

_start:
    ; 打印 Hello World
    载常 R0, 72      ; H
    打印 R0
    载常 R0, 101     ; e
    打印 R0
    载常 R0, 108     ; l
    打印 R0
    
    ; 循环
    载常 R0, 1
循环:
    打印 R0
    载常 R1, 1
    加 R2, R0, R1
    赋值 R0, R2
    载常 R1, 5
    比较 R0, R1
    若大于跳转 结束
    跳转 循环
结束:
    停止
```

## 编译器用法

```bash
# 编译
python3 fsg编译器1.py 程序.fsg 输出.fsgb

# 运行
python3 simple_vm.py 输出.fsgb
```
