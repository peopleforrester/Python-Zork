// ABOUTME: Mirrors the server's line buffer so Tab can request completions.
// ABOUTME: Must track server.py's handle_input loop byte for byte, or Tab lies.

/**
 * A mirror of the line the server is buffering.
 *
 * The server owns the authoritative buffer; this reproduces it so a completion
 * request can name the prefix the player has typed. Every rule here exists
 * because the two disagreed:
 *
 *  - Ctrl-C clears the server's buffer, so it must clear this one.
 *  - A paste arrives as ONE multi-character event with newlines normalised to
 *    CR, so the chunk has to be walked per character rather than compared whole.
 *  - Escape sequences (arrow keys) are dropped by the server, so they are
 *    dropped here too.
 *  - The server stops accepting printable input at MAX_LINE.
 */
export class LineMirror {
  private line = '';
  private escape: 0 | 1 | 2 = 0;

  constructor(private readonly maxLine = 1024) {}

  get value(): string {
    return this.line;
  }

  reset(): void {
    this.line = '';
    this.escape = 0;
  }

  /** Feed one raw data chunk from xterm, exactly as the server would. */
  push(chunk: string): void {
    for (const ch of chunk) {
      if (this.escape === 1) {
        // "ESC [" opens a CSI sequence; anything else is a two-byte escape.
        this.escape = ch === '[' ? 2 : 0;
        continue;
      }
      if (this.escape === 2) {
        // CSI ends on a final byte in the @-~ range.
        if (ch >= '@' && ch <= '~') this.escape = 0;
        continue;
      }
      if (ch === '\x1b') {
        this.escape = 1;
      } else if (ch === '\r' || ch === '\n') {
        this.line = '';
      } else if (ch === '\x7f' || ch === '\b') {
        this.line = this.line.slice(0, -1);
      } else if (ch === '\x03') {
        // Ctrl-C abandons the line server-side; mirror that or Tab completes
        // against text the server no longer has.
        this.line = '';
      } else if (ch >= ' ' && this.line.length < this.maxLine) {
        this.line += ch;
      }
    }
  }

  /** Record a completion the server accepted, keeping the mirror in step. */
  accept(remainder: string): void {
    this.line += remainder;
  }
}

/**
 * What to insert given the line already typed and the single match.
 *
 * The server's buffer already holds the typed prefix, so only the tail may be
 * sent; sending the whole match produced "solsolve".
 */
export function remainderFor(typed: string, match: string): string {
  const lastWord = typed.endsWith(' ') ? '' : (typed.split(' ').pop() ?? '');
  return match.startsWith(lastWord) ? match.slice(lastWord.length) : match;
}
