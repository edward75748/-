import { describe, expect, it } from 'vitest';
import { GomokuGame, Player } from '../src/game.js';
import { ensureLegalMove, findBestMove } from '../src/ai.js';

describe('Gomoku AI', () => {
  it('plays in the centre on an empty board', () => {
    const game = new GomokuGame();
    const move = findBestMove(game, Player.BLACK);
    expect(move).toEqual({ x: 7, y: 7 });
    expect(ensureLegalMove(game, move)).toBe(true);
  });

  it('finds immediate winning moves', () => {
    const game = new GomokuGame();

    for (let i = 0; i < 4; i += 1) {
      game.placeStone(i, 0);
      game.placeStone(i, 1);
    }

    const move = findBestMove(game, game.currentPlayer);
    expect(move).toEqual({ x: 4, y: 0 });
    expect(() => game.placeStone(move.x, move.y)).not.toThrow();
    expect(game.winner).toBe(Player.BLACK);
  });

  it('blocks opponent five-in-a-row threats', () => {
    const game = new GomokuGame();
    const moves = [
      [Player.BLACK, 5, 5],
      [Player.WHITE, 0, 0],
      [Player.BLACK, 6, 5],
      [Player.WHITE, 1, 0],
      [Player.BLACK, 7, 5],
      [Player.WHITE, 2, 0],
      [Player.BLACK, 8, 5],
      [Player.WHITE, 3, 0]
    ];

    for (const [, x, y] of moves) {
      game.placeStone(x, y);
    }

    const move = findBestMove(game, Player.BLACK);
    expect(move).toEqual({ x: 4, y: 0 });
    expect(ensureLegalMove(game, move)).toBe(true);
    expect(() => game.placeStone(move.x, move.y)).not.toThrow();
    expect(game.board[0][4]).toBe(Player.BLACK);
  });
});
