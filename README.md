# Sliding Solver

## 项目介绍

经常能看到数字华容道这类游戏, 每次点来点去耗费时间, 也没有啥技巧可言, 于是决定开发一款软件来自动求解, 顺便联系python开发以及pyqt的使用.

## 目录结构

```
SlidingSolver/
│
├── main.py               # 主程序入口
├── game_logic.py         # 游戏逻辑模块（棋盘生成和操作）
├── solver.py             # 求解算法模块
├── gui/                  # GUI 相关模块
│   ├── __init__.py       # 标记为 Python 包
│   ├── main_window.py    # 主窗口的逻辑
│   ├── game_view.py      # 游戏棋盘的视图
│   └── utils.py          # 界面工具函数
├── assets/               # 静态资源（如图标、背景图片等）
│   ├── icon.png
│   └── styles.qss        # 界面样式表
└── README.md             # 项目说明文档
```

### 开发优先级建议

1. **`game_logic.py`** (核心逻辑模块)：
   - 编写棋盘生成和移动逻辑。
   - 这是整个项目的基础，GUI 和自动求解都需要依赖它。
2. **`main_window.py`** (GUI 主窗口)：
   - 创建 PyQt 的主窗口，并初始化界面。
   - 这部分可以在 `game_logic.py` 完成后立即开始。
3. **`game_view.py`** (棋盘视图)：
   - 基于 PyQt 的 QWidget，负责绘制棋盘和数字块。
   - 等基本功能稳定后，可以逐步实现美化和动画效果。
4. **`solver.py`** (求解算法模块)：
   - 编写自动求解算法，如 A* 或 BFS。
   - 可在核心逻辑和 GUI 基础上扩展。
5. **`main.py`** (程序入口)：
   - 最后整合各模块并启动程序。