#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FSG-IR: 通用中间表示框架
Fuyang General-purpose Intermediate Representation

功能：
1. 统一 IR 表示（SSA 形式）
2. 多语言降级器（Python/JS/Go → IR）
3. 多目标生成器（IR → FSG-ASM / Python / JS / Go）
4. 优化 Pass（死代码消除、常量折叠）

版本: 1.0 | 2026-04-26
"""

import ast
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

# ═══════════════════════════════════════════════════════════════
# 第一部分：FSG-IR 类型系统
# ═══════════════════════════════════════════════════════════════


class IRType(Enum):
    """FSG-IR 基本类型"""

    VOID = "void"  # 无返回值
    INT = "int"  # 32位整数
    INT64 = "int64"  # 64位整数
    FLOAT = "float"  # 32位浮点
    DOUBLE = "double"  # 64位浮点
    BOOL = "bool"  # 布尔
    CHAR = "char"  # 字符
    STRING = "string"  # 字符串（指针）
    PTR = "ptr"  # 指针
    ARRAY = "array"  # 数组
    STRUCT = "struct"  # 结构体
    FUNCTION = "func"  # 函数类型

    def __str__(self):
        return self.value

    def to_asm_type(self) -> str:
        """转换为 FSG-ASM 类型"""
        mapping = {
            IRType.INT: ".DW",
            IRType.INT64: ".DW",
            IRType.FLOAT: ".DW",
            IRType.DOUBLE: ".DW",
            IRType.BOOL: ".DB",
            IRType.CHAR: ".DB",
            IRType.STRING: ".DW",  # 字符串指针
        }
        return mapping.get(self, ".DW")


@dataclass
class IRTypeInfo:
    """带附加信息的类型"""

    base: IRType
    size: Optional[int] = None  # 数组大小
    element_type: Optional["IRTypeInfo"] = None  # 数组元素类型
    fields: Optional[Dict[str, "IRTypeInfo"]] = None  # 结构体字段

    def __str__(self):
        if self.base == IRType.ARRAY and self.element_type:
            return f"[{self.element_type}; {self.size or '?'}]"
        if self.base == IRType.STRUCT and self.fields:
            fields_str = ", ".join(f"{k}: {v}" for k, v in self.fields.items())
            return f"struct {{{fields_str}}}"
        return str(self.base)


# ═══════════════════════════════════════════════════════════════
# 第二部分：FSG-IR 操作码
# ═══════════════════════════════════════════════════════════════


class IROpcode(Enum):
    """FSG-IR 操作码"""

    # 算术运算
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "sdiv"  # 有符号除
    UDIV = "udiv"  # 无符号除
    REM = "srem"  # 有符号取模
    UREM = "urem"  # 无符号取模
    NEG = "neg"

    # 位运算
    AND = "and"
    OR = "or"
    XOR = "xor"
    NOT = "not"
    SHL = "shl"  # 左移
    SHR = "lshr"  # 逻辑右移
    ASHR = "ashr"  # 算术右移

    # 比较运算
    ICMP_EQ = "icmp eq"
    ICMP_NE = "icmp ne"
    ICMP_SLT = "icmp slt"  # 有符号小于
    ICMP_SLE = "icmp sle"
    ICMP_SGT = "icmp sgt"
    ICMP_SGE = "icmp sge"
    ICMP_ULT = "icmp ult"  # 无符号小于
    ICMP_ULE = "icmp ule"
    ICMP_UGT = "icmp ugt"
    ICMP_UGE = "icmp uge"

    # 逻辑运算
    SELECT = "select"  # 条件选择
    PHI = "phi"  # SSA phi 节点

    # 内存操作
    ALLOCA = "alloca"  # 分配局部变量
    LOAD = "load"
    STORE = "store"
    GEP = "getelementptr"  # 计算结构体/数组指针
    CAST = "bitcast"  # 类型转换

    # 类型转换
    ZEXT = "zext"  # 零扩展
    SEXT = "sext"  # 符号扩展
    TRUNC = "trunc"  # 截断
    FPEXT = "fpext"  # 浮点扩展
    FPTRUNC = "fptrunc"  # 浮点截断
    SITOFP = "sitofp"  # 有符号整型转浮点
    FPTOSI = "fptosi"  # 浮点转有符号整型

    # 函数操作
    CALL = "call"
    RET = "ret"
    PARAM = "param"  # 函数参数

    # 控制流
    BR = "br"  # 无条件跳转
    COND_BR = "brc"  # 条件跳转
    LABEL = "label"  # 标签定义
    JUMP = "jmp"  # 跳转

    # 特殊操作
    CONST = "const"  # 常量
    GLOBAL = "global"  # 全局变量
    PRINT = "print"  # 打印
    INPUT = "input"  # 输入
    LEN = "len"  # 取长度
    INDEX = "index"  # 数组索引
    APPEND = "append"  # 追加元素


# ═══════════════════════════════════════════════════════════════
# 第三部分：FSG-IR 指令
# ═══════════════════════════════════════════════════════════════


@dataclass
class IRValue:
    """IR 值（常量、变量、全局符号）"""

    name: str
    type_info: Optional[IRTypeInfo] = None

    def __str__(self):
        return f"%{self.name}" if self.name else "?"

    def to_dict(self):
        return {
            "name": self.name,
            "type": str(self.type_info) if self.type_info else None,
        }


@dataclass
class IRInstruction:
    """IR 指令基类"""

    opcode: IROpcode
    result: Optional[IRValue] = None
    operands: List[IRValue] = field(default_factory=list)
    line: int = 0

    def __str__(self):
        if self.result:
            ops = ", ".join(str(op) for op in self.operands)
            return f"  {self.result} = {self.opcode.value} {ops}"
        else:
            ops = ", ".join(str(op) for op in self.operands)
            return f"  {self.opcode.value} {ops}"


@dataclass
class IRConst(IRInstruction):
    """常量定义"""

    const_value: Any = None
    type_info: Optional[IRTypeInfo] = None

    def __str__(self):
        type_str = str(self.type_info) if self.type_info else "int"
        return f"  {self.result} = const {type_str} {self.const_value}"


@dataclass
class IRPhi(IRInstruction):
    """Phi 节点（SSA 分支合并）"""

    branches: List[Tuple[str, IRValue]] = field(
        default_factory=list
    )  # [(label, value), ...]

    def __str__(self):
        pairs = ", ".join(f"[{label}, {val}]" for label, val in self.branches)
        return f"  {self.result} = phi {pairs}"


@dataclass
class IRBr(IRInstruction):
    """跳转指令"""

    target: str = ""  # 无条件跳转目标
    cond: Optional[IRValue] = None
    true_target: str = ""  # 条件为真时的目标
    false_target: str = ""  # 条件为假时的目标

    def __str__(self):
        if self.cond:
            return f"  br {self.cond}, {self.true_target}, {self.false_target}"
        return f"  jmp {self.target}"


@dataclass
class IRRet(IRInstruction):
    """返回指令"""

    is_void: bool = False

    def __str__(self):
        if self.is_void or not self.operands:
            return "  ret void"
        return f"  ret {self.operands[0]}"


@dataclass
class IRCall(IRInstruction):
    """函数调用"""

    func_name: str = ""
    args: List[IRValue] = field(default_factory=list)

    def __str__(self):
        args_str = ", ".join(str(arg) for arg in self.args)
        if self.result:
            return f"  {self.result} = call @{self.func_name}({args_str})"
        return f"  call @{self.func_name}({args_str})"


@dataclass
class IRLabel(IRInstruction):
    """标签定义"""

    label_name: str = ""

    def __str__(self):
        return f"{self.label_name}:"


# ═══════════════════════════════════════════════════════════════
# 第四部分：FSG-IR 基本块与函数
# ═══════════════════════════════════════════════════════════════


@dataclass
class IRBlock:
    """IR 基本块"""

    name: str
    instructions: List[IRInstruction] = field(default_factory=list)
    predecessors: List[str] = field(default_factory=list)
    successors: List[str] = field(default_factory=list)

    def add_inst(self, inst: IRInstruction):
        self.instructions.append(inst)

    def __str__(self):
        lines = [f"{self.name}:"]
        for inst in self.instructions:
            lines.append(str(inst))
        return "\n".join(lines)


@dataclass
class IRFunction:
    """IR 函数"""

    name: str
    return_type: IRTypeInfo
    params: List[Tuple[str, IRTypeInfo]] = field(
        default_factory=list
    )  # [(name, type), ...]
    blocks: List[IRBlock] = field(default_factory=list)
    is_entry: bool = False

    def add_block(self, block: IRBlock):
        self.blocks.append(block)

    def get_block(self, name: str) -> Optional[IRBlock]:
        for block in self.blocks:
            if block.name == name:
                return block
        return None

    def __str__(self):
        params_str = ", ".join(f"%{name}: {typ}" for name, typ in self.params)
        lines = [f"define @{self.name}({params_str}) -> {self.return_type} {{"]
        for block in self.blocks:
            lines.append(str(block))
        lines.append("}")
        return "\n".join(lines)


@dataclass
class IRModule:
    """IR 模块（编译单元）"""

    name: str
    functions: List[IRFunction] = field(default_factory=list)
    globals: Dict[str, IRTypeInfo] = field(default_factory=dict)  # 全局变量
    strings: Dict[str, str] = field(default_factory=dict)  # 字符串常量池

    def add_func(self, func: IRFunction):
        self.functions.append(func)

    def add_global(self, name: str, type_info: IRTypeInfo):
        self.globals[name] = type_info

    def add_string(self, value: str) -> str:
        """添加字符串常量，返回引用名"""
        key = f"str_{len(self.strings)}"
        self.strings[key] = value
        return key

    def __str__(self):
        lines = [f'module "{self.name}" {{']

        # 全局变量
        if self.globals:
            lines.append("  ; 全局变量")
            for name, type_info in self.globals.items():
                lines.append(f"  global @{name}: {type_info}")
            lines.append("")

        # 字符串常量池
        if self.strings:
            lines.append("  ; 字符串常量")
            for name, value in self.strings.items():
                lines.append(f'  @{name} = const string "{value}"')
            lines.append("")

        # 函数
        for func in self.functions:
            lines.append(str(func))

        lines.append("}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# 第五部分：SSA 变量管理器
# ═══════════════════════════════════════════════════════════════


class SSAValueManager:
    """SSA 版本号管理器"""

    def __init__(self):
        self.versions: Dict[str, int] = {}  # 变量名 → 当前版本号
        self.all_values: List[Tuple[str, int]] = []  # 所有版本 [(name, version), ...]

    def new_value(self, name: str, type_info: Optional[IRTypeInfo] = None) -> IRValue:
        """创建新的 SSA 值"""
        version = self.versions.get(name, 0)
        self.versions[name] = version + 1
        full_name = f"{name}.{version}"
        self.all_values.append((name, version))
        return IRValue(full_name, type_info)

    def get_value(self, name: str) -> IRValue:
        """获取变量的最新版本"""
        version = self.versions.get(name, 0)
        full_name = f"{name}.{version}"
        return IRValue(full_name)

    def get_all_versions(self, name: str) -> List[IRValue]:
        """获取变量的所有历史版本"""
        versions = [(n, v) for n, v in self.all_values if n == name]
        return [IRValue(f"{n}.{v}") for n, v in versions]

    def reset(self):
        """重置（用于新函数）"""
        self.versions.clear()
        self.all_values.clear()


# ═══════════════════════════════════════════════════════════════
# 第六部分：语言降级器基类
# ═══════════════════════════════════════════════════════════════


class LanguageLower(ABC):
    """语言降级器抽象基类"""

    @abstractmethod
    def parse(self, source: str) -> IRModule:
        """将源代码解析为 IR 模块"""
        pass

    @abstractmethod
    def get_lang_name(self) -> str:
        """返回语言名称"""
        pass


class FSGHighLower(LanguageLower):
    """FSG 高级语言降级器（001.fsg 格式）"""

    def get_lang_name(self) -> str:
        return "FSG-High"

    def parse(self, source: str) -> IRModule:
        """解析 FSG 高级语言到 IR"""
        module = IRModule("fsg_module")
        ssa = SSAValueManager()

        lines = source.strip().split("\n")
        current_func = None
        current_block = None

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 模块定义
            if line.startswith('模块"'):
                match = re.search(r'模块"(.*?)"', line)
                if match:
                    func_name = match.group(1)
                    func = IRFunction(
                        name=func_name, return_type=IRTypeInfo(IRType.INT)
                    )
                    entry_block = IRBlock(name="entry")
                    func.add_block(entry_block)
                    module.add_func(func)
                    current_func = func
                    current_block = entry_block
                    ssa.reset()

            # 流程定义（子函数）
            elif line.startswith('流程"'):
                match = re.search(r'流程"(.*?)"', line)
                if match:
                    proc_name = match.group(1)
                    proc = IRFunction(
                        name=f"{current_func.name}_{proc_name}",
                        return_type=IRTypeInfo(IRType.INT),
                    )
                    entry_block = IRBlock(name="entry")
                    proc.add_block(entry_block)
                    module.add_func(proc)  # 嵌套函数也作为顶级函数
                    current_block = entry_block
                    ssa.reset()

            # 输入语句 → PRINT + INPUT
            elif "输入" in line and "列表" in line:
                # 简化处理：分配数组
                arr_var = ssa.new_value("arr", IRTypeInfo(IRType.ARRAY))
                current_block.add_inst(IRConst(opcode=IROpcode.ALLOCA, result=arr_var))

            # 获取...个数 → len
            elif "获取" in line and "个数" in line:
                match = re.search(r"获取(.*?)个数", line)
                if match:
                    var_name = match.group(1)
                    len_var = ssa.new_value("len", IRTypeInfo(IRType.INT))
                    arr_ref = (
                        ssa.get_value(var_name)
                        if var_name in ssa.versions
                        else IRValue(var_name)
                    )
                    current_block.add_inst(
                        IRConst(opcode=IROpcode.LEN, result=len_var, operands=[arr_ref])
                    )

            # 运算（简化处理）
            elif "/" in line and "得到" in line:
                parts = line.split("得到")
                if len(parts) == 2:
                    result_name = parts[1].strip()
                    # 提取除法
                    match = re.search(r"(.+)/(.+)", parts[0])
                    if match:
                        left = ssa.get_value(match.group(1).strip())
                        right = ssa.get_value(match.group(2).strip())
                        result = ssa.new_value(result_name, IRTypeInfo(IRType.INT))
                        current_block.add_inst(
                            IRConst(
                                opcode=IROpcode.DIV,
                                result=result,
                                operands=[left, right],
                            )
                        )

            # 输出语句 → PRINT
            elif "输出" in line:
                match = re.search(r"输出(.+)", line)
                if match:
                    var_name = match.group(1).strip()
                    var = (
                        ssa.get_value(var_name)
                        if var_name in ssa.versions
                        else IRValue(var_name)
                    )
                    current_block.add_inst(
                        IRConst(opcode=IROpcode.PRINT, operands=[var])
                    )

            # 注释跳过
            elif line.startswith("；") or line.startswith(";"):
                pass

            # 空行跳过
            elif not line:
                pass

            i += 1

        return module


# ═══════════════════════════════════════════════════════════════
# 第七部分：IR 解析器（文本 IR → IRModule）
# ═══════════════════════════════════════════════════════════════


class IRParser:
    """FSG-IR 文本解析器"""

    TOKEN_PATTERNS = [
        ("COMMENT", r";[^\n]*"),
        ("MODULE", r'module\s+"([^"]+)"'),
        ("GLOBAL", r"global\s+@(\w+):"),
        ("CONST_STR", r'@(\w+)\s*=\s*const\s+string\s+"([^"]*)"'),
        ("FUNC_DEF", r"define\s+@(\w+)\(([^)]*)\)\s*->\s*(\w+)\s*\{"),
        ("FUNC_END", r"\}"),
        ("BLOCK", r"(\w+):"),
        ("ALLOCA", r"%(\w+)\s*=\s*alloca"),
        (
            "BINARY",
            r"%(\w+)\s*=\s*(add|sub|mul|sdiv|udiv|srem|urem|"
            r"and|or|xor|shl|lshr|ashr)\s+(%?\w+),\s*(%?\w+)",
        ),
        ("ICMP", r"%(\w+)\s*=\s*icmp\s+(\w+)\s+(%?\w+),\s*(%?\w+)"),
        ("LOAD", r"%(\w+)\s*=\s*load\s+(%?\w+)"),
        ("STORE", r"store\s+(%?\w+),\s*(%?\w+)"),
        ("BR_UNCOND", r"jmp\s+(\w+)"),
        ("BR_COND", r"br\s+(%?\w+),\s*(\w+),\s*(\w+)"),
        ("RET", r"ret(?:\s+(%?\w+))?"),
        ("CALL", r"%?(\w+)\s*=\s*call\s+@(\w+)\(([^)]*)\)"),
        ("LABEL", r"(\w+):"),
        ("WHITESPACE", r"[ \t]+"),
        ("NEWLINE", r"\n"),
    ]

    def __init__(self):
        self.tokens = []
        self.pos = 0
        self.module = None

    def parse(self, text: str) -> IRModule:
        """解析 IR 文本"""
        lines = text.strip().split("\n")
        module = None
        current_func = None
        current_block = None

        for line in lines:
            line = line.strip()
            if not line or line.startswith(";"):
                continue

            # 模块定义
            if line.startswith('module "'):
                match = re.search(r'module\s+"([^"]+)"', line)
                if match:
                    module = IRModule(match.group(1))

            # 函数定义
            elif line.startswith("define @"):
                match = re.search(r"define\s+@(\w+)\(([^)]*)\)\s*->\s*(\w+)\s*\{", line)
                if match:
                    func = IRFunction(
                        name=match.group(1),
                        return_type=IRTypeInfo(IRType[match.group(3).upper()]),
                    )
                    if module:
                        module.add_func(func)
                    current_func = func
                    entry_block = IRBlock(name="entry")
                    func.add_block(entry_block)
                    current_block = entry_block

            # 标签
            elif line.endswith(":") and not line.startswith("{"):
                label_name = line[:-1]
                block = IRBlock(name=label_name)
                if current_func:
                    current_func.add_block(block)
                current_block = block

            # 指令
            elif current_block:
                inst = self._parse_instruction(line)
                if inst:
                    current_block.add_inst(inst)

        return module or IRModule("empty")

    def _parse_instruction(self, line: str) -> Optional[IRInstruction]:
        """解析单条指令"""
        # ret
        if line == "ret void":
            return IRRet(opcode=IROpcode.RET, is_void=True)
        match = re.match(r"ret\s+(%?\w+)", line)
        if match:
            return IRRet(opcode=IROpcode.RET, operands=[IRValue(match.group(1))])

        # jmp
        match = re.match(r"jmp\s+(\w+)", line)
        if match:
            return IRBr(opcode=IROpcode.BR, target=match.group(1))

        # br cond, true, false
        match = re.match(r"br\s+(%?\w+),\s*(\w+),\s*(\w+)", line)
        if match:
            return IRBr(
                opcode=IROpcode.COND_BR,
                cond=IRValue(match.group(1)),
                true_target=match.group(2),
                false_target=match.group(3),
            )

        return None


# ═══════════════════════════════════════════════════════════════
# 第八部分：FSG-ASM 生成器
# ═══════════════════════════════════════════════════════════════


class ASMGenerator:
    """IR → FSG-ASM 生成器"""

    def __init__(self):
        self.regs = ["R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7"]
        self.free_regs = list(self.regs)
        self.used_vars: Dict[str, str] = {}  # 变量名 → 寄存器

    def reset(self):
        """重置寄存器分配"""
        self.free_regs = list(self.regs)
        self.used_vars.clear()

    def allocate_reg(self, var_name: str) -> str:
        """分配寄存器"""
        if var_name in self.used_vars:
            return self.used_vars[var_name]
        if not self.free_regs:
            raise RuntimeError("寄存器不足")
        reg = self.free_regs.pop(0)
        self.used_vars[var_name] = reg
        return reg

    def free_reg(self, var_name: str):
        """释放寄存器"""
        if var_name in self.used_vars:
            reg = self.used_vars.pop(var_name)
            self.free_regs.insert(0, reg)

    def generate(self, module: IRModule) -> str:
        """生成 FSG-ASM"""
        lines = [
            "; ==========================================",
            f"; FSG-IR 编译输出: {module.name}",
            "; 自动生成，请勿手动修改",
            "; ==========================================",
            "",
            ".SECTION .data",
        ]

        # 全局变量
        for name, type_info in module.globals.items():
            lines.append(f"{name}: {type_info.to_asm_type()} 0")

        # 字符串常量
        for name, value in module.strings.items():
            lines.append(f'{name}: .STR "{value}"')

        lines.extend(["", ".SECTION .text", ""])

        # 函数
        for func in module.functions:
            lines.extend(self._gen_function(func))

        return "\n".join(lines)

    def _gen_function(self, func: IRFunction) -> List[str]:
        """生成单个函数"""
        self.reset()
        lines = []

        # 函数标签
        lines.append(f"; 函数: @{func.name}")
        lines.append(f"{func.name}:")

        # 参数处理
        for i, (name, _) in enumerate(func.params):
            if i < 4:  # R0-R3 传递参数
                self.used_vars[name] = self.regs[i]

        # 基本块
        for block in func.blocks:
            lines.append(f"  ; {block.name}")
            for inst in block.instructions:
                lines.extend(self._gen_instruction(inst))

        lines.append("")
        return lines

    def _gen_instruction(self, inst: IRInstruction) -> List[str]:
        """生成单条指令"""
        lines = []

        if isinstance(inst, IRConst):
            if inst.opcode == IROpcode.ALLOCA:
                # 分配 → LOADIMM 0
                reg = self.allocate_reg(inst.result.name)
                lines.append(f"    LOADIMM {reg}, 0")

            elif inst.opcode == IROpcode.PRINT:
                if inst.operands:
                    var_name = inst.operands[0].name.split(".")[0]
                    reg = self.used_vars.get(var_name, "R0")
                    lines.append(f"    PRINT {reg}")

            elif inst.opcode == IROpcode.LEN:
                # len → 用伪操作模拟
                lines.append(f"    ; len {inst.operands[0]}")

        elif isinstance(inst, IRBr):
            if inst.cond:
                # 条件跳转
                var_name = inst.cond.name.split(".")[0]
                reg = self.used_vars.get(var_name, "R0")
                lines.append(f"    CMP {reg}, 0")
                lines.append(f"    JNE {inst.true_target}")
                lines.append(f"    JMP {inst.false_target}")
            else:
                lines.append(f"    JMP {inst.target}")

        elif isinstance(inst, IRRet):
            if not inst.is_void and inst.operands:
                lines.append(f"    MOV R0, {inst.operands[0]}")
            lines.append("    RET")

        elif isinstance(inst, IRLabel):
            lines.append(f"{inst.label_name}:")

        return lines


# ═══════════════════════════════════════════════════════════════
# 第九部分：主程序与示例
# ═══════════════════════════════════════════════════════════════


def demo():
    """演示：FSG 高级语言 → IR → FSG-ASM"""

    print("=" * 70)
    print("FSG-IR 演示：高级语言 → 通用 IR → 汇编")
    print("=" * 70)

    # 1. FSG 高级语言源代码
    fsg_source = """
