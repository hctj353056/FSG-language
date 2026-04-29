# FSG 语言两层词表对照规范

> 版本: 1.0 | 2026-04-26
> 本文档定义 FSG 高级语言层与汇编层的词汇映射关系

---

## 一、高级自然语言层词表

### 1.1 关键字（Keyword）

```
声明    模块    引      定义    递归    流程
输入    输出    获取    使用    传入    得到
如      依次    调用    返回    若      则
否则    当      为      的      是      否
并且    或者    非      真      假      空
```

### 1.2 字面量（Literal）

```
字符串:     "..." （双引号，含 {变量} 插值）
字符:       'a'
整数:       123 | -456
浮点数:     3.14 | -0.5
布尔:       真 | 假
空值:       空 | null
标识符:     [中文|英文|数字|_]+ （首字符不能是数字）
```

### 1.3 操作符（Operator）

```
算术:   +   -   *   /   %   ^   //
比较:   =   ≠   >   <   ≥   ≤
逻辑:   且   或   非
赋值:   =   :=  得到
成员:   .   ::  @   $
```

### 1.4 分隔符（Delimiter）

```
冒号:       ：
分号:       ；
逗号:       ，
括号:       （ ）  【 】
中括号:     [ ]
大括号:     { }   （用于插值和代码块）
顿号:       、   （列表分隔）
引号:       " "  ' '
注释:       ；   （行注释）
```

### 1.5 预定义函数/流程

```
输入(提示语)        → 交互式输入
输出(内容)          → 打印/显示
获取(容器 元素个数) → len()
获取(容器 第N个)    → 列表索引
传入(参数)          → 函数调用传参
递归(描述)          → 循环或递归
```

---

## 二、汇编层词表

### 2.1 指令助记符（Mnemonic）

```
; 数据传输
LOAD    STORE   LOADIMM PUSH    POP     MOV

; 算术运算
ADD     SUB     MUL     DIV     NEG     MOD

; 比较与逻辑
CMP     AND     OR      XOR     NOT
SHL     SHR

; 控制流
JMP     JE      JNE     JG      JGE     JL      JLE
CALL    RET

; I/O
PRINT   INPUT   PRINTS

; 系统
HALT    NOP     SYSCALL DEBUG   INT
```

### 2.2 寄存器

```
通用:   R0  R1  R2  R3  R4  R5  R6  R7
特殊:   PC  SP  BP
```

### 2.3 伪指令（Directive）

```
.SECTION .text  .data  .rodata
.GLOBAL .EXTERN
.STR    .DW     .DB     .DATA   .ADDR   .ALIGN
.IF     .ELSE   .ENDIF
```

### 2.4 标识符与标签

```
标签定义:    identifier ':'
标签引用:    identifier
注释:        ';'+ 任意字符到行尾
```

### 2.5 操作数类型

```
立即数:      integer | hex | char
寄存器:      R0-R7 | PC | SP | BP
内存地址:    [register] | [address] | [label]
标签:        identifier
字符串:      ".STR content"
```

---

## 三、双向映射表

### 3.1 结构映射

| 高级层 | 汇编层 | 说明 |
|--------|--------|------|
| `声明：` | `.SECTION .data` | 元信息区域 |
| `引"path"` | `引` → LOAD/EXTERN | 模块引入 |
| `模块"名称"：` | `.GLOBAL name` | 函数/过程定义 |
| `定义"变量=[ ]"` | `.DATA` | 数据定义 |
| `流程"名称"：` | `name:` + 指令序列 | 函数体 |
| `递归"描述"` | 循环体 / CALL | 循环或递归 |
| `使用.模块名` | `CALL module` | 模块调用 |

### 3.2 运算映射

| 高级层 | 汇编层 | 说明 |
|--------|--------|------|
| `+` | `ADD` | 加法 |
| `-` | `SUB` | 减法 |
| `*` | `MUL` | 乘法 |
| `/` | `DIV` | 除法 |
| `%` | `MOD` | 取模 |
| `=` | `CMP` + `JE` | 比较跳转 |
| `≠` | `CMP` + `JNE` | 不等跳转 |
| `>` `<` `≥` `≤` | `CMP` + `JG/JL/JGE/JLE` | 有符号比较 |
| `且` | `AND` | 逻辑与 |
| `或` | `OR` | 逻辑或 |
| `非` | `NOT` | 逻辑非 |
| `依次` | 循环展开 | 遍历操作 |

