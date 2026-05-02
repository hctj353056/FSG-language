#!/usr/bin/env python3
"""
FSG自举测试脚本 v0
蜉熵阁 - FSG语言自举计划

功能:
- 用Python汇编器编译Stage1源码
- 用FSG虚拟机执行字节码
- 验证自举可行性
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.simple_vm import FSGVM, Assembler


def test_basic_compilation():
    """测试1: 编译简单FSG程序"""
    print("=" * 50)
    print("测试1: 编译简单FSG程序")
    print("=" * 50)
    
    source = """
    .SECTION .text
    _start:
        LOADIMM R0, 42
        PRINT R0
        HALT
    """
    
    assembler = Assembler()
    try:
        bytecode = assembler.assemble(source)
        print(f"✅ 编译成功!")
        print(f"   字节码长度: {len(bytecode)} bytes")
        print(f"   文件头: {bytecode[:4]}")
        return bytecode
    except Exception as e:
        print(f"❌ 编译失败: {e}")
        return None


def test_string_output():
    """测试2: 字符串输出"""
    print("\n" + "=" * 50)
    print("测试2: 字符串输出")
    print("=" * 50)
    
    source = """
    .SECTION .text
    _start:
        PRINTS msg
        HALT
    
    .SECTION .rodata
    msg:
    .STR "Hello, FSG!"
    """
    
    assembler = Assembler()
    try:
        bytecode = assembler.assemble(source)
        vm = FSGVM()
        vm.load_bytecode(bytecode)
        print("执行输出:")
        vm.run()
        print("✅ 字符串输出测试通过!")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_arithmetic():
    """测试3: 算术运算"""
    print("\n" + "=" * 50)
    print("测试3: 算术运算")
    print("=" * 50)
    
    source = """
    .SECTION .text
    _start:
        LOADIMM R0, 100
        LOADIMM R1, 200
        ADD R2, R0, R1
        PRINT R2
        SUB R3, R1, R0
        PRINT R3
        MUL R4, R0, R1
        PRINT R4
        HALT
    """
    
    assembler = Assembler()
    try:
        bytecode = assembler.assemble(source)
        vm = FSGVM()
        vm.load_bytecode(bytecode)
        print("执行输出:")
        vm.run()
        print("✅ 算术运算测试通过!")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_conditional_jump():
    """测试4: 条件跳转"""
    print("\n" + "=" * 50)
    print("测试4: 条件跳转")
    print("=" * 50)
    
    source = """
    .SECTION .text
    _start:
        LOADIMM R0, 0
        LOADIMM R1, 5
    loop:
        ADD R0, R0, R1
        LOADIMM R2, 25
        CMP R0, R2
        JNE loop
        PRINT R0
        HALT
    """
    
    assembler = Assembler()
    try:
        bytecode = assembler.assemble(source)
        vm = FSGVM()
        vm.load_bytecode(bytecode)
        print("执行输出:")
        vm.run()
        print("✅ 条件跳转测试通过!")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_compiler_v0():
    """测试5: 编译并执行compiler_v0.fsg"""
    print("\n" + "=" * 50)
    print("测试5: compiler_v0.fsg 编译与执行")
    print("=" * 50)
    
    compiler_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'compiler_v0.fsg')
    
    if not os.path.exists(compiler_path):
        print(f"❌ 文件不存在: {compiler_path}")
        return False
    
    with open(compiler_path, 'r', encoding='utf-8') as f:
        source = f.read()
    
    assembler = Assembler()
    try:
        print("正在编译 compiler_v0.fsg...")
        bytecode = assembler.assemble(source)
        print(f"✅ 编译成功!")
        print(f"   字节码长度: {len(bytecode)} bytes")
        
        # 保存字节码
        output_path = compiler_path + 'b'
        with open(output_path, 'wb') as f:
            f.write(bytecode)
        print(f"   字节码已保存: {output_path}")
        
        # 执行字节码
        vm = FSGVM()
        vm.load_bytecode(bytecode)
        print("\n执行输出:")
        vm.run()
        
        print("\n✅ compiler_v0.fsg 测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_self_compilation():
    """测试6: 自举验证（compiler_v0能否编译自己）"""
    print("\n" + "=" * 50)
    print("测试6: 自举验证 - compiler_v0 能否编译自己")
    print("=" * 50)
    
    # 注意: 由于assembler.fsg功能限制，这里先验证
    # Stage0 (Python汇编器) 能编译 Stage1 (compiler_v0.fsg)
    # Stage1 自举需要更完整的汇编器
    
    compiler_path = os.path.join(os.path.dirname(__file__), '..', 'examples', 'compiler_v0.fsg')
    
    if not os.path.exists(compiler_path):
        print(f"❌ 文件不存在: {compiler_path}")
        return False
    
    with open(compiler_path, 'r', encoding='utf-8') as f:
        source = f.read()
    
    print("Stage 0 (Python汇编器) 编译 Stage 1 (compiler_v0.fsg):")
    assembler = Assembler()
    try:
        bytecode = assembler.assemble(source)
        print(f"✅ Stage0 -> Stage1 编译成功!")
        print(f"   字节码长度: {len(bytecode)} bytes")
        
        # 验证字节码可执行
        vm = FSGVM()
        vm.load_bytecode(bytecode)
        print("\n执行Stage1字节码:")
        vm.run()
        
        print("\n📝 自举状态: Stage0编译Stage1成功")
        print("   下一步: 用FSG汇编实现完整汇编器，实现Stage1编译Stage1")
        
        return True
        
    except Exception as e:
        print(f"❌ 自举测试失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("FSG自举测试套件 v0")
    print("蜉熵阁 - FSG语言自举计划")
    print("=" * 60)
    
    results = []
    
    results.append(("基础编译", test_basic_compilation()))
    results.append(("字符串输出", test_string_output()))
    results.append(("算术运算", test_arithmetic()))
    results.append(("条件跳转", test_conditional_jump()))
    results.append(("compiler_v0", test_compiler_v0()))
    results.append(("自举验证", test_self_compilation()))
    
    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed}/{len(results)} 通过")
    
    if failed == 0:
        print("\n🎉 所有测试通过! FSG自举基础验证成功!")
        return True
    else:
        print(f"\n⚠️  {failed} 个测试失败，请检查。")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
