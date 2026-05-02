#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FSG 语言双层词法分析器
FSG Language Dual-Layer Lexer

功能：
1. 高级自然语言层分词（声明、模块、定义、流程...）
2. 汇编层分词（LOAD、ADD、JMP...）
3. 双层 Token 规范化与映射

版本: 1.0 | 2026-04-26
"""

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════
# 第一部分：Token 类型定义
# ═══════════════════════════════════════════════════════════════


class TokenType(Enum):
    """FSG Token 类型枚举"""

    # ─── 高级层专有 ───
    HIGH_DECLARE = auto()  # 声明
    HIGH_MODULE = auto()  # 模块
    HIGH_IMPORT = auto()  # 引
    HIGH_DEFINE = auto()  # 定义
    HIGH_FUNC = auto()  # 流程/递归
    HIGH_INPUT = auto()  # 输入
    HIGH_OUTPUT = auto()  # 输出
    HIGH_GET = auto()  # 获取
    HIGH_USE = auto()  # 使用
    HIGH_PASS = auto()  # 传入
    HIGH_ASSIGN = auto()  # 得到/赋值
    HIGH_IF = auto()  # 若
    HIGH_THEN = auto()  # 则
    HIGH_ELSE = auto()  # 否则
    HIGH_WHILE = auto()  # 当
    HIGH_FOR = auto()  # 循环
    HIGH_RETURN = auto()  # 返回
    HIGH_AND = auto()  # 且
    HIGH_OR = auto()  # 或
    HIGH_NOT = auto()  # 非
    HIGH_TRUE = auto()  # 真
    HIGH_FALSE = auto()  # 假
    HIGH_NULL = auto()  # 空/null
    HIGH_EACH = auto()  # 依次
    HIGH_SIMILAR = auto()  # 如
    HIGH_DOT = auto()  # 的/. 的（成员访问）

    # ─── 汇编层专有 ───
    ASM_LOAD = auto()  # LOAD
    ASM_STORE = auto()  # STORE
    ASM_LOADIMM = auto()  # LOADIMM
    ASM_PUSH = auto()  # PUSH
    ASM_POP = auto()  # POP
    ASM_MOV = auto()  # MOV
    ASM_ADD = auto()  # ADD
    ASM_SUB = auto()  # SUB
    ASM_MUL = auto()  # MUL
    ASM_DIV = auto()  # DIV
    ASM_NEG = auto()  # NEG
    ASM_MOD = auto()  # MOD
    ASM_CMP = auto()  # CMP
    ASM_AND = auto()  # AND
    ASM_OR = auto()  # OR
    ASM_XOR = auto()  # XOR
    ASM_NOT = auto()  # NOT
    ASM_SHL = auto()  # SHL
    ASM_SHR = auto()  # SHR
    ASM_JMP = auto()  # JMP
    ASM_JE = auto()  # JE
    ASM_JNE = auto()  # JNE
    ASM_JG = auto()  # JG
    ASM_JGE = auto()  # JGE
    ASM_JL = auto()  # JL
    ASM_JLE = auto()  # JLE
    ASM_CALL = auto()  # CALL
    ASM_RET = auto()  # RET
    ASM_PRINT = auto()  # PRINT
    ASM_INPUT = auto()  # INPUT
    ASM_PRINTS = auto()  # PRINTS
    ASM_HALT = auto()  # HALT
    ASM_NOP = auto()  # NOP
    ASM_SYSCALL = auto()  # SYSCALL
    ASM_DEBUG = auto()  # DEBUG
    ASM_INT = auto()  # INT

    # ─── 通用 ───
    IDENTIFIER = auto()  # 标识符
    STRING = auto()  # 字符串 "..."
    CHAR = auto()  # 字符 'x'
    INTEGER = auto()  # 整数 123
    HEX = auto()  # 十六进制 0xFF
    BINARY = auto()  # 二进制 0b1010
    FLOAT = auto()  # 浮点数 3.14
    REGISTER = auto()  # 寄存器 R0-R7
    SPECIAL_REG = auto()  # 特殊寄存器 PC/SP/BP
    LABEL_DEF = auto()  # 标签定义 name:
    LABEL_REF = auto()  # 标签引用
    DIRECTIVE = auto()  # 伪指令 .SOMETHING
    OPERATOR = auto()  # 运算符 + - * / % = ...
    LPAREN = auto()  # 左括号 (
    RPAREN = auto()  # 右括号 )
    LBRACKET = auto()  # 左中括号 [
    RBRACKET = auto()  # 右中括号 ]
    LBRACE = auto()  # 左大括号 {
    RBRACE = auto()  # 右大括号 }
    COMMA = auto()  # 逗号 ，
    SEMICOLON = auto()  # 分号 ；
    COLON = auto()  # 冒号 ：
    DOT = auto()  # 点 .
    NEWLINE = auto()  # 换行
    COMMENT = auto()  # 注释
    WHITESPACE = auto()  # 空白
    EOF = auto()  # 文件结束
    UNKNOWN = auto()  # 未知token


# ═══════════════════════════════════════════════════════════════
# 第二部分：词表定义（双层对照）
# ═══════════════════════════════════════════════════════════════

# 高级自然语言层关键字映射表
HIGH_KEYWORDS: Dict[str, TokenType] = {
    # 结构关键字
    "声明": TokenType.HIGH_DECLARE,
    "模块": TokenType.HIGH_MODULE,
    "引": TokenType.HIGH_IMPORT,
    "定义": TokenType.HIGH_DEFINE,
    "流程": TokenType.HIGH_FUNC,
    "递归": TokenType.HIGH_FUNC,
    "使用": TokenType.HIGH_USE,
    "传入": TokenType.HIGH_PASS,
    "调用": TokenType.HIGH_USE,
    # I/O 关键字
    "输入": TokenType.HIGH_INPUT,
    "输出": TokenType.HIGH_OUTPUT,
    "获取": TokenType.HIGH_GET,
    "打印": TokenType.HIGH_OUTPUT,
    "显示": TokenType.HIGH_OUTPUT,
    # 控制流关键字
    "若": TokenType.HIGH_IF,
    "则": TokenType.HIGH_THEN,
    "否则": TokenType.HIGH_ELSE,
    "当": TokenType.HIGH_WHILE,
    "循环": TokenType.HIGH_FOR,
    "返回": TokenType.HIGH_RETURN,
    "如": TokenType.HIGH_SIMILAR,
    "依次": TokenType.HIGH_EACH,
    # 逻辑关键字
    "且": TokenType.HIGH_AND,
    "并且": TokenType.HIGH_AND,
    "或": TokenType.HIGH_OR,
    "或者": TokenType.HIGH_OR,
    "非": TokenType.HIGH_NOT,
    # 值关键字
    "真": TokenType.HIGH_TRUE,
    "假": TokenType.HIGH_FALSE,
    "空": TokenType.HIGH_NULL,
    "null": TokenType.HIGH_NULL,
    # 成员访问
    "的": TokenType.HIGH_DOT,
}

# 汇编层指令助记符映射表
ASM_MNEMONICS: Dict[str, TokenType] = {
    # 数据传输
    "LOAD": TokenType.ASM_LOAD,
    "STORE": TokenType.ASM_STORE,
    "LOADIMM": TokenType.ASM_LOADIMM,
    "PUSH": TokenType.ASM_PUSH,
    "POP": TokenType.ASM_POP,
    "MOV": TokenType.ASM_MOV,
    # 算术运算
    "ADD": TokenType.ASM_ADD,
    "SUB": TokenType.ASM_SUB,
    "MUL": TokenType.ASM_MUL,
    "DIV": TokenType.ASM_DIV,
    "NEG": TokenType.ASM_NEG,
    "MOD": TokenType.ASM_MOD,
    # 比较与逻辑
    "CMP": TokenType.ASM_CMP,
    "AND": TokenType.ASM_AND,
    "OR": TokenType.ASM_OR,
    "XOR": TokenType.ASM_XOR,
    "NOT": TokenType.ASM_NOT,
    "SHL": TokenType.ASM_SHL,
    "SHR": TokenType.ASM_SHR,
    # 控制流
    "JMP": TokenType.ASM_JMP,
    "JE": TokenType.ASM_JE,
    "JNE": TokenType.ASM_JNE,
    "JG": TokenType.ASM_JG,
    "JGE": TokenType.ASM_JGE,
    "JL": TokenType.ASM_JL,
    "JLE": TokenType.ASM_JLE,
    "CALL": TokenType.ASM_CALL,
    "RET": TokenType.ASM_RET,
    # I/O
    "PRINT": TokenType.ASM_PRINT,
    "INPUT": TokenType.ASM_INPUT,
    "PRINTS": TokenType.ASM_PRINTS,
    # 系统
    "HALT": TokenType.ASM_HALT,
    "NOP": TokenType.ASM_NOP,
    "SYSCALL": TokenType.ASM_SYSCALL,
    "DEBUG": TokenType.ASM_DEBUG,
    "INT": TokenType.ASM_INT,
}

# 寄存器定义
REGISTER_PATTERN = re.compile(r"^R([0-7])$")
SPECIAL_REGISTERS = {"PC", "SP", "BP"}

# 伪指令模式
DIRECTIVE_PATTERN = re.compile(r"^\.(\w+)$")


# ═══════════════════════════════════════════════════════════════
# 第三部分：Token 数据结构
# ═══════════════════════════════════════════════════════════════


@dataclass
class Token:
    """Token 数据结构"""

    type: TokenType
    value: str
    line: int
    column: int
    layer: str  # 'high' 或 'asm'

    def __repr__(self):
        return (
            f"Token({self.type.name}, '{self.value}', "
            f"L{self.line}:C{self.column}, [{self.layer}])"
        )

    def to_dict(self) -> dict:
        """转换为字典，便于序列化"""
        return {
            "type": self.type.name,
            "value": self.value,
            "line": self.line,
            "column": self.column,
            "layer": self.layer,
        }


# ═══════════════════════════════════════════════════════════════
# 第四部分：词法分析器
# ═══════════════════════════════════════════════════════════════


class FSGTokenizer:
    """
    FSG 双层词法分析器

    自动识别代码属于高级层还是汇编层，并进行分词
    """

    # 正则表达式定义（按优先级排序）
    TOKEN_PATTERNS = [
        # 空白（跳过）
        (r"[ \t\r]+", TokenType.WHITESPACE),
        # 换行
        (r"\n", TokenType.NEWLINE),
        # 注释
        (r"；[^\n]*", TokenType.COMMENT),  # 高级层中文分号
        (r";[^\n]*", TokenType.COMMENT),  # 汇编层英文分号
        # 字符串（双引号，支持插值）
        (r'"(?:[^{}]|\{[^}]+\})*"', TokenType.STRING),
        (r'"[^"]*"', TokenType.STRING),
        # 字符常量
        (r"'[^']'", TokenType.CHAR),
        # 十六进制
        (r"0x[0-9a-fA-F]+", TokenType.HEX),
        # 二进制
        (r"0b[01]+", TokenType.BINARY),
        # 浮点数
        (r"[+-]?\d+\.\d+", TokenType.FLOAT),
        # 整数
        (r"[+-]?\d+", TokenType.INTEGER),
        # 寄存器
        (r"R[0-7]", TokenType.REGISTER),
        # 特殊寄存器
        (r"\b(PC|SP|BP)\b", TokenType.SPECIAL_REG),
        # 伪指令
        (r"\.\w+", TokenType.DIRECTIVE),
        # 标签定义（identifier:）
        (r"[A-Za-z_\u4e00-\u9fff][A-Za-z0-9_\u4e00-\u9fff]*:", TokenType.LABEL_DEF),
        # 标识符和关键字
        (r"[A-Za-z_\u4e00-\u9fff][A-Za-z0-9_\u4e00-\u9fff]*", TokenType.IDENTIFIER),
        # 运算符
        (r"≥|≤|≠|≡", TokenType.OPERATOR),  # 多字符运算符优先
        (r"[+\-*/%=<>^!&|~]", TokenType.OPERATOR),
        # 分隔符
        (r"（", TokenType.LPAREN),  # 中文括号
        (r"）", TokenType.RPAREN),
        (r"\[", TokenType.LBRACKET),
        (r"\]", TokenType.RBRACKET),
        (r"\{", TokenType.LBRACE),
        (r"\}", TokenType.RBRACE),
        (r"，", TokenType.COMMA),  # 中文逗号
        (r"；", TokenType.SEMICOLON),  # 中文分号
        (r"：", TokenType.COLON),  # 中文冒号
        (r"、", TokenType.COMMA),  # 中文顿号（列表分隔）
        (r"@|\$|::|\.\.\.", TokenType.OPERATOR),  # 特殊运算符
        (r"\.", TokenType.DOT),
        (r",", TokenType.COMMA),
        # 未知字符
        (r".", TokenType.UNKNOWN),
    ]

    def __init__(self):
        self.tokens: List[Token] = []
        self.errors: List[dict] = []
        self.detected_layer: Optional[str] = None

    def tokenize(self, code: str) -> List[Token]:
        """
        对代码进行分词

        Args:
            code: 源代码字符串

        Returns:
            Token 列表
        """
        self.tokens = []
        self.errors = []
        self._detect_layer(code)

        line = 1
        column = 1
        pos = 0

        while pos < len(code):
            matched = False

            for pattern, token_type in self.TOKEN_PATTERNS:
                regex = re.compile(pattern)
                match = regex.match(code, pos)

                if match:
                    value = match.group()
                    start_col = column

                    # 跳过空白
                    if token_type == TokenType.WHITESPACE:
                        pos += len(value)
                        column += len(value)
                        matched = True
                        break

                    # 处理换行
                    if token_type == TokenType.NEWLINE:
                        self.tokens.append(
                            Token(
                                token_type, value, line, start_col, self.detected_layer
                            )
                        )
                        pos += 1
                        line += 1
                        column = 1
                        matched = True
                        break

                    # 分类标识符和关键字
                    if token_type == TokenType.IDENTIFIER:
                        # 高级层关键字
                        if value in HIGH_KEYWORDS:
                            token_type = HIGH_KEYWORDS[value]
                            layer = "high"
                        # 汇编层关键字
                        elif value.upper() in ASM_MNEMONICS:
                            token_type = ASM_MNEMONICS[value.upper()]
                            layer = "asm"
                            value = value.upper()  # 统一大写
                        # 用户定义的标识符
                        else:
                            layer = self.detected_layer or "high"
                    else:
                        layer = self.detected_layer or "high"

                    # 寄存器统一处理
                    if token_type == TokenType.REGISTER:
                        layer = "asm"

                    # 伪指令统一处理
                    if token_type == TokenType.DIRECTIVE:
                        layer = "asm"

                    # 标签定义统一处理
                    if token_type == TokenType.LABEL_DEF:
                        layer = "asm"
                        value = value[:-1]  # 去掉冒号

                    self.tokens.append(Token(token_type, value, line, start_col, layer))

                    pos += len(value)
                    column += len(value)
                    matched = True
                    break

            if not matched:
                self.errors.append(
                    {
                        "position": pos,
                        "line": line,
                        "column": column,
                        "char": code[pos] if pos < len(code) else "EOF",
                    }
                )
                pos += 1
                column += 1

        # 添加 EOF token
        self.tokens.append(Token(TokenType.EOF, "", line, column, "unknown"))

        return self.tokens

    def _detect_layer(self, code: str) -> None:
        """
        自动检测代码属于哪个层级

        检测逻辑：
        - 高级层特征：中文关键字、引号、中文括号
        - 汇编层特征：英文助记符、R0-R7寄存器、点号伪指令、冒号标签
        """
        high_score = 0
        asm_score = 0

        # 高级层特征
        high_chars = set(
            "声明模块引定义流程输入输出获取使用传入得到依次若则否则当循环返回且或非真的假的空中文"
        )
        high_patterns = ['"', '"', "（", "）", "：", "；", "，"]

        # 汇编层特征
        asm_keywords = set(k.upper() for k in ASM_MNEMONICS.keys())
        asm_patterns = ["R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7", ".", ":"]

        for char in code:
            if char in high_chars:
                high_score += 1
            if char in high_patterns:
                high_score += 2

        code_upper = code.upper()
        for keyword in asm_keywords:
            high_score += code.count(keyword) * 0.5  # 英文关键字权重较低
        for keyword in asm_keywords:
            if keyword in code_upper:
                asm_score += 3

        for pattern in asm_patterns:
            asm_score += code.count(pattern) * 2

        if asm_score > high_score * 1.5:
            self.detected_layer = "asm"
        else:
            self.detected_layer = "high"


# ═══════════════════════════════════════════════════════════════
# 第五部分：双层 Token 映射
# ═══════════════════════════════════════════════════════════════


class TokenMapper:
    """
    双层 Token 映射器

    实现高级层 Token 与汇编层 Token 的双向转换
    """

    # 高级层结构 → 汇编层结构 的映射
    HIGH_STRUCTURE_TO_ASM: Dict[TokenType, List[TokenType]] = {
        TokenType.HIGH_DECLARE: [],  # 元信息，无直接对应
        TokenType.HIGH_MODULE: [],  # 模块 → .GLOBAL（在符号表中处理）
        TokenType.HIGH_IMPORT: [TokenType.ASM_LOAD, TokenType.ASM_MOV],
        TokenType.HIGH_DEFINE: [],  # 定义 → .DATA/.DW
        TokenType.HIGH_FUNC: [],  # 流程 → 标签+指令序列
        TokenType.HIGH_INPUT: [TokenType.ASM_PRINTS, TokenType.ASM_INPUT],
        TokenType.HIGH_OUTPUT: [TokenType.ASM_PRINT, TokenType.ASM_PRINTS],
        TokenType.HIGH_GET: [TokenType.ASM_LOAD],
        TokenType.HIGH_USE: [TokenType.ASM_CALL],
        TokenType.HIGH_PASS: [],  # 传入 → PUSH/R0-R3
        TokenType.HIGH_ASSIGN: [TokenType.ASM_MOV, TokenType.ASM_LOADIMM],
        TokenType.HIGH_IF: [TokenType.ASM_CMP],
        TokenType.HIGH_THEN: [TokenType.ASM_JE, TokenType.ASM_JNE, TokenType.ASM_JMP],
        TokenType.HIGH_ELSE: [TokenType.ASM_JMP],
        TokenType.HIGH_WHILE: [TokenType.ASM_CMP],
        TokenType.HIGH_RETURN: [TokenType.ASM_RET],
    }

    # 运算映射：高级运算符 → 汇编指令序列
    HIGH_OP_TO_ASM: Dict[str, str] = {
        "+": "ADD",
        "-": "SUB",
        "*": "MUL",
        "/": "DIV",
        "%": "MOD",
        "=": "CMP",  # 比较
        "≠": "CMP",
        ">": "CMP",
        "<": "CMP",
        "≥": "CMP",
        "≤": "CMP",
        "且": "AND",
        "||": "OR",
        "或": "OR",
        "非": "NOT",
    }

    @classmethod
    def get_asm_mnemonic(cls, token: Token) -> Optional[str]:
        """获取 Token 对应的汇编助记符"""
        if token.layer == "asm":
            return token.value

        if token.type in cls.HIGH_OP_TO_ASM:
            return cls.HIGH_OP_TO_ASM[token.value]

        # 查找映射
        for high_type, asm_types in cls.HIGH_STRUCTURE_TO_ASM.items():
            if token.type == high_type and asm_types:
                return asm_types[0].name.replace("ASM_", "")

        return None


# ═══════════════════════════════════════════════════════════════
# 第六部分：工具函数
# ═══════════════════════════════════════════════════════════════


def print_tokens(tokens: List[Token], show_whitespace: bool = False) -> None:
    """打印 Token 列表"""
    for token in tokens:
        if token.type == TokenType.WHITESPACE and not show_whitespace:
            continue
        if token.type == TokenType.EOF:
            break
        layer_marker = "▲" if token.layer == "high" else "●"
        print(f"  {layer_marker} {token}")


def print_token_table(tokens: List[Token]) -> None:
    """以表格形式打印 Token"""
    print("\n┌────────┬──────────┬────────────────┬──────┬──────┐")
    print("│ 层级   │  类型    │      值        │ 行   │  列  │")
    print("├────────┼──────────┼────────────────┼──────┼──────┤")

    for token in tokens:
        if token.type == TokenType.WHITESPACE:
            continue
        if token.type == TokenType.EOF:
            break

        layer = "高级" if token.layer == "high" else "汇编"
        type_name = token.type.name.replace("HIGH_", "").replace("ASM_", "")
        value = token.value[:14].ljust(14)
        print(
            f"│ {layer:<6} │ {type_name:<8} │ {value} "
            f"│ {token.line:>4} │ {token.column:>4} │"
        )

    print("└────────┴──────────┴────────────────┴──────┴──────┘")


def analyze_file(filepath: str) -> Tuple[List[Token], List[dict]]:
    """
    分析文件并返回 Token 列表

    Args:
        filepath: 文件路径

    Returns:
        (tokens, errors) 元组
    """
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()

    tokenizer = FSGTokenizer()
    tokens = tokenizer.tokenize(code)

    return tokens, tokenizer.errors


# ═══════════════════════════════════════════════════════════════
# 第七部分：主程序
# ═══════════════════════════════════════════════════════════════


def main():
    """主程序入口"""
    import sys

    if len(sys.argv) < 2:
        # 内置测试代码
        test_code = """
