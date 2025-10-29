import { getOpponent } from './game.js';

const DIRECTIONS = [
  { dx: 1, dy: 0 },
  { dx: 0, dy: 1 },
  { dx: 1, dy: 1 },
  { dx: 1, dy: -1 }
];

function isInside(board, x, y) {
  return y >= 0 && y < board.length && x >= 0 && x < board[y].length;
}

function hasNeighbour(board, x, y) {
  for (let dy = -1; dy <= 1; dy += 1) {
    for (let dx = -1; dx <= 1; dx += 1) {
      if (dx === 0 && dy === 0) {
        continue;
      }
      const nx = x + dx;
      const ny = y + dy;
      if (isInside(board, nx, ny) && board[ny][nx] !== null) {
        return true;
      }
    }
  }
  return false;
}

function analyseDirection(board, x, y, player, dx, dy) {
  let forward = 0;
  let nx = x + dx;
  let ny = y + dy;

  while (isInside(board, nx, ny) && board[ny][nx] === player) {
    forward += 1;
    nx += dx;
    ny += dy;
  }
  const forwardOpen = isInside(board, nx, ny) && board[ny][nx] === null;

  let backward = 0;
  nx = x - dx;
  ny = y - dy;
  while (isInside(board, nx, ny) && board[ny][nx] === player) {
    backward += 1;
    nx -= dx;
    ny -= dy;
  }
  const backwardOpen = isInside(board, nx, ny) && board[ny][nx] === null;

  return {
    length: forward + backward + 1,
    openEnds: (forwardOpen ? 1 : 0) + (backwardOpen ? 1 : 0)
  };
}

function scorePattern(length, openEnds) {
  if (length >= 5) {
    return 1_000_000;
  }

  if (length === 4) {
    return openEnds === 2 ? 100_000 : 50_000;
  }

  if (length === 3) {
    return openEnds === 2 ? 6_000 : 1_200;
  }

  if (length === 2) {
    return openEnds === 2 ? 500 : 120;
  }

  if (length === 1) {
    return openEnds === 2 ? 70 : 25;
  }

  return 5;
}

function evaluateMove(board, x, y, player) {
  const opponent = getOpponent(player);
  let attackScore = 0;
  let defenseScore = 0;
  let winningMove = false;
  let mustBlock = false;

  for (const { dx, dy } of DIRECTIONS) {
    const attack = analyseDirection(board, x, y, player, dx, dy);
    const defence = analyseDirection(board, x, y, opponent, dx, dy);

    attackScore += scorePattern(attack.length, attack.openEnds);
    defenseScore = Math.max(defenseScore, scorePattern(defence.length, defence.openEnds));

    if (attack.length >= 5) {
      winningMove = true;
    }
    if (defence.length >= 5) {
      mustBlock = true;
    }
  }

  if (winningMove) {
    return Number.POSITIVE_INFINITY;
  }

  if (mustBlock) {
    return 900_000 + defenseScore;
  }

  const center = (board.length - 1) / 2;
  const distance = Math.hypot(x - center, y - center);
  const centerBias = Math.max(0, 120 - distance * 14);
  const neighbourBonus = hasNeighbour(board, x, y) ? 100 : -150;

  return attackScore + defenseScore * 0.8 + centerBias + neighbourBonus;
}

export function findBestMove(game, player = game.currentPlayer) {
  const board = game.board;
  const size = game.size;

  if (game.history.length === 0) {
    const center = Math.floor(size / 2);
    return { x: center, y: center };
  }

  let bestScore = -Infinity;
  const bestMoves = [];

  for (let y = 0; y < size; y += 1) {
    for (let x = 0; x < size; x += 1) {
      if (board[y][x] !== null) {
        continue;
      }
      const score = evaluateMove(board, x, y, player);
      if (score > bestScore) {
        bestScore = score;
        bestMoves.length = 0;
        bestMoves.push({ x, y, score });
      } else if (score === bestScore) {
        bestMoves.push({ x, y, score });
      }
    }
  }

  if (!bestMoves.length) {
    return null;
  }

  const center = (size - 1) / 2;
  bestMoves.sort((a, b) => {
    const da = (a.x - center) ** 2 + (a.y - center) ** 2;
    const db = (b.x - center) ** 2 + (b.y - center) ** 2;
    return da - db;
  });

  const choice = bestMoves[0];
  return { x: choice.x, y: choice.y };
}

export function ensureLegalMove(game, move) {
  if (!move) {
    return false;
  }
  const { x, y } = move;
  return game.inBounds(x, y) && game.isCellEmpty(x, y);
}
