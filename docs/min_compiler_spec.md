# FSG最小编译器规格说明

> 蜉熵阁 - FSG语言自举计划
> 版本: 1.0 | 日期: 2026-04-29

---

## 1. 概述

### 1.1 设计目标

设计一个最小可行的FSG编译器（compiler_v0），能够：
- 解析FSG汇编源码
- 处理标签定义和引用
- 生成FSGB格式字节码
- 支持核心指令集

### 1.2 约束条件

- **语言限制**：仅使用FSG汇编指令实现
- **目标平台**：FSG虚拟机
- **可自举**：能用自己编译自己

---

## 2. 编译器输入输出

### 2.1 输入格式

```fsg
; hello.fsg - FSG汇编源码
.SECTION .text
.GLOBAL _start

_start:
    LOADIMM R0, 72        ; R0 = 72
    PRINT R0
    PRINTS msg_hello
    HALT

.SECTION .rodata
msg_hello:
.STR "Hello, FSG!"
```

### 2.2 输出格式

FSGB字节码文件（.fsgb），包含：
- 32字节文件头
- .text段（代码）
- .rodata段（字符串常量）
- CRC32校验和

---

## 3. 指令集支持

### 3.1 必须支持的指令

| 指令 | 操作码 | 参数 | 说明 |
|------|--------|------|------|
| NOP | 0x00 | - | 空操作 |
| HALT | 0x01 | - | 终止程序 |
| LOADIMM | 0x12 | R, imm32 | 加载立即数 |
| ADD | 0x20 | Rd, Ra, Rb | 加法 |
| SUB | 0x21 | Rd, Ra, Rb | 减法 |
| MUL | 0x22 | Rd, Ra, Rb | 乘法 |
| DIV | 0x23 | Rd, Ra, Rb | 除法 |
| MOD | 0x25 | Rd, Ra, Rb | 取模 |
| CMP | 0x30 | Ra, Rb | 比较 |
| JMP | 0x40 | offset | 无条件跳转 |
| JE | 0x41 | offset | 等于跳转 |
| JNE | 0x42 | offset | 不等于跳转 |
| JG | 0x43 | offset | 大于跳转 |
| JGE | 0x44 | offset | 大于等于跳转 |
| JL | 0x45 | offset | 小于跳转 |
| JLE | 0x46 | offset | 小于等于跳转 |
| PRINT | 0x50 | R | 打印整数 |
| PRINTS | 0x52 | addr | 打印字符串 |
| RET | 0x48 | - | 函数返回 |
| MOV | 0x15 | Rd, Rs | 寄存器移动 |
| PUSH | 0x13 | R | 压栈 |
| POP | 0x14 | R | 弹栈 |

### 3.2 可选支持的指令

| 指令 | 操作码 | 说明 |
|------|--------|------|
| LOAD | 0x10 | 内存加载 |
| STORE | 0x11 | 内存存储 |
| NEG | 0x24 | 取反 |
| AND | 0x31 | 位与 |
| OR | 0x32 | 位或 |
| XOR | 0x33 | 位异或 |
| NOT | 0x34 | 位非 |
| SHL | 0x35 | 左移 |
| SHR | 0x36 | 右移 |
| CALL | 0x47 | 函数调用 |
| INPUT | 0x51 | 输入 |

---

## 4. 汇编语法规范

### 4.1 指令格式

```
[标签:] 指令 [参数1, 参数2, ...]  [; 注释]
```

### 4.2 标签

- 标签由字母、数字、下划线组成
- 以冒号结尾
- 可出现在指令前或单独一行

```fsg
loop:                   ; 循环标签
    ADD R1, R1, R1
    JMP loop             ; 跳转到loop
```

### 4.3 寄存器

- R0-R7（共8个通用寄存器）
- 大小写不敏感

### 4.4 立即数

```fsg
LOADIMM R0, 42          ; 十进制
LOADIMM R0, 0x2A         ; 十六进制
LOADIMM R0, 0b101010     ; 二进制
LOADIMM R0, -100         ; 负数
```

### 4.5 段定义

```fsg
.SECTION .text           ; 代码段
.SECTION .rodata         ; 只读数据段
.SECTION .data           ; 可读写数据段
```

### 4.6 数据定义

```fsg
.STR "hello"             ; 字符串（自动添加null终止）
.DW 1, 2, 3, 4           ; 字列表
```

### 4.7 全局符号

```fsg
.GLOBAL _start           ; 声明全局入口
```

---

## 5. 编译器架构

### 5.1 两遍扫描设计

```
┌─────────────────────────────────────────────────────┐
│                    编译器流程                        │
├─────────────────────────────────────────────────────┤
│                                                      │
│  源码 ──► 第一遍扫描 ──► 符号表 ──► 第二遍扫描 ──► 字节码  │
│                  │                 │                │
│                  ▼                 ▼                │
│            收集标签          生成代码                │
│            计算地址          解析标签引用              │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 5.2 第一遍扫描

**任务**：收集所有标签定义及其地址

**伪代码**：
```
function first_pass(lines):
    labels = {}
    address = 0
    rodata_address = 0x1000
    in_rodata = false
    
    for each line:
        clean_line = remove_comment(line)
        
        if line is section directive:
            update in_rodata flag
            continue
        
        if line contains label:
            label_name = extract_label(line)
            if in_rodata:
                labels[label_name] = rodata_address
            else:
                labels[label_name] = address
        
        if line is .STR:
            rodata_address += len(string) + 1
        else if line is .DW:
            rodata_address += count(values) * 4
        else if line is instruction:
            address += instruction_length(line)
    
    return labels