### 3.3 I/O 映射

| 高级层 | 汇编层 | 说明 |
|--------|--------|------|
| `输入(提示)` | `PRINTS label` + `INPUT Rn` | 打印提示后读取 |
| `输出(内容)` | `PRINT Rn` 或 `PRINTS label` | 打印数值或字符串 |
| `获取列表[N]` | `LOAD Rn, [BP+offset]` | 内存寻址 |

### 3.4 控制流映射

| 高级层 | 汇编层 | 说明 |
|--------|--------|------|
| `若 条件 则 ...` | `CMP` + `JE/JNE label` | 条件分支 |
| `若 条件 则 ... 否则 ...` | `CMP` + `JE label1` + `JMP label2` | if-else |
| `当 条件 为真 重复` | `loop: CMP + JLE loop` | while 循环 |
| `递归"描述"` | `CALL function_name` | 函数调用 |

### 3.5 类型映射

| 高级层 | 汇编层 | 说明 |
|--------|--------|------|
| 整数 | 32位寄存器/内存 | int32 |
| 浮点数 | 暂无支持 | - |
| 布尔 | 0/1 整数 | bool |
| 字符 | 8位 ASCII | char |
| 字符串 | `.STR` + 内存区域 | string |
| 列表 | 连续内存块 + 长度 | array |

---

## 四、转换规则

### 4.1 高级 → 汇编 示例

```
高级层:
模块"求平均数"：
定义"列表1=[ ]"
流程"累加"：
输入列表1，依次取末尾位置元素相加得到A
；
获取列表1元素个数/A得到B
输出B

汇编层:
求平均数:
    ; R0 = 累加结果
    ; R1 = 元素个数
    ; R2 = 平均值 = R0 / R1
    CALL 流程_累加
    DIV R2, R0, R1
    PRINT R2
    HALT
```

### 4.2 词法冲突处理

```
高级层关键字冲突:
    不能用 "输出" "输入" "定义" 等作为变量名
    （与汇编层 RESERVED 不同，高级层通过空格/标点区分）

汇编层寄存器名冲突:
    不能用 R0-R7 作为高级层标识符
    不能用 PC/SP/BP 作为变量名
```

---

## 五、完整词表速查

### 高级层 → 汇编层

```
声明  →  元数据
引    →  LOAD / EXTERN
模块  →  .GLOBAL
定义  →  .DATA / .DW
流程  →  标签 + 指令序列
递归  →  循环体 / CALL
输入  →  PRINTS + INPUT
输出  →  PRINT / PRINTS
获取  →  LOAD / 地址计算
使用  →  CALL
得到  →  MOV / 寄存器赋值
依次  →  循环展开
若/则 →  CMP + 条件跳转
否则  →  JMP (else分支)
当    →  循环入口
```

### 汇编层 → 高级层

```
LOAD    →  获取/读取
STORE   →  保存/写入
LOADIMM →  赋值 立即数
PUSH/POP →  压栈/弹栈
MOV     →  得到/赋值
ADD/SUB/MUL/DIV →  算术运算
MOD     →  取模
CMP     →  比较
AND/OR/NOT →  逻辑运算
JMP/JE/JNE →  跳转/条件分支
CALL/RET →  调用/返回
PRINT   →  输出
INPUT   →  输入
PRINTS  →  输出字符串
HALT    →  结束
NOP     →  空操作
```

---

*本文档为 FSG 语言两层映射的基础定义*
*高级层词表由 001.fsg 示例反推，需随语言演进更新*


---

## 五、多语言类型映射表

### 5.1 Python 类型映射

| Python 类型 | FSG-IR 类型 | FSG-ASM | 说明 |
|------------|-------------|---------|------|
| `int` | `IRType.INT` | `.DW` | 32位整数 |
| `float` | `IRType.FLOAT` | `.DW` | 32位浮点 |
| `bool` | `IRType.BOOL` | `.DB` | 布尔（0/1） |
| `str` | `IRType.STRING` | `.DW` | 字符串指针 |
| `list` | `IRType.ARRAY` | `.DW[]` | 数组 |
| `dict` | `IRType.STRUCT` | `.DATA` | 结构体 |
| `None` | `IRType.VOID` | - | 空值 |

