import { describe, expect, it } from 'vitest';
import { GomokuGame, Player } from '../src/game.js';

describe('GomokuGame', () => {
  it('alternates players and prevents moves on occupied cells', () => {
    const game = new GomokuGame();

    const firstMove = game.placeStone(7, 7);
    expect(firstMove.player).toBeDefined();
    expect(game.currentPlayer).toBe(Player.WHITE);

    expect(() => game.placeStone(7, 7)).toThrowError(/occupied/);
  });

  it('detects horizontal wins', () => {
    const game = new GomokuGame();

    for (let i = 0; i < 4; i += 1) {
      game.placeStone(i, 0);
      game.placeStone(i, 1);
    }

    const result = game.placeStone(4, 0);
    expect(result.winner).toBe(Player.BLACK);
    expect(game.winner).toBe(Player.BLACK);
    expect(game.isGameOver).toBe(true);
    expect(game.winningLine).toHaveLength(5);
  });

  it('detects diagonal wins', () => {
    const game = new GomokuGame();

    for (let i = 0; i < 4; i += 1) {
      game.placeStone(i, i);
      game.placeStone(i, i + 1);
    }

    const result = game.placeStone(4, 4);
    expect(result.winner).toBe(Player.BLACK);
    expect(game.winningLine?.[0]).toEqual({ x: 0, y: 0 });
    expect(game.winningLine?.[4]).toEqual({ x: 4, y: 4 });
  });

  it('supports undo for multiple moves', () => {
    const game = new GomokuGame();
    game.placeStone(7, 7);
    game.placeStone(6, 7);
    game.placeStone(8, 7);
    expect(game.history).toHaveLength(3);
    expect(game.currentPlayer).toBe(Player.WHITE);

    const undone = game.undo(2);
    expect(undone).toHaveLength(2);
    expect(game.history).toHaveLength(1);
    expect(game.currentPlayer).toBe(Player.WHITE);
    expect(game.isGameOver).toBe(false);
  });

  it('supports restarting the game', () => {
    const game = new GomokuGame();
    game.placeStone(7, 7);
    game.placeStone(6, 7);
    game.restart();

    expect(game.history).toHaveLength(0);
    expect(game.currentPlayer).toBe(Player.BLACK);
    expect(game.isGameOver).toBe(false);
    expect(game.board.every((row) => row.every((cell) => cell === null))).toBe(true);
  });

  it('prevents moves once a winner is declared', () => {
    const game = new GomokuGame();

    for (let i = 0; i < 4; i += 1) {
      game.placeStone(i, 0);
      game.placeStone(i, 1);
    }

    game.placeStone(4, 0);
    expect(() => game.placeStone(5, 0)).toThrowError(/over/);
  });

  it('detects draws', () => {
    const size = 3;
    const game = new GomokuGame(size);
    const sequence = [
      [0, 0],
      [1, 0],
      [2, 0],
      [0, 1],
      [1, 1],
      [2, 1],
      [0, 2],
      [1, 2],
      [2, 2]
    ];

    for (const [x, y] of sequence) {
      if (!game.isGameOver) {
        game.placeStone(x, y);
      }
    }

    expect(game.isDraw).toBe(true);
    expect(game.winner).toBeNull();
  });
});
