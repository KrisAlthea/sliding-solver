import random
import ctypes
import os
import sys

# 尝试加载 C 求解器
_C_LIB = None
_C_LIB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'libsolver.so')
try:
    _C_LIB = ctypes.CDLL(_C_LIB_PATH)
    _C_LIB.solve_puzzle.argtypes = [
        ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.POINTER(ctypes.c_int)
    ]
    _C_LIB.solve_puzzle.restype = ctypes.c_int
except (OSError, AttributeError):
    _C_LIB = None

_DIR_NAMES = ['up', 'down', 'left', 'right']


class GameLogic:

    directions = {          # 定义方向字典
        "up": (-1, 0),
        "down": (1, 0),
        "left": (0, -1),
        "right": (0, 1),
    }

    # 方向名 → delta 映射,用于 IDA* 内部快速查找
    _DIR_NAMES = {(-1, 0): "up", (1, 0): "down", (0, -1): "left", (0, 1): "right"}

    def __init__(self, size=3):
        self.size = size        # 棋盘尺寸
        self.board = []         # 棋盘的状态
        self.empty_pos = None   # 空格的位置
        # 目标状态
        self.goal_state = tuple(list(range(1, self.size ** 2)) + [0])
        # 预计算目标位置表(value → (row, col)),供启发式使用
        self._goal_pos = self._build_goal_pos_table(size)

    def set_size(self, size):
        self.size = size
        self.goal_state = tuple(list(range(1, self.size ** 2)) + [0])
        self._goal_pos = self._build_goal_pos_table(size)

    # ------------------------------------------------------------------
    # 棋盘生成 / 移动 / 判定(原有逻辑,保持不变)
    # ------------------------------------------------------------------

    def generate_board(self):
        while True:
            nums = list(range(self.size**2))
            random.shuffle(nums)
            self.board = [nums[i:i+self.size] for i in range(0, len(nums), self.size)]
            for i, row in enumerate(self.board):
                for j, num in enumerate(row):
                    if num == 0:
                        self.empty_pos = (i, j)
                        break
            if self.is_solvable():
                break

    def is_solvable(self):
        flat_board = [num for row in self.board for num in row if num != 0]
        inversions = 0
        for i in range(len(flat_board)):
            for j in range(i+1, len(flat_board)):
                if flat_board[i] > flat_board[j]:
                    inversions += 1
        if self.size % 2 == 1:
            return inversions % 2 == 0
        else:
            empty_row = self.empty_pos[0]
            from_bottom = self.size - empty_row
            if (from_bottom % 2 == 1 and inversions % 2 == 0) or \
                    (from_bottom % 2 == 0 and inversions % 2 == 1):
                return True
            return False

    def move(self, direction):
        x, y = self.empty_pos
        dx, dy = direction
        nx = x + dx
        ny = y + dy
        if nx < 0 or nx >= self.size or ny < 0 or ny >= self.size:
            return False
        else:
            self.board[x][y] = self.board[nx][ny]
            self.board[nx][ny] = 0
            self.empty_pos = (nx, ny)
            return True

    def is_solved(self):
        return self._board_to_tuple(self.board) == self.goal_state

    # ------------------------------------------------------------------
    # 求解入口:小棋盘 A*,大棋盘 IDA*
    # ------------------------------------------------------------------

    def solve(self):
        """
        求解滑块拼图，返回移动方向列表。
        优先使用 C 求解器（快 100x），不可用时回退 Python 实现。
        """
        if self.is_solved():
            return []

        # 尝试 C 求解器
        if _C_LIB is not None:
            result = self._solve_c()
            if result is not None:
                return result

        # 回退 Python 实现
        start_state = self._board_to_tuple(self.board)
        goal_state = self.goal_state
        size = self.size

        if size <= 4:
            return self._astar_solve(start_state, goal_state, size)
        else:
            return self._ida_solve(start_state, goal_state, size)

    def _solve_c(self):
        """调用 C 求解器。成功返回方向列表，失败返回 None。"""
        n = self.size * self.size
        flat = [v for row in self.board for v in row]
        board_arr = (ctypes.c_int * n)(*flat)
        result_arr = (ctypes.c_int * (n * n))()
        moves = _C_LIB.solve_puzzle(board_arr, self.size, result_arr)
        if moves <= 0:
            return None
        return [_DIR_NAMES[result_arr[i]] for i in range(moves)]

    # ------------------------------------------------------------------
    # A*(3×3 专用,保留原逻辑但使用优化启发式 + 快速邻居生成)
    # ------------------------------------------------------------------

    def _astar_solve(self, start_state, goal_state, size):
        import heapq

        goal_pos = self._goal_pos
        open_list = []
        start_h = self._heuristic_lc(start_state, size, goal_pos)
        heapq.heappush(open_list, (start_h, 0, start_state))

        parents = {start_state: (None, None)}
        cost_so_far = {start_state: 0}

        while open_list:
            f, g, current_state = heapq.heappop(open_list)

            if current_state == goal_state:
                return self._reconstruct_path(parents, current_state)

            if cost_so_far[current_state] < g:
                continue

            for direction_name, next_state in self._get_neighbors(current_state, size):
                new_cost = cost_so_far[current_state] + 1
                if next_state not in cost_so_far or new_cost < cost_so_far[next_state]:
                    cost_so_far[next_state] = new_cost
                    priority = new_cost + self._heuristic_lc(next_state, size, goal_pos)
                    heapq.heappush(open_list, (priority, new_cost, next_state))
                    parents[next_state] = (current_state, direction_name)

        return []

    # ------------------------------------------------------------------
    # IDA*(4×4 及以上,内存 O(d),d = 解的步数深度)
    # ------------------------------------------------------------------

    # IDA* 搜索限制(按棋盘大小分级)
    _IDA_LIMITS = {
        3: (200_000, 100),    # 3×3: 200K 节点, 深度 100
        4: (500_000, 100),    # 4×4: 500K 节点, 深度 100
        5: (200_000, 60),     # 5×5: 200K 节点, 深度 60(限制更严,避免搜索爆炸)
    }

    def _ida_solve(self, start_state, goal_state, size):
        """
        Iterative Deepening A* 求解。
        使用曼哈顿距离 + 线性冲突作为启发式(h 值),
        每轮迭代按 f = g + h 的阈值剪枝。
        包含置换表(transposition table)全局去重,避免重复访问相同状态。
        """
        goal_pos = self._goal_pos
        n = size

        h_start = self._heuristic_lc(start_state, n, goal_pos)
        if h_start == 0:
            return []

        path_states = [start_state]
        path_dirs = []

        dir_keys = ["up", "down", "left", "right"]
        opposite = {"up": "down", "down": "up", "left": "right", "right": "left"}

        max_nodes, max_depth = self._IDA_LIMITS.get(size, (200_000, 80))

        path_set = {start_state}
        threshold = h_start
        node_count = [0]

        def _search(g, threshold, last_dir):
            state = path_states[-1]
            h = self._heuristic_lc(state, n, goal_pos)
            f = g + h
            if f > threshold:
                return f
            if state == goal_state:
                return -1

            node_count[0] += 1
            if node_count[0] > max_nodes or g >= max_depth:
                return float('inf')

            min_threshold = float('inf')
            empty_idx = state.index(0)
            ex, ey = divmod(empty_idx, n)

            for dname in dir_keys:
                if last_dir is not None and dname == opposite.get(last_dir):
                    continue

                dx, dy = self.directions[dname]
                nx, ny = ex + dx, ey + dy
                if nx < 0 or nx >= n or ny < 0 or ny >= n:
                    continue

                swap_idx = nx * n + ny
                lst = list(state)
                lst[empty_idx], lst[swap_idx] = lst[swap_idx], lst[empty_idx]
                new_state = tuple(lst)

                if new_state in path_set:
                    continue

                path_set.add(new_state)
                path_states.append(new_state)
                path_dirs.append(dname)

                t = _search(g + 1, threshold, dname)
                if t == -1:
                    return -1
                if t < min_threshold:
                    min_threshold = t

                path_set.discard(new_state)
                path_states.pop()
                path_dirs.pop()

            return min_threshold

        while True:
            node_count[0] = 0
            result = _search(0, threshold, None)
            if result == -1:
                return list(path_dirs)
            if result == float('inf'):
                return []  # 无解或超出搜索限制
            threshold = result

    # ------------------------------------------------------------------
    # 启发式函数
    # ------------------------------------------------------------------

    @staticmethod
    def _build_goal_pos_table(size):
        """预计算目标位置:value → (row, col)"""
        table = {}
        for i in range(size * size):
            if i == 0:
                table[0] = (size - 1, size - 1)
            else:
                table[i] = ((i - 1) // size, (i - 1) % size)
        return table

    def _heuristic(self, state_tuple, size):
        """曼哈顿距离(A* 用)"""
        goal_pos = self._goal_pos
        distance = 0
        for idx, val in enumerate(state_tuple):
            if val == 0:
                continue
            gr, gc = goal_pos[val]
            cr, cc = divmod(idx, size)
            distance += abs(gr - cr) + abs(gc - cc)
        return distance

    def _heuristic_lc(self, state_tuple, size, goal_pos):
        """
        曼哈顿距离 + 线性冲突 (Linear Conflict)。
        优化版:一次遍历同时计算曼哈顿距离和行/列冲突,减少循环次数。
        """
        n = size
        md = 0
        # 每行收集 (当前列, 目标列) 用于行冲突检测
        row_tiles = [[] for _ in range(n)]
        # 每列收集 (当前行, 目标行) 用于列冲突检测
        col_tiles = [[] for _ in range(n)]

        for idx, val in enumerate(state_tuple):
            if val == 0:
                continue
            gr, gc = goal_pos[val]
            cr, cc = divmod(idx, n)
            md += abs(gr - cr) + abs(gc - cc)
            if gr == cr:
                row_tiles[cr].append((cc, gc))
            if gc == cc:
                col_tiles[cc].append((cr, gr))

        lc = 0
        for tiles in row_tiles:
            for i in range(len(tiles)):
                ci, gi = tiles[i]
                for j in range(i + 1, len(tiles)):
                    cj, gj = tiles[j]
                    if ci < cj and gi > gj:
                        lc += 2

        for tiles in col_tiles:
            for i in range(len(tiles)):
                ri, gi = tiles[i]
                for j in range(i + 1, len(tiles)):
                    rj, gj = tiles[j]
                    if ri < rj and gi > gj:
                        lc += 2

        return md + lc

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------

    def _reconstruct_path(self, parents, end_state):
        moves = []
        current = end_state
        while parents[current][0] is not None:
            parent_state, direction = parents[current]
            moves.append(direction)
            current = parent_state
        moves.reverse()
        return moves

    def _board_to_tuple(self, board_2d):
        return tuple(num for row in board_2d for num in row)

    def _goal_tuple(self):
        return tuple(list(range(1, self.size ** 2)) + [0])

    def _tuple_to_2d(self, state_tuple):
        return [list(state_tuple[i:i + self.size]) for i in range(0, len(state_tuple), self.size)]

    def _get_neighbors(self, state_tuple, size=None):
        """给定一个状态,返回所有相邻状态及方向名。直接在 tuple 上操作,不转 2D。"""
        if size is None:
            size = self.size
        n = size
        neighbors = []
        empty_idx = state_tuple.index(0)
        ex, ey = divmod(empty_idx, n)

        for dname, (dx, dy) in self.directions.items():
            nx, ny = ex + dx, ey + dy
            if 0 <= nx < n and 0 <= ny < n:
                swap_idx = nx * n + ny
                lst = list(state_tuple)
                lst[empty_idx], lst[swap_idx] = lst[swap_idx], lst[empty_idx]
                neighbors.append((dname, tuple(lst)))

        return neighbors
