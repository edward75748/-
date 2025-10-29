export const BOARD_SIZE = 15;

export const Player = {
  BLACK: 'black',
  WHITE: 'white'
};

const DIRECTIONS = [
  { dx: 1, dy: 0 },
  { dx: 0, dy: 1 },
  { dx: 1, dy: 1 },
  { dx: 1, dy: -1 }
];

function createEmptyBoard(size) {
  return Array.from({ length: size }, () => Array.from({ length: size }, () => null));
}

export function getOpponent(player) {
  return player === Player.BLACK ? Player.WHITE : Player.BLACK;
}

export class GomokuGame {
  constructor(size = BOARD_SIZE) {
    this.size = size;
    this.board = createEmptyBoard(size);
    this.currentPlayer = Player.BLACK;
    this.history = [];
    this.winner = null;
    this.winningLine = null;
    this.isGameOver = false;
    this.isDraw = false;
  }

  inBounds(x, y) {
    return x >= 0 && x < this.size && y >= 0 && y < this.size;
  }

  isCellEmpty(x, y) {
    return this.board[y][x] === null;
  }

  getCell(x, y) {
    if (!this.inBounds(x, y)) {
      throw new Error('Cell out of bounds');
    }
    return this.board[y][x];
  }

  getLastMove() {
    if (!this.history.length) {
      return null;
    }
    return this.history[this.history.length - 1];
  }

  placeStone(x, y) {
    if (!this.inBounds(x, y)) {
      throw new Error('Move is outside of the board');
    }
    if (this.isGameOver) {
      throw new Error('Game is already over');
    }
    if (!this.isCellEmpty(x, y)) {
      throw new Error('Cell is already occupied');
    }

    const player = this.currentPlayer;
    this.board[y][x] = player;
    const move = { x, y, player };
    this.history.push(move);

    const winningLine = this.#checkWin(x, y, player);
    if (winningLine) {
      this.winner = player;
      this.winningLine = winningLine;
      this.isGameOver = true;
      this.isDraw = false;
      return { winner: player, winningLine };
    }

    if (this.history.length === this.size * this.size) {
      this.isGameOver = true;
      this.isDraw = true;
      return { draw: true };
    }

    this.currentPlayer = getOpponent(player);
    return { player };
  }

  undo(steps = 1) {
    const movesToUndo = Math.min(Math.max(steps, 0), this.history.length);
    if (movesToUndo === 0) {
      return [];
    }

    const undoneMoves = [];
    for (let i = 0; i < movesToUndo; i += 1) {
      const move = this.history.pop();
      if (!move) {
        break;
      }
      this.board[move.y][move.x] = null;
      undoneMoves.push(move);
    }

    if (this.history.length) {
      this.currentPlayer = getOpponent(this.history[this.history.length - 1].player);
    } else {
      this.currentPlayer = Player.BLACK;
    }

    this.winner = null;
    this.winningLine = null;
    this.isGameOver = false;
    this.isDraw = false;

    return undoneMoves;
  }

  restart() {
    this.board = createEmptyBoard(this.size);
    this.currentPlayer = Player.BLACK;
    this.history = [];
    this.winner = null;
    this.winningLine = null;
    this.isGameOver = false;
    this.isDraw = false;
  }

  #checkWin(x, y, player) {
    for (const { dx, dy } of DIRECTIONS) {
      const countPositive = this.#countInDirection(x, y, dx, dy, player);
      const countNegative = this.#countInDirection(x, y, -dx, -dy, player);
      const total = countPositive.count + countNegative.count + 1;

      if (total >= 5) {
        const startX = x - dx * countNegative.count;
        const startY = y - dy * countNegative.count;
        const line = [];
        for (let i = 0; i < total; i += 1) {
          line.push({ x: startX + dx * i, y: startY + dy * i });
        }
        return line;
      }
    }

    return null;
  }

  #countInDirection(x, y, dx, dy, player) {
    let count = 0;
    let currentX = x + dx;
    let currentY = y + dy;

    while (this.inBounds(currentX, currentY) && this.board[currentY][currentX] === player) {
      count += 1;
      currentX += dx;
      currentY += dy;
    }

    return { count };
  }
}