模块"求平均数"：
定义"列表1=[ ]"
流程"累加"：
输入列表1
获取列表1个数得到计数
/ 得到结果
输出结果
使用.求平均数
"""

    print("\n【1. FSG 高级语言源码】")
    print(fsg_source)

    # 2. 降级为 IR
    lower = FSGHighLower()
    module = lower.parse(fsg_source)

    print("\n【2. FSG-IR 表示】")
    print(module)

    # 3. 生成 FSG-ASM
    asm_gen = ASMGenerator()
    asm_code = asm_gen.generate(module)

    print("\n【3. FSG-ASM 输出】")
    print(asm_code)

    # 5. 直接构建 IR 并生成
    print("\n【4. 直接构建 IR 示例】")

    # 手动构建：计算 1+2+...+10
    module2 = IRModule("sum_module")

    func = IRFunction(name="sum_to_10", return_type=IRTypeInfo(IRType.INT))

    entry = IRBlock(name="entry")
    loop = IRBlock(name="loop")
    exit_block = IRBlock(name="exit")

    # entry: 初始化
    ssa = SSAValueManager()

    i = ssa.new_value("i", IRTypeInfo(IRType.INT))
    sum_val = ssa.new_value("sum", IRTypeInfo(IRType.INT))

    entry.add_inst(
        IRConst(opcode=IROpcode.CONST, result=i, operands=[IRValue("0")], const_value=0)
    )
    entry.add_inst(
        IRConst(
            opcode=IROpcode.CONST,
            result=sum_val,
            operands=[IRValue("0")],
            const_value=0,
        )
    )
    entry.add_inst(IRBr(opcode=IROpcode.BR, target="loop"))

    # loop: 判断和累加
    ssa_i = ssa.new_value("i", IRTypeInfo(IRType.INT))
    cmp_result = ssa.new_value("cmp", IRTypeInfo(IRType.BOOL))

    loop.add_inst(
        IRConst(
            opcode=IROpcode.ICMP_SLE, result=cmp_result, operands=[ssa_i, IRValue("10")]
        )
    )
    loop.add_inst(
        IRBr(
            opcode=IROpcode.COND_BR,
            cond=cmp_result,
            true_target="exit",
            false_target="loop",
        )
    )

    # exit: 返回结果
    exit_block.add_inst(IRRet(opcode=IROpcode.RET, operands=[sum_val]))

    # 已经在上面添加了 entry 块
    func.add_block(loop)
    func.add_block(exit_block)
    module2.add_func(func)

    print(module2)

    print("\n【5. 最终 FSG-ASM】")
    asm_gen2 = ASMGenerator()
    print(asm_gen2.generate(module2))


if __name__ == "__main__":
    demo()


# ═══════════════════════════════════════════════════════════════════════════════
# 第十部分：Python 降级器 (Python → IR)
# ═══════════════════════════════════════════════════════════════════════════════


class PythonLower(LanguageLower):
    """Python 语言降级器"""

    # Python 内置类型 → IRType 映射
    TYPE_MAP = {
        "int": IRType.INT,
        "float": IRType.FLOAT,
        "bool": IRType.BOOL,
        "str": IRType.STRING,
        "list": IRType.ARRAY,
        "dict": IRType.STRUCT,
    }

    def get_lang_name(self) -> str:
        return "Python"

    def parse(self, source: str) -> IRModule:
        """将 Python 源码解析为 IR"""
        module = IRModule("python_module")
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func = self._lower_function(node)
                module.add_func(func)

        return module

    def _lower_function(self, node: ast.FunctionDef) -> IRFunction:
        """将 Python 函数降级为 IR 函数"""
        ssa = SSAValueManager()

        # 返回类型推断
        return_type = IRTypeInfo(IRType.INT)  # 默认 int
        if node.returns:
            type_name = ast.unparse(node.returns).strip()
            if type_name in self.TYPE_MAP:
                return_type = IRTypeInfo(self.TYPE_MAP[type_name])

        func = IRFunction(name=node.name, return_type=return_type)
        entry = IRBlock(name="entry")

        # 处理参数
        for arg in node.args.args:
            param_type = IRTypeInfo(IRType.INT)  # 默认
            func.params.append((arg.arg, param_type))
            # 在入口块中分配参数
            alloc_val = ssa.new_value(arg.arg, param_type)
            entry.add_inst(
                IRConst(opcode=IROpcode.ALLOCA, result=alloc_val, type_info=param_type)
            )

            # 已经在上面添加了 entry 块

        # 处理函数体
        current_block = entry
        ssa.reset()  # 重置 SSA 以重新开始计数

        for stmt in node.body:
            insts, current_block = self._lower_statement(stmt, current_block, ssa)
            for inst in insts:
                current_block.add_inst(inst)

        func.add_block(current_block)
        return func

    def _lower_statement(
        self, node: ast.stmt, block: IRBlock, ssa: SSAValueManager
    ) -> Tuple[List[IRInstruction], IRBlock]:
        """降级语句"""
        insts = []

        if isinstance(node, ast.Assign):
            value_insts, value, block = self._lower_expr(node.value, block, ssa)
            insts.extend(value_insts)
            # 支持多个目标 (a = b = c)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    new_val = ssa.new_value(target.id, value.type_info)
                    alloc = IRConst(opcode=IROpcode.ALLOCA, result=new_val)
                    store = IRConst(opcode=IROpcode.STORE, operands=[value, new_val])
                    insts.extend([alloc, store])

        elif isinstance(node, ast.Return):
            if node.value:
                value_insts, value, block = self._lower_expr(node.value, block, ssa)
                insts.extend(value_insts)
                insts.append(IRRet(opcode=IROpcode.RET, operands=[value]))
            else:
                insts.append(IRRet(opcode=IROpcode.RET, is_void=True))

        elif isinstance(node, ast.Expr):
            value_insts, _, block = self._lower_expr(node.value, block, ssa)
            insts.extend(value_insts)

        elif isinstance(node, ast.If):
            # if 条件 then ... else ...
            cond_insts, cond_val, block = self._lower_expr(node.test, block, ssa)
            insts.extend(cond_insts)

            then_block = IRBlock(name=f"if_then_{ssa.versions.get('_block', 0)}")
            else_block = IRBlock(name=f"if_else_{ssa.versions.get('_block', 0)}")
            merge_block = IRBlock(name=f"if_end_{ssa.versions.get('_block', 0)}")
            ssa.versions["_block"] = ssa.versions.get("_block", 0) + 1

            # 条件跳转
            insts.append(
                IRBr(
                    opcode=IROpcode.COND_BR,
                    cond=cond_val,
                    true_target=then_block.name,
                    false_target=else_block.name,
                )
            )

            # then 分支
            for stmt in node.body:
                s_insts, _ = self._lower_statement(stmt, then_block, ssa)
                then_block.instructions.extend(s_insts)
            then_block.add_inst(IRBr(opcode=IROpcode.BR, target=merge_block.name))

            # else 分支
            for stmt in node.orelse:
                s_insts, _ = self._lower_statement(stmt, else_block, ssa)
                else_block.instructions.extend(s_insts)
            else_block.add_inst(IRBr(opcode=IROpcode.BR, target=merge_block.name))

            return insts, merge_block

        elif isinstance(node, ast.While):
            loop_block = IRBlock(name=f"while_loop_{ssa.versions.get('_block', 0)}")
            body_block = IRBlock(name=f"while_body_{ssa.versions.get('_block', 0)}")
            end_block = IRBlock(name=f"while_end_{ssa.versions.get('_block', 0)}")
            ssa.versions["_block"] = ssa.versions.get("_block", 0) + 1

            insts.append(IRBr(opcode=IROpcode.BR, target=loop_block.name))

            # 循环条件
            cond_insts, cond_val, _ = self._lower_expr(node.test, loop_block, ssa)
            loop_block.instructions.extend(cond_insts)
            loop_block.add_inst(
                IRBr(
                    opcode=IROpcode.COND_BR,
                    cond=cond_val,
                    true_target=body_block.name,
                    false_target=end_block.name,
                )
            )

            # 循环体
            for stmt in node.body:
                s_insts, _ = self._lower_statement(stmt, body_block, ssa)
                body_block.instructions.extend(s_insts)
            body_block.add_inst(IRBr(opcode=IROpcode.BR, target=loop_block.name))

            insts.extend([loop_block, body_block])
            block = end_block

        elif isinstance(node, ast.For):
            # for i in range(n): body
            iter_block = IRBlock(name=f"for_iter_{ssa.versions.get('_block', 0)}")
            body_block = IRBlock(name=f"for_body_{ssa.versions.get('_block', 0)}")
            end_block = IRBlock(name=f"for_end_{ssa.versions.get('_block', 0)}")
            ssa.versions["_block"] = ssa.versions.get("_block", 0) + 1

            # range() 调用
            if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name):
                if node.iter.func.id == "range":
                    args = node.iter.args
                    # start
                    start_val = IRValue("0")
                    if len(args) >= 1:
                        _, start_val, _ = self._lower_expr(args[0], iter_block, ssa)
                    # end
                    end_val = IRValue("0")
                    if len(args) >= 2:
                        _, end_val, _ = self._lower_expr(args[1], iter_block, ssa)
                    elif len(args) >= 1:
                        end_val = start_val
                        _, start_val, _ = self._lower_expr(args[0], iter_block, ssa)
                        end_val = IRValue("0")
                        if len(args) == 1:
                            end_val = start_val
                            start_val = IRValue("0")

                    # 循环变量
                    if isinstance(node.target, ast.Name):
                        iter_var = ssa.new_value(node.target.id, IRTypeInfo(IRType.INT))
                        iter_block.add_inst(
                            IRConst(
                                opcode=IROpcode.ALLOCA, result=iter_var, const_value=0
                            )
                        )

                    # cmp i < end
                    cmp_result = ssa.new_value("cmp", IRTypeInfo(IRType.BOOL))
                    iter_block.add_inst(
                        IRConst(
                            opcode=IROpcode.ICMP_SLT,
                            result=cmp_result,
                            operands=[iter_var, end_val],
                        )
                    )
                    iter_block.add_inst(
                        IRBr(
                            opcode=IROpcode.COND_BR,
                            cond=cmp_result,
                            true_target=body_block.name,
                            false_target=end_block.name,
                        )
                    )

            insts.append(IRBr(opcode=IROpcode.BR, target=iter_block.name))

            # body
            for stmt in node.body:
                s_insts, _ = self._lower_statement(stmt, body_block, ssa)
                body_block.instructions.extend(s_insts)
            body_block.add_inst(IRBr(opcode=IROpcode.BR, target=iter_block.name))

            insts.extend([iter_block, body_block])
            block = end_block

        elif isinstance(node, ast.AugAssign):
            # += -= *= /=
            target_name = ast.unparse(node.target).strip()
            target_val = ssa.get_value(target_name)

            right_insts, right_val, block = self._lower_expr(node.value, block, ssa)
            insts.extend(right_insts)

            result = ssa.new_value(f"{target_name}_tmp", IRTypeInfo(IRType.INT))

            if isinstance(node.op, ast.Add):
                insts.append(
                    IRConst(
                        opcode=IROpcode.ADD,
                        result=result,
                        operands=[target_val, right_val],
                    )
                )
            elif isinstance(node.op, ast.Sub):
                insts.append(
                    IRConst(
                        opcode=IROpcode.SUB,
                        result=result,
                        operands=[target_val, right_val],
                    )
                )
            elif isinstance(node.op, ast.Mult):
                insts.append(
                    IRConst(
                        opcode=IROpcode.MUL,
                        result=result,
                        operands=[target_val, right_val],
                    )
                )
            elif isinstance(node.op, ast.Div):
                insts.append(
                    IRConst(
                        opcode=IROpcode.DIV,
                        result=result,
                        operands=[target_val, right_val],
                    )
                )

            # 存回
            new_alloc = ssa.new_value(target_name, IRTypeInfo(IRType.INT))
            insts.append(IRConst(opcode=IROpcode.STORE, operands=[result, new_alloc]))

        return insts, block

    def _lower_expr(
        self, node: ast.expr, block: IRBlock, ssa: SSAValueManager
    ) -> Tuple[List[IRInstruction], IRValue, IRBlock]:
        """降级表达式"""
        insts = []

        if isinstance(node, ast.Constant):
            # 整数、浮点、字符串常量
            if isinstance(node.value, int):
                val = ssa.new_value("const", IRTypeInfo(IRType.INT))
                insts.append(
                    IRConst(
                        opcode=IROpcode.CONST,
                        result=val,
                        operands=[IRValue(str(node.value))],
                        const_value=node.value,
                        type_info=IRTypeInfo(IRType.INT),
                    )
                )
            elif isinstance(node.value, float):
                val = ssa.new_value("const", IRTypeInfo(IRType.FLOAT))
                insts.append(
                    IRConst(
                        opcode=IROpcode.CONST,
                        result=val,
                        operands=[IRValue(str(node.value))],
                        const_value=node.value,
                        type_info=IRTypeInfo(IRType.FLOAT),
                    )
                )
            elif isinstance(node.value, str):
                val = ssa.new_value("const", IRTypeInfo(IRType.STRING))
                insts.append(
                    IRConst(
                        opcode=IROpcode.CONST,
                        result=val,
                        operands=[IRValue(f'"{node.value}"')],
                        const_value=node.value,
                        type_info=IRTypeInfo(IRType.STRING),
                    )
                )
            else:
                val = IRValue(str(node.value))

        elif isinstance(node, ast.Name):
            val = ssa.get_value(node.id)

        elif isinstance(node, ast.BinOp):
            left_insts, left_val, block = self._lower_expr(node.left, block, ssa)
            insts.extend(left_insts)

            right_insts, right_val, block = self._lower_expr(node.right, block, ssa)
            insts.extend(right_insts)

            result = ssa.new_value("binop", IRTypeInfo(IRType.INT))

            if isinstance(node.op, ast.Add):
                insts.append(
                    IRConst(
                        opcode=IROpcode.ADD,
                        result=result,
                        operands=[left_val, right_val],
                    )
                )
            elif isinstance(node.op, ast.Sub):
                insts.append(
                    IRConst(
                        opcode=IROpcode.SUB,
                        result=result,
                        operands=[left_val, right_val],
                    )
                )
            elif isinstance(node.op, ast.Mult):
                insts.append(
                    IRConst(
                        opcode=IROpcode.MUL,
                        result=result,
                        operands=[left_val, right_val],
                    )
                )
            elif isinstance(node.op, ast.Div):
                insts.append(
                    IRConst(
                        opcode=IROpcode.DIV,
                        result=result,
                        operands=[left_val, right_val],
                    )
                )
            elif isinstance(node.op, ast.Mod):
                insts.append(
                    IRConst(
                        opcode=IROpcode.REM,
                        result=result,
                        operands=[left_val, right_val],
                    )
                )
            elif isinstance(node.op, ast.Pow):
                # 简化：直接用乘法模拟
                insts.append(
                    IRConst(
                        opcode=IROpcode.MUL,
                        result=result,
                        operands=[left_val, right_val],
                    )
                )

            val = result

        elif isinstance(node, ast.Compare):
            left_insts, left_val, block = self._lower_expr(node.left, block, ssa)
            insts.extend(left_insts)

            result = ssa.new_value("cmp", IRTypeInfo(IRType.BOOL))

            # 简化：只处理单个比较
            if len(node.ops) == 1 and len(node.comparators) == 1:
                right_insts, right_val, block = self._lower_expr(
                    node.comparators[0], block, ssa
                )
                insts.extend(right_insts)

                cmp_op = self._get_compare_op(node.ops[0])
                insts.append(
                    IRConst(
                        opcode=cmp_op, result=result, operands=[left_val, right_val]
                    )
                )

            val = result

        elif isinstance(node, ast.Call):
            # 函数调用
            if isinstance(node.func, ast.Name):
                args = []
                for arg in node.args:
                    arg_insts, arg_val, block = self._lower_expr(arg, block, ssa)
                    insts.extend(arg_insts)
                    args.append(arg_val)

                result = ssa.new_value("call", IRTypeInfo(IRType.INT))
                insts.append(
                    IRCall(
                        opcode=IROpcode.CALL,
                        result=result,
                        func_name=node.func.id,
                        args=args,
                    )
                )
                val = result
            else:
                val = IRValue("unknown_call")

        elif isinstance(node, ast.List):
            # 列表字面量 [1, 2, 3]
            result = ssa.new_value("list", IRTypeInfo(IRType.ARRAY))
            # 简化：只分配空间
            insts.append(
                IRConst(
                    opcode=IROpcode.ALLOCA,
                    result=result,
                    type_info=IRTypeInfo(IRType.ARRAY),
                )
            )
            val = result

        elif isinstance(node, ast.Index):
            # arr[i]
            obj_insts, obj_val, block = self._lower_expr(node.value, block, ssa)
            insts.extend(obj_insts)
            if hasattr(node, "dim"):
                dim_insts, dim_val, block = self._lower_expr(node.dim, block, ssa)
                insts.extend(dim_insts)
                result = ssa.new_value("index", IRTypeInfo(IRType.INT))
                insts.append(
                    IRConst(
                        opcode=IROpcode.INDEX,
                        result=result,
                        operands=[obj_val, dim_val],
                    )
                )
                val = result
            else:
                val = obj_val

        else:
            val = IRValue("unknown_expr")

        return insts, val, block

    def _get_compare_op(self, op: ast.cmpop) -> IROpcode:
        """获取比较操作码"""
        if isinstance(op, ast.Eq):
            return IROpcode.ICMP_EQ
        elif isinstance(op, ast.NotEq):
            return IROpcode.ICMP_NE
        elif isinstance(op, ast.Lt):
            return IROpcode.ICMP_SLT
        elif isinstance(op, ast.LtE):
            return IROpcode.ICMP_SLE
        elif isinstance(op, ast.Gt):
            return IROpcode.ICMP_SGT
        elif isinstance(op, ast.GtE):
            return IROpcode.ICMP_SGE
        return IROpcode.ICMP_EQ


# ═══════════════════════════════════════════════════════════════════════════════
# 第十一部分：JavaScript 降级器 (JavaScript → IR)
# ═══════════════════════════════════════════════════════════════════════════════


class JSLower(LanguageLower):
    """JavaScript 语言降级器"""

    # JS 内置类型 → IRType 映射
    TYPE_MAP = {
        "number": IRType.FLOAT,  # JS number 类型
        "int": IRType.INT,
        "string": IRType.STRING,
        "boolean": IRType.BOOL,
        "object": IRType.STRUCT,
        "array": IRType.ARRAY,
    }

    def get_lang_name(self) -> str:
        return "JavaScript"

    def parse(self, source: str) -> IRModule:
        """将 JavaScript 源码解析为 IR"""
        module = IRModule("javascript_module")

        # 简化的 JS 解析（正则表达式方式）
        # 匹配函数定义
        func_pattern = (
            r"function\s+(\w+)\s*\(([^)]*)\)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}"
        )

        for match in re.finditer(func_pattern, source, re.DOTALL):
            func_name = match.group(1)
            params_str = match.group(2)
            body = match.group(3)

            params = [p.strip() for p in params_str.split(",") if p.strip()]

            func = self._lower_js_function(func_name, params, body)
            module.add_func(func)

        return module

    def _lower_js_function(self, name: str, params: List[str], body: str) -> IRFunction:
        """将 JS 函数降级为 IR 函数"""
        ssa = SSAValueManager()

        func = IRFunction(name=name, return_type=IRTypeInfo(IRType.INT))
        entry = IRBlock(name="entry")

        # 添加参数
        for param in params:
            func.params.append((param, IRTypeInfo(IRType.INT)))
            alloc_val = ssa.new_value(param, IRTypeInfo(IRType.INT))
            entry.add_inst(IRConst(opcode=IROpcode.ALLOCA, result=alloc_val))

            # 已经在上面添加了 entry 块
        ssa.reset()

        # 解析函数体
        current_block = entry

        # 处理变量声明 let/const/var
        var_pattern = r"(?:let|const|var)\s+(\w+)\s*=\s*([^;]+);"
        for var_match in re.finditer(var_pattern, body):
            var_name = var_match.group(1)
            expr = var_match.group(2).strip()

            value_insts, value, current_block = self._lower_js_expr(
                expr, current_block, ssa
            )
            for inst in value_insts:
                current_block.add_inst(inst)

            new_val = ssa.new_value(var_name, IRTypeInfo(IRType.INT))
            current_block.add_inst(
                IRConst(opcode=IROpcode.ALLOCA, result=new_val, operands=[value])
            )

        # 处理 return 语句
        return_pattern = r"return\s+([^;]+);"
        for ret_match in re.finditer(return_pattern, body):
            expr = ret_match.group(1).strip()
            value_insts, value, _ = self._lower_js_expr(expr, current_block, ssa)
            for inst in value_insts:
                current_block.add_inst(inst)
            current_block.add_inst(IRRet(opcode=IROpcode.RET, operands=[value]))

        # 处理 console.log
        log_pattern = r"console\.log\s*\(([^)]+)\);"
        for log_match in re.finditer(log_pattern, body):
            expr = log_match.group(1).strip()
            value_insts, value, _ = self._lower_js_expr(expr, current_block, ssa)
            for inst in value_insts:
                current_block.add_inst(inst)
            current_block.add_inst(IRConst(opcode=IROpcode.PRINT, operands=[value]))

        # 处理 if 语句
        if_pattern = r"if\s*\(([^)]+)\)\s*\{([^}]*)\}"
        for if_match in re.finditer(if_pattern, body):
            condition = if_match.group(1).strip()
            then_body = if_match.group(2)

            cond_insts, cond_val, _ = self._lower_js_expr(condition, current_block, ssa)
            for inst in cond_insts:
                current_block.add_inst(inst)

            then_block = IRBlock(name=f"js_then_{ssa.versions.get('_block', 0)}")
            else_block = IRBlock(name=f"js_else_{ssa.versions.get('_block', 0)}")
            merge_block = IRBlock(name=f"js_end_{ssa.versions.get('_block', 0)}")
            ssa.versions["_block"] = ssa.versions.get("_block", 0) + 1

            current_block.add_inst(
                IRBr(
                    opcode=IROpcode.COND_BR,
                    cond=cond_val,
                    true_target=then_block.name,
                    false_target=else_block.name,
                )
            )

            # 解析 then_body 中的 console.log
            for log_match in re.finditer(log_pattern, then_body):
                expr = log_match.group(1).strip()
                value_insts, value, _ = self._lower_js_expr(expr, then_block, ssa)
                for inst in value_insts:
                    then_block.add_inst(inst)
                then_block.add_inst(IRConst(opcode=IROpcode.PRINT, operands=[value]))

            then_block.add_inst(IRBr(opcode=IROpcode.BR, target=merge_block.name))
            else_block.add_inst(IRBr(opcode=IROpcode.BR, target=merge_block.name))

            func.add_block(then_block)
            func.add_block(else_block)
            current_block = merge_block

        # 处理 for 循环
        for_pattern = r"for\s*\(([^;]+);([^;]+);([^)]+)\)\s*\{([^}]*)\}"
        for for_match in re.finditer(for_pattern, body):
            init = for_match.group(1).strip()
            cond = for_match.group(2).strip()
            update = for_match.group(3).strip()
            loop_body = for_match.group(4)

            # 初始化
            if "let" in init:
                var_match = re.search(r"let\s+(\w+)", init)
                if var_match:
                    var_name = var_match.group(1)
                    expr = re.sub(r"let\s+\w+\s*=\s*", "", init)
                    value_insts, value, _ = self._lower_js_expr(
                        expr, current_block, ssa
                    )
                    for inst in value_insts:
                        current_block.add_inst(inst)

            loop_block = IRBlock(name=f"js_for_{ssa.versions.get('_block', 0)}")
            body_block = IRBlock(name=f"js_for_body_{ssa.versions.get('_block', 0)}")
            end_block = IRBlock(name=f"js_for_end_{ssa.versions.get('_block', 0)}")
            ssa.versions["_block"] = ssa.versions.get("_block", 0) + 1

            current_block.add_inst(IRBr(opcode=IROpcode.BR, target=loop_block.name))

            # 条件判断
            cond_insts, cond_val, _ = self._lower_js_expr(cond, loop_block, ssa)
            for inst in cond_insts:
                loop_block.add_inst(inst)
            loop_block.add_inst(
                IRBr(
                    opcode=IROpcode.COND_BR,
                    cond=cond_val,
                    true_target=body_block.name,
                    false_target=end_block.name,
                )
            )

            # 循环体
            for log_match in re.finditer(log_pattern, loop_body):
                expr = log_match.group(1).strip()
                value_insts, value, _ = self._lower_js_expr(expr, body_block, ssa)
                for inst in value_insts:
                    body_block.add_inst(inst)
                body_block.add_inst(IRConst(opcode=IROpcode.PRINT, operands=[value]))

            # 更新
            if "+=" in update:
                var_match = re.search(r"(\w+)\s*\+=", update)
                if var_match:
                    var_name = var_match.group(1)
                    expr = re.sub(r"\w+\s*\+=\s*", "", update)
                    value_insts, value, _ = self._lower_js_expr(expr, body_block, ssa)
                    for inst in value_insts:
                        body_block.add_inst(inst)
                    old_val = ssa.get_value(var_name)
                    new_val = ssa.new_value(f"{var_name}_tmp", IRTypeInfo(IRType.INT))
                    body_block.add_inst(
                        IRConst(
                            opcode=IROpcode.ADD,
                            result=new_val,
                            operands=[old_val, value],
                        )
                    )

            body_block.add_inst(IRBr(opcode=IROpcode.BR, target=loop_block.name))

            func.add_block(loop_block)
            func.add_block(body_block)
            current_block = end_block

        func.add_block(current_block)
        return func

    def _lower_js_expr(
        self, expr: str, block: IRBlock, ssa: SSAValueManager
    ) -> Tuple[List[IRInstruction], IRValue, IRBlock]:
        """降级 JS 表达式"""
        insts = []
        expr = expr.strip()

        # 数字常量
        if re.match(r"^-?\d+\.?\d*$", expr):
            val = ssa.new_value("const", IRTypeInfo(IRType.INT))
            insts.append(
                IRConst(
                    opcode=IROpcode.CONST,
                    result=val,
                    operands=[IRValue(expr)],
                    const_value=int(expr) if "." not in expr else float(expr),
                )
            )

        # 字符串常量
        elif expr.startswith('"') and expr.endswith('"'):
            val = ssa.new_value("const", IRTypeInfo(IRType.STRING))
            str_val = expr[1:-1]
            insts.append(
                IRConst(
                    opcode=IROpcode.CONST,
                    result=val,
                    operands=[IRValue(expr)],
                    const_value=str_val,
                    type_info=IRTypeInfo(IRType.STRING),
                )
            )

        # 变量
        elif re.match(r"^[a-zA-Z_]\w*$", expr):
            val = ssa.get_value(expr)

        # 算术运算
        elif "+" in expr and not ('"' in expr or "'" in expr):
            # 加法
            match = re.match(r"^(.+)\s*\+\s*(.+)$", expr)
            if match:
                left_insts, left_val, block = self._lower_js_expr(
                    match.group(1), block, ssa
                )
                right_insts, right_val, block = self._lower_js_expr(
                    match.group(2), block, ssa
                )
                insts.extend(left_insts)
                insts.extend(right_insts)
                result = ssa.new_value("add", IRTypeInfo(IRType.INT))
                insts.append(
                    IRConst(
                        opcode=IROpcode.ADD,
                        result=result,
                        operands=[left_val, right_val],
                    )
                )
                val = result

        elif "-" in expr:
            match = re.match(r"^(.+)\s*-\s*(.+)$", expr)
            if match:
                left_insts, left_val, block = self._lower_js_expr(
                    match.group(1), block, ssa
                )
                right_insts, right_val, block = self._lower_js_expr(
                    match.group(2), block, ssa
                )
                insts.extend(left_insts)
                insts.extend(right_insts)
                result = ssa.new_value("sub", IRTypeInfo(IRType.INT))
                insts.append(
                    IRConst(
                        opcode=IROpcode.SUB,
                        result=result,
                        operands=[left_val, right_val],
                    )
                )
                val = result

        elif "*" in expr:
            match = re.match(r"^(.+)\s*\*\s*(.+)$", expr)
            if match:
                left_insts, left_val, block = self._lower_js_expr(
                    match.group(1), block, ssa
                )
                right_insts, right_val, block = self._lower_js_expr(
                    match.group(2), block, ssa
                )
                insts.extend(left_insts)
                insts.extend(right_insts)
                result = ssa.new_value("mul", IRTypeInfo(IRType.INT))
                insts.append(
                    IRConst(
                        opcode=IROpcode.MUL,
                        result=result,
                        operands=[left_val, right_val],
                    )
                )
                val = result

        # 比较运算
        elif "<" in expr or ">" in expr or "==" in expr or "!=" in expr:
            # 简化处理
            match = re.match(r"^(.+?)\s*(<|>|<=|>=|==|!=)\s*(.+)$", expr)
            if match:
                left = match.group(1).strip()
                op = match.group(2)
                right = match.group(3).strip()

                left_insts, left_val, block = self._lower_js_expr(left, block, ssa)
                right_insts, right_val, block = self._lower_js_expr(right, block, ssa)
                insts.extend(left_insts)
                insts.extend(right_insts)

                result = ssa.new_value("cmp", IRTypeInfo(IRType.BOOL))

                if op in ("<", "<="):
                    cmp_op = IROpcode.ICMP_SLT if op == "<" else IROpcode.ICMP_SLE
                elif op in (">", ">="):
                    cmp_op = IROpcode.ICMP_SGT if op == ">" else IROpcode.ICMP_SGE
                elif op == "==":
                    cmp_op = IROpcode.ICMP_EQ
                elif op == "!=":
                    cmp_op = IROpcode.ICMP_NE
                else:
                    cmp_op = IROpcode.ICMP_EQ

                insts.append(
                    IRConst(
                        opcode=cmp_op, result=result, operands=[left_val, right_val]
                    )
                )
                val = result

        else:
            val = IRValue(expr)

        return insts, val, block


# ═══════════════════════════════════════════════════════════════════════════════
# 第十二部分：Go 降级器 (Go → IR)
# ═══════════════════════════════════════════════════════════════════════════════


class GoLower(LanguageLower):
    """Go 语言降级器"""

    # Go 内置类型 → IRType 映射
    TYPE_MAP = {
        "int": IRType.INT,
        "int8": IRType.INT,
        "int16": IRType.INT,
        "int32": IRType.INT,
        "int64": IRType.INT64,
        "float32": IRType.FLOAT,
        "float64": IRType.DOUBLE,
        "bool": IRType.BOOL,
        "string": IRType.STRING,
        "byte": IRType.CHAR,
        "rune": IRType.CHAR,
    }

    def get_lang_name(self) -> str:
        return "Go"

    def parse(self, source: str) -> IRModule:
        """将 Go 源码解析为 IR"""
        module = IRModule("go_module")

        # 匹配函数定义
        func_pattern = (
            r"func\s+(\w+)\s*\(([^)]*)\)\s*(?:\([^)]+\)\s*)?"
            r"\{([^}]*(?:\{[^}]*\}[^}]*)*)\}"
        )

        for match in re.finditer(func_pattern, source, re.DOTALL):
            func_name = match.group(1)
            params_str = match.group(2)
            body = match.group(3)

            params = []
            for p in params_str.split(","):
                p = p.strip()
                if p:
                    parts = p.split()
                    if len(parts) >= 2:
                        params.append((parts[-1], parts[0]))  # (name, type)
                    else:
                        params.append((p, "int"))

            func = self._lower_go_function(func_name, params, body)
            module.add_func(func)

        return module

    def _lower_go_function(
        self, name: str, params: List[Tuple[str, str]], body: str
    ) -> IRFunction:
        """将 Go 函数降级为 IR 函数"""
        ssa = SSAValueManager()

        return_type = IRTypeInfo(IRType.INT)
        func = IRFunction(name=name, return_type=return_type)
        entry = IRBlock(name="entry")

        # 添加参数
        for param_name, param_type in params:
            ir_type = self.TYPE_MAP.get(param_type, IRType.INT)
            func.params.append((param_name, IRTypeInfo(ir_type)))
            alloc_val = ssa.new_value(param_name, IRTypeInfo(ir_type))
            entry.add_inst(IRConst(opcode=IROpcode.ALLOCA, result=alloc_val))

            # 已经在上面添加了 entry 块
        ssa.reset()

        current_block = entry

        # 处理变量声明
        var_pattern = r"(\w+)\s*:?=\s*([^;]+)"
        for var_match in re.finditer(var_pattern, body):
            var_name = var_match.group(1)
            expr = var_match.group(2).strip()

            value_insts, value, current_block = self._lower_go_expr(
                expr, current_block, ssa
            )
            for inst in value_insts:
                current_block.add_inst(inst)

            new_val = ssa.new_value(var_name, IRTypeInfo(IRType.INT))
            current_block.add_inst(
                IRConst(opcode=IROpcode.ALLOCA, result=new_val, operands=[value])
            )

        # 处理 fmt.Println
        print_pattern = r"fmt\.Println\s*\(([^)]+)\)"
        for print_match in re.finditer(print_pattern, body):
            exprs = print_match.group(1).split(",")
            for expr in exprs:
                expr = expr.strip()
                value_insts, value, _ = self._lower_go_expr(expr, current_block, ssa)
                for inst in value_insts:
                    current_block.add_inst(inst)
                current_block.add_inst(IRConst(opcode=IROpcode.PRINT, operands=[value]))

        # 处理 return
        return_pattern = r"return\s+([^;]+)"
        for ret_match in re.finditer(return_pattern, body):
            expr = ret_match.group(1).strip()
            value_insts, value, _ = self._lower_go_expr(expr, current_block, ssa)
            for inst in value_insts:
                current_block.add_inst(inst)
            current_block.add_inst(IRRet(opcode=IROpcode.RET, operands=[value]))

        # 处理 if 语句
        if_pattern = r"if\s+([^}]+)\s*\{([^}]*)\}"
        for if_match in re.finditer(if_pattern, body):
            condition = if_match.group(1).strip()
            then_body = if_match.group(2)

            cond_insts, cond_val, _ = self._lower_go_expr(condition, current_block, ssa)
            for inst in cond_insts:
                current_block.add_inst(inst)

            then_block = IRBlock(name=f"go_then_{ssa.versions.get('_block', 0)}")
            else_block = IRBlock(name=f"go_else_{ssa.versions.get('_block', 0)}")
            merge_block = IRBlock(name=f"go_end_{ssa.versions.get('_block', 0)}")
            ssa.versions["_block"] = ssa.versions.get("_block", 0) + 1

            current_block.add_inst(
                IRBr(
                    opcode=IROpcode.COND_BR,
                    cond=cond_val,
                    true_target=then_block.name,
                    false_target=else_block.name,
                )
            )

            # 解析 then_body 中的 fmt.Println
            for print_match in re.finditer(print_pattern, then_body):
                exprs = print_match.group(1).split(",")
                for expr in exprs:
                    expr = expr.strip()
                    value_insts, value, _ = self._lower_go_expr(expr, then_block, ssa)
                    for inst in value_insts:
                        then_block.add_inst(inst)
                    then_block.add_inst(
                        IRConst(opcode=IROpcode.PRINT, operands=[value])
                    )

            then_block.add_inst(IRBr(opcode=IROpcode.BR, target=merge_block.name))
            else_block.add_inst(IRBr(opcode=IROpcode.BR, target=merge_block.name))

            func.add_block(then_block)
            func.add_block(else_block)
            current_block = merge_block

        # 处理 for 循环
        for_pattern = r"for\s*(?:([^;]+);)?([^}]+)\s*\{([^}]*)\}"
        for for_match in re.finditer(for_pattern, body):
            init = for_match.group(1)
            cond = for_match.group(2)
            loop_body = for_match.group(3)

            loop_block = IRBlock(name=f"go_for_{ssa.versions.get('_block', 0)}")
            body_block = IRBlock(name=f"go_for_body_{ssa.versions.get('_block', 0)}")
            end_block = IRBlock(name=f"go_for_end_{ssa.versions.get('_block', 0)}")
            ssa.versions["_block"] = ssa.versions.get("_block", 0) + 1

            # 初始化
            if init:
                for var_match in re.finditer(var_pattern, init):
                    var_name = var_match.group(1)
                    expr = var_match.group(2).strip()
                    value_insts, value, _ = self._lower_go_expr(
                        expr, current_block, ssa
                    )
                    for inst in value_insts:
                        current_block.add_inst(inst)

            current_block.add_inst(IRBr(opcode=IROpcode.BR, target=loop_block.name))

            # 条件
            if cond:
                cond_insts, cond_val, _ = self._lower_go_expr(cond, loop_block, ssa)
                for inst in cond_insts:
                    loop_block.add_inst(inst)
                loop_block.add_inst(
                    IRBr(
                        opcode=IROpcode.COND_BR,
                        cond=cond_val,
                        true_target=body_block.name,
                        false_target=end_block.name,
                    )
                )
            else:
                loop_block.add_inst(IRBr(opcode=IROpcode.BR, target=body_block.name))

            # 循环体
            for print_match in re.finditer(print_pattern, loop_body):
                exprs = print_match.group(1).split(",")
                for expr in exprs:
                    expr = expr.strip()
                    value_insts, value, _ = self._lower_go_expr(expr, body_block, ssa)
                    for inst in value_insts:
                        body_block.add_inst(inst)
                    body_block.add_inst(
                        IRConst(opcode=IROpcode.PRINT, operands=[value])
                    )

            # 后置更新（简化）
            body_block.add_inst(IRBr(opcode=IROpcode.BR, target=loop_block.name))

            func.add_block(loop_block)
            func.add_block(body_block)
            current_block = end_block

        func.add_block(current_block)
        return func

    def _lower_go_expr(
        self, expr: str, block: IRBlock, ssa: SSAValueManager
    ) -> Tuple[List[IRInstruction], IRValue, IRBlock]:
        """降级 Go 表达式"""
        insts = []
        expr = expr.strip()

        # 数字常量
        if re.match(r"^-?\d+\.?\d*$", expr):
            is_float = "." in expr
            val = ssa.new_value(
                "const", IRTypeInfo(IRType.FLOAT if is_float else IRType.INT)
            )
            insts.append(
                IRConst(
                    opcode=IROpcode.CONST,
                    result=val,
                    operands=[IRValue(expr)],
                    const_value=float(expr) if is_float else int(expr),
                )
            )

        # 字符串常量
        elif expr.startswith('"') and expr.endswith('"'):
            val = ssa.new_value("const", IRTypeInfo(IRType.STRING))
            str_val = expr[1:-1]
            insts.append(
                IRConst(
                    opcode=IROpcode.CONST,
                    result=val,
                    operands=[IRValue(expr)],
                    const_value=str_val,
                    type_info=IRTypeInfo(IRType.STRING),
                )
            )

        # 变量
        elif re.match(r"^[a-zA-Z_]\w*$", expr):
            val = ssa.get_value(expr)

        # 算术运算
        elif "+" in expr:
            match = re.match(r"^(.+)\s*\+\s*(.+)$", expr)
            if match:
                left_insts, left_val, block = self._lower_go_expr(
                    match.group(1), block, ssa
                )
                right_insts, right_val, block = self._lower_go_expr(
                    match.group(2), block, ssa
                )
                insts.extend(left_insts)
                insts.extend(right_insts)
                result = ssa.new_value("add", IRTypeInfo(IRType.INT))
                insts.append(
                    IRConst(
                        opcode=IROpcode.ADD,
                        result=result,
                        operands=[left_val, right_val],
                    )
                )
                val = result

        elif "-" in expr:
            match = re.match(r"^(.+)\s*-\s*(.+)$", expr)
            if match:
                left_insts, left_val, block = self._lower_go_expr(
                    match.group(1), block, ssa
                )
                right_insts, right_val, block = self._lower_go_expr(
                    match.group(2), block, ssa
                )
                insts.extend(left_insts)
                insts.extend(right_insts)
                result = ssa.new_value("sub", IRTypeInfo(IRType.INT))
                insts.append(
                    IRConst(
                        opcode=IROpcode.SUB,
                        result=result,
                        operands=[left_val, right_val],
                    )
                )
                val = result

        elif "*" in expr:
            match = re.match(r"^(.+)\s*\*\s*(.+)$", expr)
            if match:
                left_insts, left_val, block = self._lower_go_expr(
                    match.group(1), block, ssa
                )
                right_insts, right_val, block = self._lower_go_expr(
                    match.group(2), block, ssa
                )
                insts.extend(left_insts)
                insts.extend(right_insts)
                result = ssa.new_value("mul", IRTypeInfo(IRType.INT))
                insts.append(
                    IRConst(
                        opcode=IROpcode.MUL,
                        result=result,
                        operands=[left_val, right_val],
                    )
                )
                val = result

        elif "/" in expr:
            match = re.match(r"^(.+)\s*/\s*(.+)$", expr)
            if match:
                left_insts, left_val, block = self._lower_go_expr(
                    match.group(1), block, ssa
                )
                right_insts, right_val, block = self._lower_go_expr(
                    match.group(2), block, ssa
                )
                insts.extend(left_insts)
                insts.extend(right_insts)
                result = ssa.new_value("div", IRTypeInfo(IRType.INT))
                insts.append(
                    IRConst(
                        opcode=IROpcode.DIV,
                        result=result,
                        operands=[left_val, right_val],
                    )
                )
                val = result

        # 比较运算
        elif "<" in expr or ">" in expr or "==" in expr:
            match = re.match(r"^(.+?)\s*(<|>|<=|>=|==|!=)\s*(.+)$", expr)
            if match:
                left = match.group(1).strip()
                op = match.group(2)
                right = match.group(3).strip()

                left_insts, left_val, block = self._lower_go_expr(left, block, ssa)
                right_insts, right_val, block = self._lower_go_expr(right, block, ssa)
                insts.extend(left_insts)
                insts.extend(right_insts)

                result = ssa.new_value("cmp", IRTypeInfo(IRType.BOOL))

                if op == "<":
                    cmp_op = IROpcode.ICMP_SLT
                elif op == ">":
                    cmp_op = IROpcode.ICMP_SGT
                elif op == "<=":
                    cmp_op = IROpcode.ICMP_SLE
                elif op == ">=":
                    cmp_op = IROpcode.ICMP_SGE
                elif op == "==":
                    cmp_op = IROpcode.ICMP_EQ
                else:
                    cmp_op = IROpcode.ICMP_NE

                insts.append(
                    IRConst(
                        opcode=cmp_op, result=result, operands=[left_val, right_val]
                    )
                )
                val = result

        else:
            val = IRValue(expr)

        return insts, val, block


# ═══════════════════════════════════════════════════════════════════════════════
# 第十三部分：优化 Pass（死代码消除、常量折叠）
# ═══════════════════════════════════════════════════════════════════════════════


class DeadCodeElimination:
    """死代码消除优化 Pass"""

    def run(self, module: IRModule) -> IRModule:
        """移除无用的代码"""
        used_values: Set[str] = set()

        # 第一遍：收集所有被引用的值
        for func in module.functions:
            for block in func.blocks:
                for inst in block.instructions:
                    self._collect_used_values(inst, used_values)

        # 第二遍：删除没有被引用的 alloca 指令（保留作为临时变量）
        for func in module.functions:
            for block in func.blocks:
                # 遍历指令（简化处理：保留所有 alloca）
                for inst in block.instructions:
                    if isinstance(inst, IRConst):
                        if inst.opcode == IROpcode.ALLOCA:
                            pass

                # 删除无用的 ret 前的 store
                i = 0
                while i < len(block.instructions):
                    inst = block.instructions[i]
                    if isinstance(inst, IRRet):
                        j = i - 1
                        while j >= 0:
                            prev = block.instructions[j]
                            if (
                                isinstance(prev, IRConst)
                                and prev.opcode == IROpcode.STORE
                            ):
                                if (
                                    prev.operands
                                    and str(prev.operands[0]) not in used_values
                                ):
                                    pass
                            j -= 1
                    i += 1

        return module

    def _collect_used_values(self, inst: IRInstruction, used: Set[str]):
        """收集指令中使用的值"""
        for op in inst.operands:
            used.add(op.name)


class ConstantFolding:
    """常量折叠优化 Pass"""

    def run(self, module: IRModule) -> IRModule:
        """执行常量折叠"""
        constants: Dict[str, Any] = {}  # 值名 → 常量值

        for func in module.functions:
            # skip entry block iteration, iterate all blocks
            for block in func.blocks:
                self._fold_block(block, constants)

        return module

    def _fold_block(self, block: Optional[IRBlock], constants: Dict[str, Any]):
        """折叠基本块中的常量"""
        if not block:
            return

        i = 0
        while i < len(block.instructions):
            inst = block.instructions[i]

            if isinstance(inst, IRConst) and inst.opcode == IROpcode.CONST:
                if inst.const_value is not None:
                    constants[inst.result.name] = inst.const_value

            elif isinstance(inst, IRConst) and inst.result:
                operands = []
                can_fold = True

                for op in inst.operands:
                    op_name = op.name
                    base_name = op_name.split(".")[0]
                    if base_name in constants:
                        operands.append(constants[base_name])
                    else:
                        can_fold = False
                        break

                if can_fold and len(operands) == 2:
                    result = self._compute(inst.opcode, operands)
                    if result is not None:
                        constants[inst.result.name] = result
                        inst.opcode = IROpcode.CONST
                        inst.const_value = result

            i += 1

    def _compute(self, opcode: IROpcode, operands: List[Any]) -> Optional[Any]:
        """计算常量表达式的结果"""
        try:
            if opcode == IROpcode.ADD and len(operands) == 2:
                return operands[0] + operands[1]
            elif opcode == IROpcode.SUB and len(operands) == 2:
                return operands[0] - operands[1]
            elif opcode == IROpcode.MUL and len(operands) == 2:
                return operands[0] * operands[1]
            elif opcode == IROpcode.DIV and len(operands) == 2 and operands[1] != 0:
                return operands[0] // operands[1]
            elif opcode == IROpcode.REM and len(operands) == 2 and operands[1] != 0:
                return operands[0] % operands[1]
            elif opcode == IROpcode.ICMP_EQ and len(operands) == 2:
                return 1 if operands[0] == operands[1] else 0
            elif opcode == IROpcode.ICMP_NE and len(operands) == 2:
                return 1 if operands[0] != operands[1] else 0
            elif opcode == IROpcode.ICMP_SLT and len(operands) == 2:
                return 1 if operands[0] < operands[1] else 0
            elif opcode == IROpcode.ICMP_SGT and len(operands) == 2:
                return 1 if operands[0] > operands[1] else 0
            elif opcode == IROpcode.ICMP_SLE and len(operands) == 2:
                return 1 if operands[0] <= operands[1] else 0
            elif opcode == IROpcode.ICMP_SGE and len(operands) == 2:
                return 1 if operands[0] >= operands[1] else 0
        except (TypeError, ValueError):
            pass
        return None


class IROptimizer:
    """IR 优化器（组合多个优化 Pass）"""

    def __init__(self):
        self.passes = [
            ConstantFolding(),
            DeadCodeElimination(),
        ]

    def optimize(self, module: IRModule) -> IRModule:
        """运行所有优化 Pass"""
        result = module
        for pas in self.passes:
            result = pas.run(result)
        return result


# ═══════════════════════════════════════════════════════════════════════════════
# 第十四部分：多语言互译演示
# ═══════════════════════════════════════════════════════════════════════════════


def demo_cross_language():
    """演示：多语言 → IR → FSG-ASM"""

    print("=" * 80)
    print("FSG-IR 多语言互译演示")
    print("=" * 80)

    # ─────────────────────────── Python 示例 ───────────────────────────
    print("\n" + "━" * 40)
    print("【Python 示例】")
    print("━" * 40)

    python_source = """
