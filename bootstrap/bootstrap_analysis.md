# FSG语言自举技术分析文档

> 蜉熵阁 - FSG语言自举计划
> 版本: 1.0 | 日期: 2026-04-29

---

## 目录

1. [自举原理](#1-自举原理)
2. [c4架构分析](#2-c4架构分析)
3. [FSG当前架构](#3-fsg当前架构)
4. [自举路线图](#4-自举路线图)
5. [可行性分析](#5-可行性分析)
6. [实施建议](#6-实施建议)

---

## 1. 自举原理

### 1.1 什么是自举（Bootstrap）

自举是编译器（或任何自引用系统）用自己的语言编写自身代码的能力。英文中称为 "bootstrapping"，源自"pull oneself up by one's bootstraps"（拽着鞋带把自己提起来）。

**核心概念**：
- Stage0：用外部语言（如Python/C）实现的编译器
- Stage1：用目标语言（FSG汇编）重写的编译器
- Stage2：用Stage1编译器编译Stage1代码，验证一致性

### 1.2 为什么需要自举

| 原因 | 说明 |
|------|------|
| **证明语言完整性** | 能用自己写编译器，说明语言足够强大 |
| **去除外部依赖** | 一旦自举成功，语言可以独立于创建它的工具运行 |
| **优化控制** | 可以用目标语言特性优化编译器本身 |
| **美学价值** | "真正的程序员用自己的语言写自己的编译器" |

### 1.3 自举的三个阶段

```
Stage0 (Python实现)
    │
    ├── 用Python编译器编译 Stage1 源码
    │
    ▼
Stage1 (FSG汇编实现)
    │
    ├── 用Stage0编译Stage1得到字节码
    ├── 用Stage1编译Stage1得到字节码
    │
    ▼
Stage2 (自举验证)
    └── 对比两份字节码，确保一致性
```

### 1.4 FSG自举的可行性分析

**有利因素**：
- ✅ FSG已有34条指令，覆盖核心功能
- ✅ Python虚拟机功能完整
- ✅ 汇编器assembler.fsg存在
- ✅ 有自举验证脚本bootstrap_verify.py
- ✅ c4参考实现证明小语言可自举

**挑战因素**：
- ⚠️ 当前assembler.fsg功能较简单，仅演示用
- ⚠️ 缺少高级语言特性（变量、表达式解析）
- ⚠️ 字节码格式需要支持更复杂的数据结构
- ⚠️ 需要实现完整的词法/语法分析器

---

## 2. c4架构分析

c4（C in Four Functions）是由Robert Swierczek编写的极简C编译器，约400行代码，可自编译。

### 2.1 四函数结构

```
┌─────────────────────────────────────────────────────┐
│                     main()                         │
│  - 初始化(内存分配、符号表、关键字)                    │
│  - 解析声明(parse declarations)                       │
│  - 虚拟机执行(run VM)                                │
└─────────────────────────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
┌─────────────────┐ ┌───────────┐ ┌─────────────────┐
│    next()       │ │   expr()  │ │     stmt()      │
│   词法分析器     │ │ 表达式解析 │ │   语句解析       │
│                 │ │           │ │                 │
│ - 跳过空白       │ │ - 优先级   │ │ - if/while     │
│ - 识别关键字     │ │ - 递归下降 │ │ - return       │
│ - 识别数字       │ │ - 生成字节码│ │ - 复合语句     │
│ - 识别标识符     │ │           │ │                 │
│ - 识别字符串     │ │           │ │                 │
└─────────────────┘ └───────────┘ └─────────────────┘
```

### 2.2 词法分析实现（next函数）

```c
void next() {
  char *pp;
  while (tk = *p) {
    ++p;
    if (tk == '\n') { /* 处理换行 */ }
    else if (tk == '#') { /* 跳过预处理 */ }
    else if ((tk >= 'a' && tk <= 'z') || tk == '_') {
      // 标识符哈希
      pp = p - 1;
      while (...) tk = tk * 147 + *p++;
      tk = (tk << 6) + (p - pp);
      // 符号表查找
      id = sym;
      while (id[Tk]) {
        if (tk == id[Hash] && !memcmp(...)) { tk = id[Tk]; return; }
        id = id + Idsz;
      }
      id[Name] = (int)pp;
      id[Hash] = tk;
      tk = id[Tk] = Id;
      return;
    }
    else if (tk >= '0' && tk <= '9') {
      // 数字解析（支持十进制/十六进制/八进制）
      if (ival = tk - '0') { while (*p >= '0' && *p <= '9') ... }
      tk = Num;
      return;
    }
    // 运算符处理 (=, +, -, *, /, &, |, ^, ...)
  }
}
```

### 2.3 递归下降解析（expr函数）

c4使用**优先级攀升法（Precedence Climbing）**：

```c
void expr(int lev) {
  // 1. 单目运算符 + 基本表达式
  if (tk == Num) { *++e = IMM; *++e = ival; next(); ty = INT; }
  else if (tk == '"') { ... }
  else if (tk == Id) { ... }
  else if (tk == '(') { next(); expr(Assign); ... }
  
  // 2. 二元运算符（按优先级）
  while (tk >= lev) {
    if (tk == Assign) { next(); expr(Assign); ... }
    else if (tk == Lor) { next(); expr(Lan); ... }      // ||
    else if (tk == Lan) { next(); expr(Or); ... }        // &&
    else if (tk == Or) { next(); expr(Xor); ... }        // |
    else if (tk == Xor) { next(); expr(And); ... }       // ^
    else if (tk == And) { next(); expr(Eq); ... }        // &
    else if (tk == Add) { next(); expr(Mul); ... }       // +
    else if (tk == Mul) { next(); expr(Inc); ... }      // *
    ...
  }
}
```

**运算符优先级表**：

| 优先级 | 运算符 | 结合性 |
|--------|--------|--------|
| 1 | `||` | 左 |
| 2 | `&&` | 左 |
| 3 | `\|` | 左 |
| 4 | `^` | 左 |
| 5 | `&` | 左 |
| 6 | `== !=` | 左 |
| 7 | `< > <= >=` | 左 |
| 8 | `<< >>` | 左 |
| 9 | `+ -` | 左 |
| 10 | `* / %` | 左 |
| 11 | `! ~ - * &` | 右 |
| 12 | `++ --` | 右 |

### 2.4 虚拟机指令集设计

c4虚拟机有35条指令：

```c
enum Opcode {
  LEA ,IMM ,JMP ,JSR ,BZ  ,BNZ ,ENT ,ADJ ,LEV ,LI  ,LC  ,SI  ,SC  ,PSH ,
  OR  ,XOR ,AND ,EQ  ,NE  ,LT  ,GT  ,LE  ,GE  ,SHL ,SHR ,ADD ,SUB ,MUL ,DIV ,MOD ,
  OPEN,READ,CLOS,PRTF,MALC,MSET,MCMP,MCPY,MMAP,DOPN,DSYM,QSRT,EXIT
};
```

**指令分类**：

| 类别 | 指令 | 说明 |
|------|------|------|
| 加载 | LEA, IMM, LI, LC | 加载地址/立即数/整数/字符 |
| 存储 | SI, SC | 存储整数/字符 |
| 控制流 | JMP, JSR, BZ, BNZ, ENT, LEV | 跳转/调用/条件分支/函数入口/返回 |
| 算术 | ADD, SUB, MUL, DIV, MOD | 整数运算 |
| 位运算 | OR, XOR, AND, SHL, SHR | 位操作 |
| 比较 | EQ, NE, LT, GT, LE, GE | 比较运算 |
| 系统 | PRTF, MALC, MSET, EXIT | 运行时支持 |

### 2.5 自举机制

c4能自编译的关键：

1. **自包含**：编译器源码不依赖任何外部库
2. **简单数据类型**：只用char、int、指针
3. **有限特性**：不支持float、结构体、动态内存分配代码
4. **固定内存布局**：符号表、代码区、数据区位置固定
5. **两遍扫描**：第一遍解析声明，第二遍执行代码

---

## 3. FSG当前架构

### 3.1 simple_vm.py分析

**核心组件**：

```
simple_vm.py
├── OpCode (IntEnum)      - 34条指令操作码定义
├── VMState (dataclass)   - 虚拟机状态(寄存器、PC、SP、内存)
├── Symbol (dataclass)    - 符号表条目
├── LoadedProgram         - 已加载程序
├── Assembler             - 汇编器(两遍扫描)
│   ├── _first_pass()     - 收集标签
│   ├── _second_pass()    - 生成字节码
│   └── _generate_bytecode() - FSGB格式输出
└── FSGVM                 - 虚拟机执行器
    ├── load_bytecode()   - 加载字节码
    ├── run()             - 执行主循环
    └── _execute_instruction() - 指令分派
```

**字节码格式（FSGB）**：

```
+------------------+
|   文件头 (32B)   |  - magic, version, entry_point, sizes
+------------------+
|   .text 段       |  - 代码
+------------------+
|   .rodata 段     |  - 只读数据(字符串)
+------------------+
|   校验和          |
+------------------+
```

### 3.2 汇编器assembler.fsg分析

**当前功能**（演示用）：
- ✅ 基本指令编码（LOADIMM, ADD, PRINT等）
- ✅ 标签定义和引用
- ✅ .SECTION指令（.text/.rodata）
- ✅ .STR字符串定义
- ✅ .DW数据定义
- ⚠️ 不支持变量声明
- ⚠️ 不支持表达式解析
- ⚠️ 不支持函数定义

### 3.3 字节码格式分析

**指令编码规范**：

| 指令 | opcode | 参数 | 长度 |
|------|--------|------|------|
| HALT | 0x01 | 无 | 1B |
| LOADIMM | 0x12 | reg(1) + imm(4) | 6B |
| ADD | 0x20 | rd(1) + ra(1) + rb(1) | 4B |
| JMP | 0x40 | offset(4) | 5B |
| PRINTS | 0x52 | addr(4) | 5B |

### 3.4 当前缺失的功能

| 缺失项 | 说明 | 优先级 |
|--------|------|--------|
| 变量声明 | `VAR x = 10` | 高 |
| 表达式解析 | `x + y * 2 > 10` | 高 |
| 函数定义 | `FUNC add(a, b)` | 高 |
| 局部变量 | 栈帧管理 | 中 |
| 错误处理 | 语法/语义错误报告 | 中 |
| 符号表 | 完整的标识符管理 | 高 |

---

## 4. 自举路线图

### 4.1 总体阶段

```
┌─────────────────────────────────────────────────────────────────┐
│                         FSG自举路线图                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 1: 分析与设计 (当前)                                       │
│  ├─ bootstrap_analysis.md (本文档)                               │
│  └─ min_compiler_spec.md (最小编译器规格)                         │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 2: 最小编译器 v0                                          │
│  ├─ compiler_v0.fsg (核心编译器)                                 │
│  ├─ test_min.fsg (测试用例)                                      │
│  └─ bootstrap_test_v0.py (验证脚本)                              │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 3: 自举验证                                               │
│  ├─ Stage0编译Stage1源码                                          │
│  ├─ Stage1编译Stage1源码                                         │
│  └─ 字节码一致性对比                                              │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 4: 功能增强                                               │
│  ├─ 添加变量支持                                                 │
│  ├─ 添加函数调用                                                 │
│  ├─ 添加表达式解析                                               │
│  └─ compiler_v1.fsg                                              │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 5: 完整自举                                               │
│  └─ fsg_compiler.fsg (完整FSG编译器，可自编译)                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 最小编译器设计规格

**目标**：编译器能处理基本的FSG程序，生成可执行字节码。

**必须支持的功能**：

```fsg
; 标签和跳转
loop:
    LOADIMM R0, 1
    ADD R1, R1, R0
    CMP R1, R0, 10
    JNE loop

; 字符串输出
PRINTS hello

; 基本算术
LOADIMM R0, 5
LOADIMM R1, 3
ADD R2, R0, R1  ; R2 = 8
```

**不需要的功能（暂不实现）**：
- 变量声明（直接用寄存器）
- 表达式解析（手写汇编）
- 函数调用（用JMP/CALL）

### 4.3 里程碑定义

| 里程碑 | 目标 | 验证方法 |
|--------|------|----------|
| M1 | 汇编器能编译带标签的代码 | compiler_v0编译assembler.fsg |
| M2 | 能执行条件跳转 | bootstrap_test.fsg输出正确 |
| M3 | Stage0=Stage1字节码 | 字节码逐字节对比 |
| M4 | 支持变量 | VAR x = 10 语法 |
| M5 | 支持函数 | FUNC foo() {} 语法 |
| M6 | 完整自举 | fsg_compiler.fsg自编译 |

---

## 5. 可行性分析

### 5.1 技术可行性

**FSG指令集完备性**：

| 指令类别 | 可行性 | 说明 |
|----------|--------|------|
| 数据传输 | ✅ | LOAD, STORE, MOV, LOADIMM |
| 算术运算 | ✅ | ADD, SUB, MUL, DIV, MOD |
| 比较跳转 | ✅ | CMP, JE, JNE, JMP |
| 函数调用 | ✅ | CALL, RET |
| I/O | ✅ | PRINT, PRINTS |

**结论**：FSG指令集足够实现编译器。

### 5.2 工作量评估

| 阶段 | 工作量 | 复杂度 |
|------|--------|--------|
| 最小编译器v0 | 500-800行FSG汇编 | 中 |
| 自举验证 | 200行测试代码 | 低 |
| 增强编译器 | 1000-1500行FSG汇编 | 高 |
| 完整编译器 | 2000+行FSG汇编 | 极高 |

**参考**：c4约400行C代码实现自举，FSG汇编密度略低，估计总工作量约3000行。

### 5.3 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 汇编器bug | 高 | 分阶段验证，每步测试 |
| 字节码格式不兼容 | 高 | 严格遵循FSGB格式 |
| 栈空间不足 | 中 | 预分配足够栈空间 |
| 调试困难 | 中 | Python验证脚本辅助 |

---

## 6. 实施建议

### 6.1 开发策略

1. **渐进式开发**：每实现一个功能立即测试
2. **Python验证**：每个阶段用Python脚本对比输出
3. **参考c4实现**：遇到困难时参考c4的解决方案
4. **文档先行**：先写规格说明，再写代码

### 6.2 测试策略

```python
# bootstrap_test.py 测试框架
def test_stage0_compiles_stage1():
    """Stage0能编译Stage1源码"""
    bytecode = python_assembler.assemble(stage1_source)
    assert len(bytecode) > 0
    assert verify_fsgb(bytecode)

def test_stage1_compiles_stage1():
    """Stage1能编译Stage1源码"""
    fsg_vm.load_bytecode(stage1_bytecode)
    output_bytecode = fsg_vm.compile(stage1_source)
    return output_bytecode

def test_bytecode_equivalence():
    """两份字节码一致"""
    bc1 = stage0.compile(source)
    bc2 = stage1.compile(source)
    assert bc1 == bc2
```

### 6.3 下一步行动

1. 创建 `min_compiler_spec.md` - 最小编译器规格
2. 实现 `compiler_v0.fsg` - 核心编译器
3. 编写 `bootstrap_test_v0.py` - 验证脚本
4. 运行自举测试
5. 迭代增强

---

## 附录A：c4指令集参考

```
LEA  - 加载局部变量地址
IMM  - 加载立即数
JMP  - 跳转
JSR  - 子程序调用
BZ   - 零跳转
BNZ  - 非零跳转
ENT  - 函数入口
ADJ  - 栈调整
LEV  - 函数返回
LI   - 加载整数
LC   - 加载字符
SI   - 存储整数
SC   - 存储字符
PSH  - 压栈
```

## 附录B：FSG指令集对照

```
LOAD   - 内存到寄存器
STORE  - 寄存器到内存
LOADIMM- 加载立即数
PUSH   - 压栈
POP    - 弹栈
MOV    - 寄存器移动
ADD/SUB/MUL/DIV/MOD - 算术运算
CMP    - 比较
JMP/JE/JNE/JG/JGE/JL/JLE - 条件跳转
CALL/RET - 函数调用
PRINT/PRINTS - 输出
```

---

*文档版本: 1.0*
*创建日期: 2026-04-29*
*作者: FSG自举计划*
