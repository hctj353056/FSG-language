# FSG语言 - 自举编译器项目

> 蜉熵阁 - 蜉蝣 & 灵镜

## 项目概述

FSG（蜉熵阁汇编语言）是一个实验性的自举编译器项目，目标是实现"用FSG语言写FSG编译器"。

**核心特性：**
- 纯Python实现，无外部依赖
- 支持中文关键字编程
- 完整的自举流程（Stage 0-3）
- 跨平台兼容，支持手机环境运行

## 快速开始

### 编译FSG程序

```bash
# 使用Python编译器
python3 fsg编译器1.py examples/hello.fsg

# 使用内置命令编译到文件
python3 fsg编译器1.py compile examples/hello.fsg output.fsgb
```

### 运行编译产物

```bash
python3 simple_vm.py output.fsgb
```

### 自举验证

```bash
python3 fsg编译器1.py bootstrap

# 或使用验证脚本
python3 自举验证.py
```

## 项目结构

```
FSG-language/
├── simple_vm.py              # Python虚拟机 (Stage 0)
├── fsg编译器1.py             # Python编译器 (Stage 1)
├── fsg编译器2_中文版.fsg     # FSG汇编编译器 (Stage 2)
├── fsg编译器_自举版.fsgb     # 自举产物 (Stage 3)
├── 自举验证.py               # 自举验证脚本
├── fsg_lexer.py              # 词法分析器
├── fsg_ir.py                 # 中间表示
├── interpreter.py            # 解释器
├── examples/                 # 示例程序
│   ├── hello.fsg             # Hello World示例
│   ├── factorial.fsg         # 阶乘计算
│   ├── fib.fsg               # 斐波那契数列
│   └── bubblesort.fsg        # 冒泡排序
├── 早期符语/                  # 早期实验代码
│   └── 符语.py
└── docs/                     # 文档目录
    ├── FSG中文关键字.md      # 关键字参考
    ├── FSG语言双层词表规范.md
    ├── assembler_spec.md     # 汇编规格
    ├── bytecode_format.md    # 字节码格式
    └── vm_instruction_set.md # 虚拟机指令集
```

## 自举流程

```
Stage 0: simple_vm.py (Python虚拟机)
         ↓
Stage 1: fsg编译器1.py (Python编译器)
         ↓ 编译
Stage 2: fsg编译器2_中文版.fsg (FSG汇编)
         ↓ 编译
Stage 3: fsg编译器_自举版.fsgb (自举产物)
         ↓ VM执行
    "FSG v3.0*12345*"
```

## 支持的关键字

### 中文关键字

| 关键字 | 英文等价 | 说明 |
|--------|----------|------|
| 载常 | LOADIMM | 加载立即数 |
| 打印 | PRINT | 打印寄存器值 |
| 跳转 | JMP | 无条件跳转 |
| 若等跳转 | JE | 相等时跳转 |
| 若大于跳转 | JG | 大于时跳转 |
| 比较 | CMP | 比较寄存器 |
| 加 | ADD | 加法 |
| 赋值 | MOV | 赋值 |
| 停止 | HALT | 停止执行 |

## 示例程序

```fsg
.全局 _start

_start:
    载常 R0, 72
    打印 R0
    载常 R0, 42
    打印 R0
    停止
```

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v3.2 | 2026-04-30 | 添加内置命令支持 |
| v3.1 | 2026-04-30 | 修复跳转偏移bug |
| v3.0 | 2026-04-30 | 添加中文关键字支持 |
| v2.x | - | 早期版本 |
| v1.x | - | 初始版本 |

## 开发指南

### 环境要求

- Python >= 3.10
- 无外部依赖

### 代码风格

遵循PEP 8规范，支持中文变量和函数名。

## 作者

- 蜉蝣 - 项目设计者
- 灵镜 - AI助手

## 许可证

MIT License

---

*蜉熵阁 · FSG语言项目*
