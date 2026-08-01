// ABOUTME: The completion remainder rule the web terminal applies to a match.
// ABOUTME: Inserting a whole match on top of a typed prefix produced "solsolve".

import { describe, expect, it } from 'vitest';

/** What to insert given the line already typed and the single match. */
export function remainderFor(typed: string, match: string): string {
  const lastWord = typed.endsWith(' ') ? '' : (typed.split(' ').pop() ?? '');
  return match.startsWith(lastWord) ? match.slice(lastWord.length) : match;
}

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