### 5.2 JavaScript 类型映射

| JavaScript 类型 | FSG-IR 类型 | FSG-ASM | 说明 |
|----------------|-------------|---------|------|
| `number` | `IRType.FLOAT` | `.DW` | JS number |
| `int` | `IRType.INT` | `.DW` | 显式整数 |
| `string` | `IRType.STRING` | `.DW` | 字符串指针 |
| `boolean` | `IRType.BOOL` | `.DB` | 布尔（0/1） |
| `object` | `IRType.STRUCT` | `.DATA` | 对象 |
| `array` | `IRType.ARRAY` | `.DW[]` | 数组 |
| `null` | `IRType.VOID` | - | 空值 |
| `undefined` | `IRType.VOID` | - | 未定义 |

### 5.3 Go 类型映射

| Go 类型 | FSG-IR 类型 | FSG-ASM | 说明 |
|--------|-------------|---------|------|
| `int` | `IRType.INT` | `.DW` | 平台相关整数 |
| `int8` | `IRType.INT` | `.DB` | 8位整数 |
| `int16` | `IRType.INT` | `.DW` | 16位整数 |
| `int32` | `IRType.INT` | `.DW` | 32位整数 |
| `int64` | `IRType.INT64` | `.DW` | 64位整数 |
| `float32` | `IRType.FLOAT` | `.DW` | 32位浮点 |
| `float64` | `IRType.DOUBLE` | `.DW` | 64位浮点 |
| `bool` | `IRType.BOOL` | `.DB` | 布尔 |
| `string` | `IRType.STRING` | `.DW` | 字符串指针 |
| `byte` | `IRType.CHAR` | `.DB` | 字节 |
| `rune` | `IRType.CHAR` | `.DB` | Unicode码点 |
| `struct` | `IRType.STRUCT` | `.DATA` | 结构体 |
| `slice` | `IRType.ARRAY` | `.DW[]` | 切片 |
| `array` | `IRType.ARRAY` | `.DW[]` | 数组 |

### 5.4 操作符映射表

| FSG-IR | Python | JavaScript | Go |
|--------|--------|------------|-----|
| `ADD` | `+` | `+` | `+` |
| `SUB` | `-` | `-` | `-` |
| `MUL` | `*` | `*` | `*` |
| `DIV` | `//` | `/` | `/` |
| `REM` | `%` | `%` | `%` |
| `AND` | `and` / `&` | `&&` / `&` | `&&` / `&` |
| `OR` | `or` / `\|` | `\|\|` / `\|` | `\|\|` / `\|` |
| `XOR` | `^` | `^` | `^` |
| `NOT` | `not` / `~` | `!` / `~` | `!` / `^` |

### 5.5 控制流映射表

| FSG-IR | Python | JavaScript | Go |
|--------|--------|------------|-----|
| `BR` | `goto` (无) | - | - |
| `COND_BR` | `if` | `if` / `?:` | `if` |
| `CALL` | `func()` | `func()` | `func()` |
| `RET` | `return` | `return` | `return` |

---

## 六、桥接器开发指南

### 6.1 桥接器架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  源语言源码  │ ──→ │  LanguageLower │ ──→ │   IRModule   │
│  (Python/JS/Go) │     │   (降级器)    │     │   (统一IR)   │
└─────────────┘     └─────────────┘     └───────┬─────┘
                                                │
                    ┌───────────────────────────┼───────────────────────────┐
                    │                           │                           │
                    ▼                           ▼                           ▼
            ┌───────────────┐           ┌───────────────┐           ┌───────────────┐
            │  ASMGenerator │           │  PythonGen    │           │  JSGenerator  │
            │ (FSG-ASM输出) │           │ (Python输出)  │           │ (JS输出)      │
            └───────────────┘           └───────────────┘           └───────────────┘