```

### 5.3 第二遍扫描

**任务**：生成字节码，处理标签引用

**伪代码**：
```
function second_pass(lines, labels):
    output = []
    address = 0
    
    for each line:
        clean_line = remove_comment(line)
        
        if line is section directive or label:
            continue
        
        if line is .STR:
            emit_string(string)
        else if line is .DW:
            emit_words(values)
        else if line is instruction:
            opcode = parse_opcode(line)
            operands = parse_operands(line)
            
            emit(opcode)
            for each operand:
                if operand is label:
                    emit(labels[operand])
                else:
                    emit(operand)
            
            address += instruction_length(line)
    
    return output
```

### 5.4 标签解析规则

**前向引用**：允许跳转目标在引用点之后定义

```fsg
    JMP target      ; 前向引用
    ...
target:             ; 定义
    HALT
```

**后向引用**：常见于循环

```fsg
loop:               ; 定义
    ...
    JMP loop        ; 后向引用
```

---

## 6. 字节码生成

### 6.1 FSGB文件格式

```
偏移    大小    字段           说明
0x00    4       magic          "FSGB" (0x46534742)
0x04    2       version        0x0100
0x06    2       flags         标志位
0x08    4       entry_point   入口点偏移（默认0）
0x0C    4       text_size     .text段大小
0x10    4       data_size     .data段大小
0x14    4       rodata_size   .rodata段大小
0x18    4       symbol_count  符号数量
0x1C    4       debug_size    调试信息大小
0x20    -       code          代码开始
```

### 6.2 立即数编码

**小整数（-128 ~ 127）**：
```
[imm8]  ; 1字节
```

**大整数**：
```
[imm32] ; 4字节，大端序
```

### 6.3 跳转偏移计算

跳转目标 = 当前PC + 偏移量

```fsg
; 示例
0x00: JMP target    ; PC=0x00, 下一条指令PC=0x05
0x05: target: NOP   ; 目标地址=0x05
; 跳转偏移 = 0x05 - 0x05 = 0
```

---

## 7. 错误处理

### 7.1 语法错误

| 错误 | 说明 | 处理 |
|------|------|------|
| 未知指令 | 指令名不在指令表中 | 报错并退出 |
| 参数数量错误 | 参数个数不匹配 | 报错并退出 |
| 无效寄存器 | R8-R15或寄存器拼写错误 | 报错并退出 |
| 无效立即数 | 无法解析的数字格式 | 报错并退出 |

### 7.2 语义错误

| 错误 | 说明 | 处理 |
|------|------|------|
| 未定义标签 | 引用的标签不存在 | 报错并退出 |
| 重复定义标签 | 同一标签出现多次 | 报错并退出 |
| 无效段 | .SECTION参数错误 | 报错并退出 |

---

## 8. 测试用例

### 8.1 基础测试

```fsg
; test_basic.fsg
.SECTION .text
_start:
    LOADIMM R0, 42
    PRINT R0
    HALT
```

**预期输出**：42

### 8.2 算术运算测试

```fsg
; test_arith.fsg
.SECTION .text
_start:
    LOADIMM R0, 10
    LOADIMM R1, 3
    ADD R2, R0, R1      ; 13
    SUB R3, R0, R1      ; 7
    MUL R4, R0, R1      ; 30
    DIV R5, R0, R1      ; 3
    MOD R6, R0, R1      ; 1
    PRINT R2
    PRINT R3
    PRINT R4
    PRINT R5
    PRINT R6
    HALT
```

**预期输出**：13 7 30 3 1

### 8.3 条件跳转测试

```fsg
; test_jump.fsg
.SECTION .text
_start:
    LOADIMM R0, 0
    LOADIMM R1, 1
loop:
    ADD R0, R0, R1
    LOADIMM R2, 5
    CMP R0, R2
    JNE loop
    PRINT R0
    HALT
```

**预期输出**：5

### 8.4 字符串测试

```fsg
; test_string.fsg
.SECTION .text
_start:
    PRINTS msg
    LOADIMM R0, 10
    PRINT R0
    HALT

.SECTION .rodata
msg:
.STR "Hello, World!"
```

**预期输出**：Hello, World!

### 8.5 自举测试

```fsg
; bootstrap_test.fsg
.SECTION .text
.GLOBAL _start

_start:
    ; 输出编译器已就绪
    LOADIMM R0, str_ready
    PRINTS str_ready
    
    ; 测试汇编器功能
    LOADIMM R0, 100
    LOADIMM R1, 200
    ADD R2, R0, R1
    PRINT R2
    
    LOADIMM R0, 10
    PRINT R0
    
    HALT

.SECTION .rodata
str_ready:
.STR "FSG Assembler v1.0 - Bootstrap Ready!"
```

---

## 9. 性能目标

| 指标 | 目标 | 说明 |
|------|------|------|
| 编译速度 | < 1秒 | 编译1000行代码 |
| 内存占用 | < 1MB | 编译过程内存使用 |
| 代码密度 | > 50% | 实际指令/总空间 |

---

## 10. 扩展计划

### 10.1 Phase 1（当前）

- ✅ 基础指令支持
- ✅ 标签和跳转
- ✅ 字符串常量

### 10.2 Phase 2

- 变量声明支持
- 表达式解析
- 函数定义

### 10.3 Phase 3

- 优化pass
- 错误恢复
- 调试信息

---

*文档版本: 1.0*
*创建日期: 2026-04-29*
