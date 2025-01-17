import random


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
        pass