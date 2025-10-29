import './styles.css';
import { GomokuGame, Player } from './game.js';
import { ensureLegalMove, findBestMove } from './ai.js';

const canvas = document.getElementById('board');
const statusText = document.getElementById('statusText');
const resultText = document.getElementById('resultText');
const modeSelect = document.getElementById('modeSelect');
const undoButton = document.getElementById('undoButton');
const restartButton = document.getElementById('restartButton');

const aiPlayer = Player.WHITE;
let game = new GomokuGame();
let aiEnabled = modeSelect.value === 'ai';
let pendingAi = null;

function formatPlayer(player) {
  return player === Player.BLACK ? 'Black' : 'White';
}

function clearPendingAi() {
  if (pendingAi) {
    clearTimeout(pendingAi);
    pendingAi = null;
  }
}

function queueAiMove() {
  if (!aiEnabled || game.isGameOver || game.currentPlayer !== aiPlayer) {
    return;
  }
  clearPendingAi();
  pendingAi = setTimeout(() => {
    pendingAi = null;
    if (!aiEnabled || game.isGameOver || game.currentPlayer !== aiPlayer) {
      return;
    }
    const move = findBestMove(game, aiPlayer);
    if (!ensureLegalMove(game, move)) {
      return;
    }
    game.placeStone(move.x, move.y);
    draw();
    updateStatus();
  }, 80);
}

function handleBoardPointer(event) {
  if (aiEnabled && game.currentPlayer === aiPlayer) {
    return;
  }
  if (game.isGameOver) {
    return;
  }

  const point = event.changedTouches ? event.changedTouches[0] : event;
  const rect = canvas.getBoundingClientRect();
  const relativeX = point.clientX - rect.left;
  const relativeY = point.clientY - rect.top;
  const cellSize = rect.width / game.size;

  const boardX = Math.floor(relativeX / cellSize);
  const boardY = Math.floor(relativeY / cellSize);

  if (boardX < 0 || boardX >= game.size || boardY < 0 || boardY >= game.size) {
    return;
  }

  try {
    game.placeStone(boardX, boardY);
  } catch (error) {
    return;
  }

  draw();
  updateStatus();
  if (aiEnabled) {
    queueAiMove();
  }
}

function handleUndo() {
  if (!game.history.length) {
    return;
  }

  const steps = aiEnabled ? Math.min(2, game.history.length) : 1;
  game.undo(steps);
  clearPendingAi();
  draw();
  updateStatus();

  if (aiEnabled && game.currentPlayer === aiPlayer) {
    queueAiMove();
  }
}

function handleRestart() {
  game.restart();
  clearPendingAi();
  draw();
  updateStatus();

  if (aiEnabled && game.currentPlayer === aiPlayer) {
    queueAiMove();
  }
}

function handleModeChange() {
  aiEnabled = modeSelect.value === 'ai';
  clearPendingAi();
  updateStatus();

  if (aiEnabled && game.currentPlayer === aiPlayer && !game.isGameOver) {
    queueAiMove();
  }
}

function resizeCanvas() {
  const displaySize = canvas.clientWidth;
  const dpr = window.devicePixelRatio || 1;

  if (displaySize === 0) {
    return;
  }

  if (canvas.width !== Math.floor(displaySize * dpr)) {
    canvas.width = Math.floor(displaySize * dpr);
    canvas.height = Math.floor(displaySize * dpr);
  }

  const context = canvas.getContext('2d');
  context.setTransform(dpr, 0, 0, dpr, 0, 0);
  draw();
}

function draw() {
  const ctx = canvas.getContext('2d');
  const size = canvas.clientWidth;
  const dpr = window.devicePixelRatio || 1;

  if (size === 0) {
    return;
  }

  if (canvas.width !== Math.floor(size * dpr) || canvas.height !== Math.floor(size * dpr)) {
    canvas.width = Math.floor(size * dpr);
    canvas.height = Math.floor(size * dpr);
  }

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, size, size);
  ctx.fillStyle = '#f5d6a1';
  ctx.fillRect(0, 0, size, size);

  const cellSize = size / game.size;

  ctx.strokeStyle = '#8c6239';
  ctx.lineWidth = 1;
  for (let i = 0; i <= game.size; i += 1) {
    const position = i * cellSize;
    ctx.beginPath();
    ctx.moveTo(0, position);
    ctx.lineTo(size, position);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(position, 0);
    ctx.lineTo(position, size);
    ctx.stroke();
  }

  drawStarPoints(ctx, cellSize);
  drawStones(ctx, cellSize);
  drawWinningLine(ctx, cellSize);
}

