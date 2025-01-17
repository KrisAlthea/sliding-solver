import random
import heapq

class GameLogic:

    directions = {          #定义方向字典
        "up": (-1, 0),
        "down": (1, 0),
        "left": (0, -1),
        "right": (0, 1),
    }

    def __init__(self, size=3):
        self.size = size        # 棋盘尺寸
        self.board = []         # 棋盘的状态
        self.empty_pos = None   # 空格的位置

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
        # 计算逆序数
        inversions = 0
        for i in range(len(flat_board)):
            for j in range(i+1, len(flat_board)):
                if flat_board[i] > flat_board[j]:
                    inversions += 1
        # 判断合法性
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
        # 超出范围
        if nx<0 or nx>=self.size or \
            ny<0 or ny>=self.size:
            return False
        else:
            self.board[x][y] = self.board[nx][ny]
            self.board[nx][ny] = 0
            self.empty_pos = (nx, ny)
            return True

    def shuffle_board(self, moves=100):
        for i in range(moves):
            direction = random.choice(list(GameLogic.directions.values()))
            self.move(direction)

    def is_solved(self):
        target = [[i * self.size + j + 1 for j in range(self.size)] for i in range(self.size)]
        target[-1][-1] = 0
        return self.board == target

    def solve(self):
        """
        使用 A* 搜索求解
        :return: moves列表
        """
        if self.is_solved():
            return []
        # 1) 获取当前起始状态与目标状态
        start_state = self._board_to_tuple(self.board)
        goal_state = self._goal_tuple()

        # 2) 用优先队列存储(f, g, state)
        #   f = g + h
        open_list = []
        start_h = self._heuristic(start_state)
        heapq.heappush(open_list, (start_h, 0, start_state))

        # 3) parents 和 cost_so_far
        parents = {start_state: (None, None)} # {状态: (父状态, "移动方向")}
        cost_so_far = {start_state: 0}        # 用来记录 g(n)

        # 4) 开始循环, 直到队列空 or 找到解
        while open_list:
            f, g, current_state = heapq.heappop(open_list)

            if current_state == goal_state:
                # 找到目标，回溯路径
                return self._reconstruct_path(parents, current_state)
                # 如果弹出的这个节点 f 超过了记录的 cost + heuristic，则说明它是陈旧的，可以忽略
            if cost_so_far[current_state] < g:
                continue

            # 扩展邻居
            for direction_name, next_state in self._get_neighbors(current_state):
                new_cost = cost_so_far[current_state] + 1
                # 如果是没见过的状态，或者找到更短路径
                if next_state not in cost_so_far or new_cost < cost_so_far[next_state]:
                    cost_so_far[next_state] = new_cost
                    priority = new_cost + self._heuristic(next_state)
                    heapq.heappush(open_list, (priority, new_cost, next_state))
                    parents[next_state] = (current_state, direction_name)

        # 没搜索到解就返回 None or []
        return None

    def _heuristic(self, state_tuple):
        """
        计算状态 state_tuple 的曼哈顿距离之和
        state_tuple 类似 (1,2,3,4,5,6,7,8,0)
        """
        distance = 0
        for index, value in enumerate(state_tuple):
            if value == 0:
                continue
            # 目标位置：假设数字 value 应该在 (target_x, target_y)
            # 注意: 数字 value 可能是 1 到 self.size**2 - 1
            # 行列大小 = self.size
            target_value = value - 1  # 因为数字 1 应该在 index=0 的地方
            target_x = target_value // self.size
            target_y = target_value % self.size

            # 当前数值所在的位置
            current_x = index // self.size
            current_y = index % self.size

            # 曼哈顿距离
            distance += abs(target_x - current_x) + abs(target_y - current_y)
        return distance

    def _reconstruct_path(self, parents, end_state):
        """
        A* 搜索完成后，从 end_state 回溯到初始状态。
        返回移动方向的列表 (如 ["up","left","down",...])。
        也可以在这里改写，让它返回状态序列，以便后续做动画演示。
        """
        moves = []
        current = end_state

        while parents[current][0] is not None:
            parent_state, direction = parents[current]
            moves.append(direction)
            current = parent_state
        moves.reverse()  # 因为我们是从终点回溯到起点，需反转
        return moves

    def _board_to_tuple(self, board_2d):
        """二维转扁平 tuple"""
        return tuple(num for row in board_2d for num in row)

    def _goal_tuple(self):
        """返回目标状态 (1,2,3,4,5,6,7,8,0)"""
        return tuple(list(range(1, self.size ** 2)) + [0])

    def _tuple_to_2d(self, state_tuple):
        """将扁平 tuple 转为二维 list"""
        board_2d = []
        for i in range(0, len(state_tuple), self.size):
            board_2d.append(list(state_tuple[i:i + self.size]))
        return board_2d

    def _get_neighbors(self, state_tuple):
        """
        给定一个状态，返回其所有相邻状态(四个可能移动)及对应的方向名字。
        """
        neighbors = []
        board_2d = self._tuple_to_2d(state_tuple)

        # 找到空格位置
        empty_x, empty_y = None, None
        for i in range(self.size):
            for j in range(self.size):
                if board_2d[i][j] == 0:
                    empty_x, empty_y = i, j
                    break
            if empty_x is not None:
                break

        # 遍历上下左右
        for direction_name, (dx, dy) in self.directions.items():
            nx, ny = empty_x + dx, empty_y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                new_board = [row[:] for row in board_2d]  # 深拷贝
                # 交换
                new_board[empty_x][empty_y], new_board[nx][ny] = new_board[nx][ny], new_board[empty_x][empty_y]
                new_state = self._board_to_tuple(new_board)
                neighbors.append((direction_name, new_state))

        return neighbors

    def solve_and_get_path(self):
        """
        1) 调用 self.solve() 获取到一串移动方向
        2) 根据这串移动方向，从当前状态一步步“模拟移动”，
           记录并返回所有中间状态(含开头和结尾)。
        """
        moves = self.solve()
        if not moves:
            return []

        # 先复制一份当前 board (避免直接改到原来的 self.board)
        import copy
        temp_game = copy.deepcopy(self)  # 复制整个 GameLogic 对象

        state_path = []
        # 把扁平 tuple 或直接 board 数组都行，这里假设返回二维列表
        state_path.append(copy.deepcopy(temp_game.board))

        # 根据 moves 逐步移动，记录每一步状态
        for move_dir in moves:
            temp_game.move(GameLogic.directions[move_dir])
            state_path.append(copy.deepcopy(temp_game.board))

        return state_path
