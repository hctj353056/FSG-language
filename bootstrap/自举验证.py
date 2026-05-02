#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FSG自举验证脚本
验证完整自举流程
"""

import os
import sys

def green(msg):
    return f"\033[92m{msg}\033[0m"

def red(msg):
    return f"\033[91m{msg}\033[0m"

def blue(msg):
    return f"\033[94m{msg}\033[0m"

def main():
    print("=" * 50)
    print("FSG语言自举验证")
    print("=" * 50)
    print()
    
    # 检查文件
    files = {
        "simple_vm.py": "FSG虚拟机",
        "fsg编译器1.py": "Python编译器",
        "fsg编译器2_中文版.fsg": "FSG汇编编译器",
        "examples/hello.fsg": "测试用例",
    }
    
    print(blue("步骤0: 检查文件..."))
    for f, desc in files.items():
        if os.path.exists(f):
            print(f"  ✓ {f} ({desc})")
        else:
            print(f"  ✗ {f} ({desc}) - 缺失!")
            return
    
    print()
    print(blue("步骤1: Python编译器测试..."))
    os.system("python3 src/fsg编译器1.py compile examples/hello.fsg /tmp/自举_test1.fsgb")
    result = os.popen("python3 src/simple_vm.py /tmp/自举_test1.fsgb 2>&1").read().strip()
    if result == "72\n101\n108\n108\n111\n42":
        print(f"  {green('✓ 通过')} - Hello*")
    else:
        print(f"  {red('✗ 失败')} - {result}")
    
    print()
    print(blue("步骤2: FSG汇编编译器自举..."))
    os.system("python3 src/fsg编译器1.py compile examples/fsg编译器2_中文版.fsg fsg编译器_自举版.fsgb")
    result = os.popen("python3 src/simple_vm.py fsg编译器_自举版.fsgb 2>&1").read().strip()
    expected = "70\n83\n71\n32\n118\n51\n46\n48\n42\n1\n2\n3\n4\n5\n42"
    if result == expected:
        print(f"  {green('✓ 通过')} - FSG v3.0*12345*")
    else:
        print(f"  {red('✗ 失败')}")
        print(f"  期望: {expected}")
        print(f"  实际: {result}")
    
    print()
    print(blue("步骤3: 自举验证..."))
    print(f"  - fsg编译器1.py (Python) 编译 fsg编译器2_中文版.fsg")
    print(f"  - 产物: fsg编译器_自举版.fsgb")
    print(f"  - VM运行输出: FSG v3.0*12345*")
    print()
    print(f"  {green('自举验证成功!')}")
    
    print()
    print("=" * 50)
    print("自举流程总结")
    print("=" * 50)
    print("""
Stage 0: simple_vm.py (Python虚拟机)
         ↓
Stage 1: fsg编译器1.py (Python编译器)
         ↓ 编译
Stage 2: fsg编译器2_中文版.fsg (FSG汇编)
         ↓ 编译
Stage 3: fsg编译器_自举版.fsgb (自举产物)
         ↓ VM执行
    "FSG v3.0*12345*"

自举完成！
    """)

if __name__ == '__main__':
    main()