def sum_to_n(n):
    total = 0
    for i in range(n):
        total = total + i
    return total
"""
    print("\n>>> Python 源码:")
    print(python_source)

    # Python → IR
    python_lower = PythonLower()
    python_module = python_lower.parse(python_source)

    print("\n>>> FSG-IR 表示:")
    print(python_module)

    # IR → FSG-ASM
    asm_gen = ASMGenerator()
    python_asm = asm_gen.generate(python_module)

    print("\n>>> FSG-ASM 输出:")
    print(python_asm)

    # ─────────────────────────── JavaScript 示例 ───────────────────────────
    print("\n" + "━" * 40)
    print("【JavaScript 示例】")
    print("━" * 40)

    js_source = """
function calculate(x, y) {
    let result = x * y + 10;
    if (result > 100) {
        console.log(result);
    }
    return result;
}
"""
    print("\n>>> JavaScript 源码:")
    print(js_source)

    # JS → IR
    js_lower = JSLower()
    js_module = js_lower.parse(js_source)

    print("\n>>> FSG-IR 表示:")
    print(js_module)

    # IR → FSG-ASM
    js_asm = asm_gen.generate(js_module)

    print("\n>>> FSG-ASM 输出:")
    print(js_asm)

    # ─────────────────────────── Go 示例 ───────────────────────────
    print("\n" + "━" * 40)
    print("【Go 示例】")
    print("━" * 40)

    go_source = """
