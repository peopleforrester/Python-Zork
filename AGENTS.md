# Python Zork

Educational text-based adventure teaching computer architecture

**Stack**: Python, Node.js/TypeScript, React

## Commands

### Python

- **Install**: `uv sync --dev`
- **Test**: `uv run pytest`
- **Lint**: `uv run ruff check .`
- **Format**: `uv run ruff format .`
- **Type check**: `uv run mypy computerquest` (`src/` holds the React app and
  has no Python in it, so `mypy src/` errors out)

### Frontend

- **Install**: `npm install`
- **Dev**: `npm run dev`
- **Build**: `npm run build`
- **Test**: `npm test` (vitest)
- **E2E**: `npm run test:e2e` (Playwright, builds and serves first)

### Authoring and deploy

- **Validate puzzles**: `uv run python scripts/validate_puzzles.py`
  Prints every puzzle's canonical answer, which is computed at runtime and
  stored nowhere else, and reports unrunnable setups, header comments that no
  longer state the answer, and puzzles bound to no room.
- **Deploy**: `uv run python scripts/deploy.py` (refuses to call a deploy done
  until `/api/health` reports the uploaded commit)

## Live

- **Play / demo**: https://zork.michaelrishiforrester.com
- **Origin**: https://python-zork-production.up.railway.app (the custom domain
  is a CNAME to this; `scripts/deploy.py` verifies against the origin so a DNS
  problem can never look like a failed deploy)

## Adding a puzzle

Binding is a literal list, so a new YAML file alone is unreachable:

1. Write `computerquest/mechanics/puzzles/data/<category>/<id>.yaml`. The
   filename stem must equal the `id`, and `answer_kind` must match what the
   named simulator returns (the loader enforces both).
2. Add the id to `ComputerArchitecture.bind_puzzles` in
   `computerquest/world/architecture.py`. Max 3 per room.
3. Run the validator, put the printed canonical answer in a header comment,
   and check the prompt actually asks for that answer.
4. Add the answer to `tests/fixtures/golden_puzzle_answers.json`; a new puzzle
   without a pinned answer fails the suite by design.
