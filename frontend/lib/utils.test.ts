import assert from 'node:assert';
import { test } from 'node:test';
import { cn } from './utils.ts';

test('cn handles basic strings', () => {
  assert.strictEqual(cn('px-2', 'py-2'), 'px-2 py-2');
});

test('cn handles conflicting tailwind classes', () => {
  assert.strictEqual(cn('p-2', 'p-4'), 'p-4');
});

test('cn handles conditional classes', () => {
  assert.strictEqual(cn('px-2', true && 'py-2', false && 'm-2'), 'px-2 py-2');
  assert.strictEqual(cn('px-2', { 'py-2': true, 'm-2': false }), 'px-2 py-2');
});

test('cn handles arrays', () => {
  assert.strictEqual(cn(['px-2', 'py-2']), 'px-2 py-2');
});

test('cn handles falsy values', () => {
  assert.strictEqual(cn('px-2', null, undefined, false, ''), 'px-2');
});

test('cn handles nested arrays and objects', () => {
  assert.strictEqual(cn('base', ['arr1', { obj1: true, obj2: false }], { obj3: true }), 'base arr1 obj1 obj3');
});