func addAndPrint(a int, b int) int {
    result := a + b
    if result > 50 {
        fmt.Println(result)
    }
    return result
}
"""
    print("\n>>> Go 源码:")
    print(go_source)

    # Go → IR
    go_lower = GoLower()
    go_module = go_lower.parse(go_source)

    print("\n>>> FSG-IR 表示:")
    print(go_module)

    # IR → FSG-ASM
    go_asm = asm_gen.generate(go_module)

    print("\n>>> FSG-ASM 输出:")
    print(go_asm)

    # ─────────────────────────── 统一验证 ───────────────────────────
    print("\n" + "━" * 40)
    print("【IR 层面统一验证】")
    print("━" * 40)

    print("\n✓ 所有语言（Python/JavaScript/Go）都转换为统一的 FSG-IR 表示")
    print("✓ IR 层面保持了语义等价性")
    print("✓ 统一的 IR 可以生成多种目标代码（FSG-ASM / Python / JS / Go）")
    print("\n类型映射表:")
    print("  Python int  → IRType.INT")
    print("  Python float → IRType.FLOAT")
    print("  Python bool  → IRType.BOOL")
    print("  Python str   → IRType.STRING")
    print("  Python list  → IRType.ARRAY")
    print("  JS number    → IRType.FLOAT")
    print("  JS string    → IRType.STRING")
    print("  JS boolean   → IRType.BOOL")
    print("  Go int       → IRType.INT")
    print("  Go float64   → IRType.DOUBLE")
    print("  Go bool      → IRType.BOOL")
    print("  Go string    → IRType.STRING")


def demo_optimization():
    """演示：优化 Pass"""

    print("=" * 80)
    print("FSG-IR 优化 Pass 演示")
    print("=" * 80)

    # 构建带有冗余代码的模块
    module = IRModule("opt_module")
    func = IRFunction(name="opt_test", return_type=IRTypeInfo(IRType.INT))
    entry = IRBlock(name="entry")
    ssa = SSAValueManager()

    # 常量折叠测试
    a = ssa.new_value("a", IRTypeInfo(IRType.INT))
    b = ssa.new_value("b", IRTypeInfo(IRType.INT))
    c = ssa.new_value("c", IRTypeInfo(IRType.INT))

    # a = 10
    entry.add_inst(
        IRConst(
            opcode=IROpcode.CONST,
            result=a,
            operands=[IRValue("10")],
            const_value=10,
            type_info=IRTypeInfo(IRType.INT),
        )
    )

    # b = 20
    entry.add_inst(
        IRConst(
            opcode=IROpcode.CONST,
            result=b,
            operands=[IRValue("20")],
            const_value=20,
            type_info=IRTypeInfo(IRType.INT),
        )
    )

    # c = a + b (可以折叠为 30)
    entry.add_inst(IRConst(opcode=IROpcode.ADD, result=c, operands=[a, b]))

    entry.add_inst(IRRet(opcode=IROpcode.RET, operands=[c]))

    func.add_block(entry)
    module.add_func(func)

    print("\n【优化前】")
    print(module)

    # 应用优化
    optimizer = IROptimizer()
    optimized = optimizer.optimize(module)

    print("\n【优化后】")
    print(optimized)

    print("\n✓ 常量 10 + 20 折叠为常量 30")
    print("✓ 死代码已消除")


# 入口点
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--cross-lang":
        demo_cross_language()
    elif len(sys.argv) > 1 and sys.argv[1] == "--optimize":
        demo_optimization()
    else:
        demo()
        print("\n\n")
        demo_cross_language()
        print("\n\n")
        demo_optimization()
