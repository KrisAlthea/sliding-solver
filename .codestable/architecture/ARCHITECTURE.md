# Sliding Solver 架构总入口

> 状态：骨架（待填充）
> 创建日期：2026-06-23

## 1. 项目简介

Bing 拼图（滑块拼图）自动求解器。PyQt5 GUI，支持 3×3 / 4×4 / 5×5 棋盘。

## 2. 核心概念 / 术语表

- **滑块拼图 (Sliding Puzzle)**：N×N 网格，N²-1 个编号方块 + 1 个空格，通过滑动方块还原到目标状态
- **A\***：启发式搜索算法，f(n) = g(n) + h(n)
- **IDA\***：迭代加深 A*，内存 O(d)
- **线性冲突 (Linear Conflict)**：曼哈顿距离的增强启发式，同行/列中目标方向相反的 tile 对额外 +2

## 3. 子系统 / 模块索引

| 模块 | 职责 |
|------|------|
| `game_logic.py` | 棋盘状态、移动、求解（Python fallback） |
| `solver_c.c` | C 高性能求解器（A* + 线性冲突） |
| `gui/` | PyQt5 界面（主窗口、棋盘、历史、对话框） |
| `history/` | 历史记录模型、持久化、构建 |
| `tests/` | 单元测试 |

## 4. 关键架构决定

- 求解器双实现：C 版优先（ctypes 调用），Python 版 fallback
- 棋盘状态用扁平 tuple 编码（row-major），便于哈希和比较
- 历史记录 JSON 文件持久化（`data/history.json`）

## 5. 已知约束 / 硬边界

- 5×5 随机布局可能超出搜索限制（16M 状态池上限）
- GUI 需要桌面环境（PyQt5），无头服务器只能跑测试
- C 求解器需手动编译（`gcc -O2 -shared -fPIC -o libsolver.so solver_c.c`）
