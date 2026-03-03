# jrob - 机器人OS学习项目

这是一个用于学习机器人操作系统的C++项目。

## 项目结构

```
jrob/
├── CMakeLists.txt    # CMake构建配置
├── README.md         # 本文件
├── .gitignore        # Git忽略规则
├── include/jrob/     # 头文件目录
├── src/              # 源文件目录
├── tests/            # 测试文件目录
└── examples/         # 示例程序目录
```

## 构建说明

项目使用 CMake 构建系统，要求 CMake 版本 3.16 或更高。

```bash
# 配置项目
cmake -B build

# 构建项目
cmake --build build
```

## 运行测试

构建完成后，运行测试：

```bash
./build/jrob_tests
```

## 运行示例

示例程序会自动构建为独立可执行文件：

```bash
# 如果有 example.cpp，则
./build/example
```

## 开发环境要求

- C++20 兼容的编译器
- CMake 3.16+

## 许可证

MIT License
