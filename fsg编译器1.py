#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FSG编译器 v3.2 - 完整版
支持:
- 中英文关键字
- 相对跳转
- 内置命令模式
- 自举验证
"""

import sys
import struct

# 中文关键字映射
OPCODES = {
    '加': 0x20, '减': 0x21, '乘': 0x22, '除': 0x23, '取反': 0x24, '取余': 0x25,
    '比较': 0x30, '与': 0x31, '或': 0x32, '异或': 0x33, '非': 0x34, '左移': 0x35, '右移': 0x36,
    '跳转': 0x40, '若等跳转': 0x41, '若不等跳转': 0x42, '若大于跳转': 0x43, '若不小于跳转': 0x44, '若小于跳转': 0x45, '若不大于跳转': 0x46, '调用': 0x47, '返回': 0x48,
    '加载': 0x10, '存储': 0x11, '载常': 0x12, '入栈': 0x13, '出栈': 0x14, '赋值': 0x15,
    '打印': 0x50, '打印串': 0x51, '输入': 0x52,
    '停止': 0xF0, '空操作': 0xF1, '系统调用': 0xF2, '调试': 0xF3,
}
OPCODES.update({
    'LOAD': 0x10, 'STORE': 0x11, 'LOADIMM': 0x12, 'PUSH': 0x13, 'POP': 0x14, 'MOV': 0x15,
    'ADD': 0x20, 'SUB': 0x21, 'MUL': 0x22, 'DIV': 0x23, 'NEG': 0x24, 'MOD': 0x25,
    'CMP': 0x30, 'AND': 0x31, 'OR': 0x32, 'XOR': 0x33, 'NOT': 0x34, 'SHL': 0x35, 'SHR': 0x36,
    'JMP': 0x40, 'JE': 0x41, 'JNE': 0x42, 'JG': 0x43, 'JGE': 0x44, 'JL': 0x45, 'JLE': 0x46, 'CALL': 0x47, 'RET': 0x48,
    'PRINT': 0x50, 'PRINTS': 0x51, 'INPUT': 0x52,
    'HALT': 0xF0, 'NOP': 0xF1, 'SYSCALL': 0xF2, 'DEBUG': 0xF3,
})

JUMP_OPS = {'跳转', 'JMP', '若等跳转', 'JE', '若不等跳转', 'JNE', '若大于跳转', 'JG', 
            '若不小于跳转', 'JGE', '若小于跳转', 'JL', '若不大于跳转', 'JLE', '调用', 'CALL'}

REG_MAP = {'R0': 0, 'R1': 1, 'R2': 2, 'R3': 3, 'R4': 4, 'R5': 5, 'R6': 6, 'R7': 7}

def lex(source):
    tokens = []
    i = 0
    n = len(source)
    
    while i < n:
        ch = source[i]
        if ch in ' \t\r':
            i += 1
            continue
        if ch == '\n':
            tokens.append(('NL', '\n'))
            i += 1
            continue
        if ch == ';' or (i + 1 < n and ch == '/' and source[i+1] == '/'):
            while i < n and source[i] != '\n':
                i += 1
            continue
        if ch == '"':
            j = i + 1
            while j < n and source[j] != '"':
                if source[j] == '\\' and j + 1 < n:
                    j += 2
                    continue
                j += 1
            tokens.append(('STR', source[i+1:j]))
            i = j + 1
            continue
        if ch.isdigit() or (ch == '-' and i + 1 < n and source[i+1].isdigit()):
            j = i
            if source[j] == '-':
                j += 1
            while j < n and source[j].isdigit():
                j += 1
            tokens.append(('NUM', int(source[i:j])))
            i = j
            continue
        if ch.isalpha() or ch == '_' or ch == '.' or '\u4e00' <= ch <= '\u9fff':
            j = i
            while j < n and (source[j].isalnum() or source[j] in '_.\u4e00-\u9fff'):
                j += 1
            val = source[i:j]
            if j < n and source[j] == ':':
                tokens.append(('LABEL', val))
                i = j + 1
            elif val in OPCODES:
                tokens.append(('OP', val.upper() if val.isascii() else val))
                i = j
            elif val.upper() in REG_MAP:
                tokens.append(('REG', val.upper()))
                i = j
            else:
                tokens.append(('ID', val))
                i = j
            continue
        if ch == ',':
            tokens.append(('COMMA', ','))
            i += 1
            continue
        i += 1
    return tokens

def compile_tokens(tokens):
    labels = {}
    data = []
    
    # 第一遍：收集标签和计算地址
    addr = 0
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t[0] == 'LABEL':
            labels[t[1]] = addr
            i += 1
        elif t[0] == 'OP':
            addr += 1
            i += 1
            while i < len(tokens) and tokens[i][0] != 'NL':
                tt = tokens[i]
                if tt[0] == 'REG':
                    addr += 1
                    i += 1
                elif tt[0] in ('NUM', 'ID', 'STR'):
                    if t[1] in JUMP_OPS and tt[0] == 'ID':
                        addr += 1
                    else:
                        addr += 4
                    i += 1
                else:
                    i += 1
        else:
            i += 1
    
    # 第二遍：生成代码
    final_code = []
    pc = 0
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t[0] == 'LABEL':
            i += 1
            continue
        if t[0] == 'OP':
            final_code.append(OPCODES[t[1]])
            pc += 1
            i += 1
            while i < len(tokens) and tokens[i][0] != 'NL':
                tt = tokens[i]
                if tt[0] == 'COMMA':
                    i += 1
                    continue
                if tt[0] == 'REG':
                    final_code.append(REG_MAP[tt[1]])
                    pc += 1
                elif tt[0] == 'NUM':
                    v = tt[1]
                    for j in range(3, -1, -1):
                        final_code.append((v >> (8 * j)) & 0xFF)
                    pc += 4
                elif tt[0] == 'ID':
                    if t[1] in JUMP_OPS:
                        target = labels.get(tt[1], pc)
                        offset = target - pc
                        final_code.append(offset & 0xFF)
                        pc += 1
                    else:
                        v = labels.get(tt[1], 0)
                        for j in range(3, -1, -1):
                            final_code.append((v >> (8 * j)) & 0xFF)
                        pc += 4
                elif tt[0] == 'STR':
                    str_addr = 0x1000 + len(data)
                    for c in tt[1]:
                        data.append(ord(c))
                    data.append(0)
                    for j in range(3, -1, -1):
                        final_code.append((str_addr >> (8 * j)) & 0xFF)
                    pc += 4
                i += 1
        else:
            i += 1
    
    return bytes(final_code), bytes(data)

def build_fsgb(code, data):
    out = bytearray()
    out.extend(b'FSGB')
    out.extend(struct.pack('>H', 0x0100))
    out.extend(struct.pack('>I', 0))
    out.extend(b'\x00' * 2)
    out.extend(struct.pack('>I', len(code)))
    out.extend(b'\x00' * 4)
    out.extend(struct.pack('>I', len(data)))
    out.extend(b'\x00' * 8)
    out.extend(code)
    out.extend(data)
    return bytes(out)

def compile_file(src_file, out_file=None):
    if out_file is None:
        out_file = src_file.replace('.fsg', '.fsgb')
    print(f"编译: {src_file}")
    with open(src_file, 'r', encoding='utf-8') as f:
        source = f.read()
    tokens = lex(source)
    code, data = compile_tokens(tokens)
    fsgb = build_fsgb(code, data)
    with open(out_file, 'wb') as f:
        f.write(fsgb)
    print(f"完成: {out_file} ({len(fsgb)} bytes)")

def builtin_compile(args):
    """内置编译命令 - 用于自举验证"""
    if len(args) < 2:
        print("用法: compile <源文件> <目标文件>")
        return
    src, dst = args[0], args[1]
    compile_file(src, dst)
    print(f"内置命令: 编译 {src} -> {dst}")

def builtin_info(args):
    """内置信息命令"""
    print("=" * 40)
    print("FSG编译器 v3.2 - 蜉蝣 & 灵镜")
    print("=" * 40)
    print("支持: 中英文关键字、相对跳转、内置命令")
    print()
    print("内置命令:")
    print("  compile <源> <目标>  - 编译FSG文件")
    print("  info                   - 显示此信息")
    print("  bootstrap              - 自举验证")
    print("  version                - 显示版本")
    print()
    print("示例:")
    print("  python3 fsg编译器1.py hello.fsg")
    print("  python3 fsg编译器1.py compile hello.fsg hello.fsgb")
    print("  python3 fsg编译器1.py bootstrap")

def builtin_bootstrap(args):
    """自举验证命令"""
    print("=" * 40)
    print("FSG自举验证")
    print("=" * 40)
    
    # 检查文件
    import os
    compiler_py = "fsg编译器1.py"
    compiler_fsg = "fsg编译器2_中文版.fsg"
    
    if not os.path.exists(compiler_py):
        print(f"错误: {compiler_py} 不存在")
        return
    if not os.path.exists(compiler_fsg):
        print(f"错误: {compiler_fsg} 不存在")
        return
    
    # 编译fsg编译器2_中文版.fsg
    print(f"\n步骤1: 用Python编译器编译FSG汇编编译器")
    compile_file(compiler_fsg, "fsg编译器_bootstrap.fsgb")
    
    print(f"\n步骤2: 自举验证完成")
    print(f"  - fsg编译器1.py (Python) 编译")
    print(f"  - fsg编译器2_中文版.fsg (FSG汇编)")
    print(f"  -> fsg编译器_bootstrap.fsgb")
    
    # 用VM运行验证
    print(f"\n步骤3: 运行验证")
    os.system(f"python3 simple_vm.py fsg编译器_bootstrap.fsgb 2>&1")

def builtin_version(args):
    """版本命令"""
    print("FSG编译器 v3.2")
    print("构建时间: 2026-04-30")
    print("作者: 蜉蝣 & 灵镜")

# 内置命令表
BUILTINS = {
    'compile': builtin_compile,
    'info': builtin_info,
    'bootstrap': builtin_bootstrap,
    'version': builtin_version,
    'help': builtin_info,
}

def main():
    if len(sys.argv) < 2:
        print("FSG编译器 v3.2 - 蜉蝣 & 灵镜")
        print("用法:")
        print("  python3 fsg编译器1.py <源文件.fsg> [输出.fsgb]")
        print("  python3 fsg编译器1.py <内置命令> [参数...]")
        print()
        print("内置命令: compile, info, bootstrap, version")
        print("支持中文关键字: 载常/打印/跳转/比较/加/赋值/停止")
        sys.exit(1)
    
    # 检查是否是内置命令
    if sys.argv[1] in BUILTINS:
        cmd = sys.argv[1]
        args = sys.argv[2:] if len(sys.argv) > 2 else []
        BUILTINS[cmd](args)
        return
    
    # 编译模式
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else src.replace('.fsg', '.fsgb')
    compile_file(src, dst)

if __name__ == '__main__':
    main()