```

### 6.2 实现新的语言降级器

继承 `LanguageLower` 基类，实现以下方法：

```python
class NewLanguageLower(LanguageLower):
    """新语言降级器模板"""
    
    # 类型映射表
    TYPE_MAP = {
        'source_int': IRType.INT,
        'source_float': IRType.FLOAT,
        # ... 更多类型映射
    }
    
    def get_lang_name(self) -> str:
        """返回语言名称"""
        return "NewLanguage"
    
    def parse(self, source: str) -> IRModule:
        """解析源语言到 IR"""
        module = IRModule("newlang_module")
        
        # 1. 词法分析
        tokens = self._tokenize(source)
        
        # 2. 语法分析
        ast = self._parse(tokens)
        
        # 3. 语义降低到 IR
        for node in ast:
            ir_func = self._lower_node(node)
            module.add_func(ir_func)
        
        return module
    
    def _lower_node(self, node) -> IRFunction:
        """将语法树节点降级为 IR 函数"""
        ssa = SSAValueManager()
        func = IRFunction(...)
        
        # 实现具体的降低逻辑
        ...
        
        return func
```

### 6.3 实现新的目标生成器

```python
class NewTargetGenerator:
    """新目标代码生成器"""
    
    def generate(self, module: IRModule) -> str:
        """从 IR 生成目标代码"""
        lines = []
        
        for func in module.functions:
            lines.extend(self._gen_function(func))
        
        return "\n".join(lines)
    
    def _gen_function(self, func: IRFunction) -> List[str]:
        """生成函数"""
        lines = []
        
        for block in func.blocks:
            lines.extend(self._gen_block(block))
        
        return lines
    
    def _gen_block(self, block: IRBlock) -> List[str]:
        """生成基本块"""
        lines = []
        
        for inst in block.instructions:
            lines.extend(self._gen_instruction(inst))
        
        return lines
    
    def _gen_instruction(self, inst: IRInstruction) -> List[str]:
        """生成单条指令"""
        # 根据指令类型生成对应的目标代码
        ...
```

### 6.4 添加新的优化 Pass

```python
class MyOptimization:
    """自定义优化 Pass"""
    
    def run(self, module: IRModule) -> IRModule:
        """执行优化"""
        for func in module.functions:
            for block in func.blocks:
                self._optimize_block(block)
        return module
    
    def _optimize_block(self, block: IRBlock):
        """优化基本块"""
        i = 0
        while i < len(block.instructions):
            inst = block.instructions[i]
            
            # 分析和替换逻辑
            ...
            
            i += 1
```

### 6.5 使用优化器

```python
# 创建优化器并添加 Pass
optimizer = IROptimizer()
optimizer.passes.append(MyOptimization())

# 运行优化
optimized_module = optimizer.optimize(module)
```

### 6.6 测试指南

```python
def test_language_lower():
    """测试语言降级器"""
    
    # 测试源码
    source = '''
def add(a, b):
        return a + b
    '''
    
    # 降级到 IR
    lower = NewLanguageLower()
    module = lower.parse(source)
    
    # 验证 IR 结构
    assert len(module.functions) == 1
    assert module.functions[0].name == "add"
    assert len(module.functions[0].params) == 2
    
    # 生成目标代码
    gen = NewTargetGenerator()
    output = gen.generate(module)
    
    # 验证输出
    assert "add" in output
    
    print("✓ 测试通过")


def test_cross_language():
    """测试多语言互译"""
    
    sources = {
        "python": "def add(a, b):\\n    return a + b\\n",
        "javascript": "function add(a, b) { return a + b; }",
        "go": "func add(a int, b int) int { return a + b }",
    }
    
    lowers = {
        "python": PythonLower(),
        "javascript": JSLower(),
        "go": GoLower(),
    }
    
    # 所有语言降级到 IR
    modules = {}
    for lang, source in sources.items():
        modules[lang] = lowers[lang].parse(source)
    
    # 验证 IR 等价性（简化检查）
    for lang, module in modules.items():
        assert len(module.functions) == 1
        func = module.functions[0]
        assert len(func.blocks) >= 1
        assert any(
            str(IROpcode.ADD) in str(inst) 
            for inst in func.blocks[0].instructions
        )
    
    print("✓ 多语言互译测试通过")
```

### 6.7 性能考虑

1. **SSA 变量管理**：使用版本号快速追踪变量
2. **常量折叠**：在解析时立即计算常量表达式
3. **死代码消除**：两遍扫描，第一遍收集引用，第二遍删除
4. **指令合并**：将多个相关指令合并为单条复合指令

### 6.8 已知限制

- 当前版本不支持lambda/闭包
- 面向对象特性（类、继承）需扩展
- 异常处理模型尚未完善
- 垃圾回收机制依赖目标运行时
