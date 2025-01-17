# Sliding Solver

## 项目介绍

经常玩 Microsoft Bing 的 [**拼图**](https://cn.bing.com/spotlight/imagepuzzle) , 每次点来点去耗费时间, 也没有啥技巧可言, 于是决定开发一款软件来自动求解, 顺便练习 Python 开发以及`PyQt5`的使用.

## 目录结构

```
SlidingSolver/
│
├── main.py               		# 主程序入口
├── game_logic.py         		# 游戏逻辑模块（棋盘生成和操作）
├── gui/                  		# GUI 相关模块
│   ├── __init__.py       		# 标记为 Python 包
│   ├── main_window.py    		# 主窗口的逻辑
│   ├── game_window.py    		# 游戏棋盘的视图
│   ├── customize_dialog.py		# 自定义棋盘对话框
│   ├── select_size_dialog.py	# 选择棋盘大小对话框
│   └── utils.py          		# 界面工具函数
├── assets/               		# 静态资源（如图标、背景图片等）
│   ├── icon.png
│   └── styles.qss        		# 界面样式表
└── README.md             		# 项目说明文档
```

## 程序功能

1. 开始一局游戏
2. 自定义棋盘
3. 自动解答
4. 历史记录...(待开发)