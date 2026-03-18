from models import Game, Value, StringMode, MoveValue
from typing import Optional

levels = {}
file_path = '/Users/dorischiang/Berk/gamescrafters_sp26/Sokoban/GamesmanPy/games/src/games/levels.txt'
def load_files(filename): 
        with open(filename) as f:
            current_level = None
            current_grid = []
    
            for line in f:
                line = line.rstrip()
                if line.startswith(';'):
                    if current_level is not None:
                        levels[current_level] = current_grid
                    current_level = line[2:].strip()
                    current_grid = []
                else:
                    if line=='':
                        continue
                    current_grid.append(line)
    
        if current_level is not None:
            levels[current_level] = current_grid
        
        return levels

load_files(file_path)

class Sokoban(Game):
    id = 'sokoban'
    variants = ["Level 1", "Level 2", "Level 3", "Level 4"]
    n_players = 1
    cyclic = True 
    
    def __init__(self, variant_id: str):
        if variant_id not in Sokoban.variants:
           raise ValueError(f"Variant not defined: {variant_id!r}")
        
        def get_static_board():
            """
            Returns a string with the positions of the static tiles in the starting board.
            """
            static_board = []
            for idx in range(self.rows*self.cols):
                if self.starting_board[idx] not in "@$":
                    static_board.append(self.starting_board[idx])
                else:
                    static_board.append(" ")
            return "".join(static_board)

        def get_dynamic_board():
            """
            Returns a bit string with the positions of the dynamic (box) tiles in the starting board.
            """
            dynamic_board = []
            for idx in range(self.rows*self.cols):
                if self.starting_board[idx] == "$":
                    dynamic_board.append("1")
                else:
                    dynamic_board.append("0")
            return "".join(dynamic_board)

        self.variant_id = variant_id
        self.rows = len(levels[variant_id])
        self.cols = len(levels[variant_id][0])
        self.starting_board = "".join(levels[variant_id])
        self.keybindings = {"w": -self.rows, "a": -1, "s": self.rows, "d": 1}
        self.readable_pieces = "@$. #"
        self.types_of_pieces = "01234"
        self.player_idx = self.starting_board.find("@")
        self.static_board = get_static_board()
        self.dynamic_board = get_dynamic_board()
        self.dxdy = [self.rows, 1, -self.rows, -1]
        

    def start(self):
        """"
        Returns the starting position of the game. 
        """
        return self.dynamic_board
    
    def check_bounds(self, idx, offset):
                if idx < 0 or idx >= self.rows *self.cols: 
                        return False
                if offset == 1 and idx % self.cols == self.cols - 1:  
                        return False
                if offset == -1 and idx % self.cols == 0:
                        return False 
                return True 

    def generate_moves(self, position) -> list[int]:
        """
        Returns a list of positions given the input position.
        """
        moves = []
        queue = set()
        visited = set() 

        queue.add((self.player_idx, position)) 
        
        while queue:
            player_idx, board = queue.pop()
            state = (player_idx, board)
            if state in visited:
                continue
            visited.add(state)

            for offset in self.dxdy:
                    new_player_idx = player_idx + offset

                    if not self.check_bounds(new_player_idx, offset):
                        continue 
                    
                    #check static board
                    if self.static_board[new_player_idx] == "#":
                        continue

                    #check dynamic board
                    if board[new_player_idx] == "0":
                        queue.add((new_player_idx, board))
                    elif board[new_player_idx] == "1":
                        new_box_idx = new_player_idx + offset
                
                        if not self.check_bounds(new_box_idx, offset):
                             continue

                        #check if a box can be pushed
                        if self.static_board[new_box_idx] == "#" or board[new_box_idx] == "1":
                            continue 

                        #push is valid: update dynamic board
                        new_board = list(board)
                        new_board[new_player_idx] = "0"
                        new_board[new_box_idx] = "1"
                        new_board_str = "".join(new_board)

                        queue.add((new_player_idx, new_board_str))
                        moves.append(new_board_str)

        return moves
                    
        
    def do_move(self, position, move: int):
        """
        Returns the resulting position of applying move to position.
        """
        new_pos = list(position)

        if position[move] == "1":
            offset = move-self.player_idx
            new_pos[move] = "0"
            new_pos[move + offset] = "1"
            
        self.player_idx = move
        return "".join(new_pos)

        
    def primitive(self, position) -> Optional[Value]:
        """
        Returns a Value enum which defines whether the current position is a win, loss, or non-terminal. 
        """
        for idx in range(self.rows*self.cols):
             if self.static_board[idx] == ".":
                  if position[idx] == "1":
                       return None
        return Value.Win
                  
    
    def to_string(self, position, mode = StringMode.Readable) -> str:
        """
        Returns a string representation of the position based on the given mode.
        """
        board = ''

        for idx in range(self.rows*self.cols):
            if self.static_board[idx] == "#":
                board += "#"
            elif self.static_board[idx] == ".":
                if position[idx] == "1":  
                    board += "*" #box on goal
                elif idx == self.player_idx:
                    board += "+"  #player on goal
                else:
                    board += "."
            elif self.static_board[idx] == " ":
                if position[idx] == "1":
                    board += "$"
                elif idx == self.player_idx:
                     board += "@"
                else:
                    board += " "

        return board
              
    def from_string(self, strposition: str):
        """
        Returns the position from a string representation of the position.
        Input string is StringMode.Readable.
        """
        position = []
        for idx in range(self.rows*self.cols):
            if strposition[idx] in "$*":
                position.append("1")
            else:
                position.append("0")
        return "".join(position)
    
    def move_to_string(self, move: int, mode: StringMode) -> str:
        """
        Returns a string representation of the move based on the given mode.
        """
        offset = move - self.player_idx
        return {-self.rows: "w", self.rows: "s", -1: "a", 1: "d"}.get(offset)
    
    def hash_ext(self, position):
        return int(position, base = 2)
    
    def generate_single_move(self, position):
        moves = []
        for offset in self.dxdy:
            new_player_idx = self.player_idx + offset

            if not self.check_bounds(new_player_idx, offset): 
                continue
                    
            if self.static_board[new_player_idx] == "#":
                continue

            if position[new_player_idx] == "1":
                new_box_idx = new_player_idx + offset

                if not self.check_bounds(new_box_idx, offset):
                     continue
                
                if self.static_board[new_box_idx] == "#" or position[new_box_idx] == "1":
                     continue
                
                moves.append(new_player_idx)

        return moves
   

    def resolve_move(self, position, move):
        offset = self.keybindings[move]
        return self.do_move(position, self.player_idx + offset)
    

    def print_board(self, board_str: str) -> None:
        """
        Prints a board string with a newline after each row.
        """
        for r in range(self.rows):
            start = r * self.cols
            end = start + self.cols
            print(board_str[start:end])
    