function drawStarPoints(ctx, cellSize) {
  if (game.size < 11) {
    return;
  }
  const points = [3, Math.floor(game.size / 2), game.size - 4];
  const uniquePoints = [...new Set(points)];
  ctx.fillStyle = '#6d4c41';

  for (const px of uniquePoints) {
    for (const py of uniquePoints) {
      const x = px * cellSize + cellSize / 2;
      const y = py * cellSize + cellSize / 2;
      ctx.beginPath();
      ctx.arc(x, y, Math.max(2, cellSize * 0.08), 0, Math.PI * 2);
      ctx.fill();
    }
  }
}

function drawStones(ctx, cellSize) {
  const lastMove = game.getLastMove();

  for (let y = 0; y < game.size; y += 1) {
    for (let x = 0; x < game.size; x += 1) {
      const cell = game.board[y][x];
      if (!cell) {
        continue;
      }

      const centerX = x * cellSize + cellSize / 2;
      const centerY = y * cellSize + cellSize / 2;
      const radius = cellSize * 0.42;

      const gradient = ctx.createRadialGradient(
        centerX - radius * 0.35,
        centerY - radius * 0.35,
        radius * 0.1,
        centerX,
        centerY,
        radius
      );

      if (cell === Player.BLACK) {
        gradient.addColorStop(0, '#4d4d4d');
        gradient.addColorStop(1, '#000000');
      } else {
        gradient.addColorStop(0, '#ffffff');
        gradient.addColorStop(1, '#d6d6d6');
      }

      ctx.beginPath();
      ctx.fillStyle = gradient;
      ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
      ctx.fill();

      if (lastMove && lastMove.x === x && lastMove.y === y) {
        ctx.beginPath();
        ctx.fillStyle = cell === Player.BLACK ? '#f4f4f4' : '#303030';
        ctx.arc(centerX, centerY, cellSize * 0.12, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }
}

function drawWinningLine(ctx, cellSize) {
  if (!game.winningLine || game.winningLine.length < 2) {
    return;
  }

  const first = game.winningLine[0];
  const last = game.winningLine[game.winningLine.length - 1];
  const startX = first.x * cellSize + cellSize / 2;
  const startY = first.y * cellSize + cellSize / 2;
  const endX = last.x * cellSize + cellSize / 2;
  const endY = last.y * cellSize + cellSize / 2;

  ctx.save();
  ctx.strokeStyle = '#d62828';
  ctx.lineWidth = Math.max(3, cellSize * 0.18);
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(startX, startY);
  ctx.lineTo(endX, endY);
  ctx.stroke();
  ctx.restore();
}

function updateStatus() {
  if (game.winner) {
    statusText.textContent = `${formatPlayer(game.winner)} wins!`;
    resultText.textContent = 'Game over. Tap restart to play again';
  } else if (game.isDraw) {
    statusText.textContent = 'Draw';
    resultText.textContent = 'No more legal moves. Tap restart to play again';
  } else {
    const player = formatPlayer(game.currentPlayer);
    const suffix = aiEnabled && game.currentPlayer === aiPlayer ? ' (AI)' : '';
    statusText.textContent = `${player} to move${suffix}`;
    resultText.textContent = '';
  }

  undoButton.disabled = !game.history.length;
}

canvas.addEventListener('click', handleBoardPointer);
canvas.addEventListener(
  'touchstart',
  (event) => {
    event.preventDefault();
    handleBoardPointer(event);
  },
  { passive: false }
);

undoButton.addEventListener('click', handleUndo);
restartButton.addEventListener('click', handleRestart);
modeSelect.addEventListener('change', handleModeChange);
window.addEventListener('resize', resizeCanvas);

resizeCanvas();
updateStatus();
if (aiEnabled && game.currentPlayer === aiPlayer) {
  queueAiMove();
}
