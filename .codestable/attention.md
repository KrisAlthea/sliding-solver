# Attention

本文件是 CodeStable 技能启动必读的项目注意事项入口。所有 CodeStable 子技能开始工作前必须读取它。

## 项目碎片知识

<!-- cs-note managed: 用 cs-note 维护，新条目按下面分节追加 -->

### 编译与构建

- C 求解器需手动编译：`gcc -O2 -shared -fPIC -o libsolver.so solver_c.c`
- 无 `requirements.txt`，依赖 PyQt5 + pytest

### 运行与本地起服务

- GUI 启动：`python main.py`（需要桌面环境 + PyQt5）

### 测试

- `python3 -m pytest tests/ -q`（13 个测试，0.06s）

### 命令与脚本陷阱

### 路径与目录约定

### 环境变量与凭证

### 其他

- 项目路径：`/root/projects/SlidingSolver/`
- GitHub：`KrisAlthea/sliding-solver`（public）