声明：
文件名: test.fsg
编码：UTF-8

模块"求平均数"：
定义"列表1=[ ]"
流程"累加"：
输入列表1，依次取末尾位置元素相加得到A
；
获取列表1元素个数/A得到B
输出B

使用.求平均数
        """

        print("=" * 60)
        print("FSG 双层词法分析器 - 测试")
        print("=" * 60)
        print("\n【测试代码】")
        print(test_code)
        print("\n【分词结果】")

        tokenizer = FSGTokenizer()
        tokens = tokenizer.tokenize(test_code)

        print(f"\n检测到层级: {tokenizer.detected_layer}")
        filtered_tokens = [
            t for t in tokens
            if t.type != TokenType.WHITESPACE and t.type != TokenType.EOF
        ]
        print(f"Token 总数: {len(filtered_tokens)}")

        print_token_table(tokens)

        if tokenizer.errors:
            print("\n【错误】")
            for err in tokenizer.errors:
                print(
                    f"  位置 {err['line']}:{err['column']} - 未知字符 '{err['char']}'"
                )

        # 汇编层测试
        print("\n" + "=" * 60)
        print("【汇编层测试】")
        print("=" * 60)

        asm_code = """
.SECTION .text
.GLOBAL _start
_start:
    LOADIMM R0, 0
    LOADIMM R1, 10
loop:
    ADD R0, R0, R1
    SUB R1, R1, 1
    CMP R1, R0
    JNE loop
    PRINT R0
    HALT
        """

        print("\n【测试代码】")
        print(asm_code)
        print("\n【分词结果】")

        tokenizer2 = FSGTokenizer()
        tokens2 = tokenizer2.tokenize(asm_code)

        print(f"\n检测到层级: {tokenizer2.detected_layer}")
        print_token_table(tokens2)

    else:
        # 文件模式
        filepath = sys.argv[1]
        print(f"分析文件: {filepath}\n")

        tokens, errors = analyze_file(filepath)

        tokenizer = FSGTokenizer()
        with open(filepath, "r", encoding="utf-8") as f:
            tokenizer.tokenize(f.read())

        print(f"检测到层级: {tokenizer.detected_layer}")
        print_token_table(tokens)

        if errors:
            print("\n【错误】")
            for err in errors:
                print(
                    f"  位置 {err['line']}:{err['column']} - 未知字符 '{err['char']}'"
                )


if __name__ == "__main__":
    main()
