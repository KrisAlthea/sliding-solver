# Sliding Solver

## 项目介绍

经常玩 Microsoft Bing 的 [**拼图**](https://cn.bing.com/spotlight/imagepuzzle) , 每次点来点去耗费时间, 也没有啥技巧可言, 于是决定开发一款软件来自动求解, 顺便练习 Python 开发以及`PyQt5`的使用.

## 目录结构

```
SlidingSolver/
│
├── main.py               		# 主程序入口
├── game_logic.py         		# 游戏逻辑模块（棋盘生成和操作）
├── solver_c.c            		# C 求解器（A* 算法，高性能）
├── libsolver.so          		# C 求解器编译产物（需自行编译）
├── history/              		# 历史记录模块（数据模型、持久化、记录构建）
├── gui/                  		# GUI 相关模块
│   ├── __init__.py       		# 标记为 Python 包
│   ├── main_window.py    		# 主窗口的逻辑
│   ├── game_window.py    		# 游戏棋盘的视图
│   ├── history_window.py 		# 历史记录页面
│   ├── customize_dialog.py		# 自定义棋盘对话框
│   ├── select_size_dialog.py	# 选择棋盘大小对话框
│   └── utils.py          		# 界面工具函数
├── tests/                		# 单元测试
├── assets/               		# 静态资源（如图标、背景图片等）
│   ├── icon.png
│   └── styles.qss        		# 界面样式表
└── README.md             		# 项目说明文档
```

## 程序功能

1. 开始一局游戏
2. 自定义棋盘
3. 自动解答（支持 3×3、4×4、5×5）
4. 历史记录（本地 JSON 持久化）
5. 历史回放（可将历史终局棋盘加载回游戏页）

## 求解算法

项目包含两套求解实现：

### C 求解器（推荐）
- **A* 算法 + 曼哈顿距离 + 线性冲突启发式**
- 性能：3×3 < 1ms，4×4 < 200ms，5×5 < 10ms
- 支持最多 16M 状态（足够解绝大多数 4×4 和 5×5 布局）
- 编译：`gcc -O2 -shared -fPIC -o libsolver.so solver_c.c`

### Python fallback
- 3×3 / 4×4: A* + 线性冲突
- 5×5: IDA* + 节点限制（超限时返回空）
- 当 C 求解器不可用时自动使用

## 运行与测试

```bash
# 编译 C 求解器（必须）
gcc -O2 -shared -fPIC -o libsolver.so solver_c.c

# 运行程序
python main.py

# 运行全部测试
python -m pytest -q

# 运行单个测试
python -m pytest tests/test_game_logic.py::test_solve_returns_valid_moves_that_reach_goal_state -q
```

## 历史记录说明

- 历史记录默认写入 `data/history.json`。
- 每条记录包含：棋盘大小、初始/终局棋盘、步数、耗时、完成时间、来源。
- 在主菜单进入 `History` 页面后，可查看记录详情并执行回放。
