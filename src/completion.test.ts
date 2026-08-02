// ABOUTME: Pins the client's mirror of the server line buffer against server.py.
// ABOUTME: Imports the shipped module; an earlier copy here tested nothing real.

import { describe, expect, it } from 'vitest';

import { LineMirror, remainderFor } from './completion';

describe('completion remainder', () => {
  it('inserts only the untyped tail of a command', () => {
    expect(remainderFor('sol', 'solve')).toBe('ve');
  });

  it('inserts nothing when the word is already complete', () => {
    expect(remainderFor('solve', 'solve')).toBe('');
  });

  it('inserts the whole word after a trailing space', () => {
    expect(remainderFor('solve ', 'pipeline_forwarding_intro'))
      .toBe('pipeline_forwarding_intro');
  });

  it('only considers the last word, not the whole line', () => {
    expect(remainderFor('take wid', 'widget_here')).toBe('get_here');
  });

  it('falls back to the whole match when it does not extend what was typed', () => {
    expect(remainderFor('xyz', 'scan')).toBe('scan');
  });

  it('handles an empty line', () => {
    expect(remainderFor('', 'look')).toBe('look');
  });
});

describe('LineMirror', () => {
  const feed = (...chunks: string[]) => {
    const mirror = new LineMirror();
    for (const chunk of chunks) mirror.push(chunk);
    return mirror;
  };

  it('accumulates ordinary typing', () => {
    expect(feed('l', 'o', 'o', 'k').value).toBe('look');
  });

  it('clears on Enter, because the server flushes the line', () => {
    expect(feed('look', '\r').value).toBe('');
  });

  it('erases one character on backspace', () => {
    expect(feed('lookx', '\x7f').value).toBe('look');
  });

  it('clears on Ctrl-C, because the server abandons the line', () => {
    // Left stale, the next Tab asked the server to complete text the server
    // had already discarded.
    expect(feed('sol', '\x03').value).toBe('');
  });

  it('splits a pasted chunk into characters instead of appending it whole', () => {
    // xterm delivers a paste as ONE event with newlines normalised to CR.
    // Comparing the chunk to '\r' fails, so the whole blob used to land in
    // the mirror, newline and all.
    expect(feed('look\rknowledge').value).toBe('knowledge');
  });

  it('keeps only the tail after a multi-line paste', () => {
    expect(feed('a\rb\rc').value).toBe('c');
  });

  it('drops an arrow key rather than typing its CSI bytes', () => {
    expect(feed('kn', '\x1b[A').value).toBe('kn');
  });

  it('drops an escape sequence delivered one byte per event', () => {
    expect(feed('k', '\x1b', '[', 'B', 'n').value).toBe('kn');
  });

  it('does not mistake the CSI opener for its terminator', () => {
    // '[' is inside the @-to-~ final-byte range, so a one-stage state machine
    // ended the sequence early and leaked the 'A'.
    expect(feed('\x1b[A').value).toBe('');
  });

  it('stops accepting input at the server cap', () => {
    const mirror = new LineMirror(8);
    mirror.push('x'.repeat(100));
    expect(mirror.value).toBe('xxxxxxxx');
  });

  it('records an accepted completion so the next Tab sees it', () => {
    const mirror = feed('sol');
    mirror.accept(remainderFor(mirror.value, 'solve'));
    expect(mirror.value).toBe('solve');
  });

  it('resets on demand, for a restarted game', () => {
    const mirror = feed('half typed');
    mirror.reset();
    expect(mirror.value).toBe('');
  });

  it('clears a half-read escape sequence on reset', () => {
    const mirror = feed('\x1b[');
    mirror.reset();
    mirror.push('A');
    expect(mirror.value).toBe('A');
  });
});
