# US-001 Local Project Setup

## Status

implemented

## Lane

normal

## Product Contract

The application must support local project setup via a CLI command. Running the command:
```bash
python main.py init
```
must create the required scaffolding files and directories if they do not exist:
- `.env.example`
- `config.yaml`
- `keywords.txt`
- `output/`
- `output/posts/`
- `output/Ảnh Trillion $ news/`
- `output/logs/`

## Relevant Product Docs

- [overview.md](file:///home/trung/Documents/2026/project/auto-trillion-news-post/docs/product/overview.md)

## Acceptance Criteria

- Running `python main.py init` creates all directories and default config files.
- Default `.env.example` must contain fields for `GEMINI_API_KEY`, `AI_PROVIDER`, `AI_MODEL` (defaulting to `gemini-1.5-flash`), and directory paths matching `overview.md`.
- Default `config.yaml` must contain configuration for keywords, search providers, fixed bottom hashtags, and platform rules.
- Default `keywords.txt` contains a seed list of search terms from `SPEC.md`.
- If files already exist, the command should log an informational message and not overwrite them.

## Design Notes

- **CLI entrypoint**: `main.py` using `argparse` or `click`/`typer`.
- **Config**: YAML file loaded via `PyYAML`.
- **Directories**: Handled safely via `os.makedirs` or `pathlib.Path.mkdir`.

## Validation

When updating durable proof status, use numeric booleans:
`scripts/bin/harness-cli story update --id US-001 --unit 1 --integration 1 --e2e 0 --platform 0`.

| Layer | Expected proof |
| --- | --- |
| Unit | Verify file creation logic and safe overwrite handling. |
| Integration | Run CLI command `python main.py init` and check existence of files/folders. |
| E2E | N/A |
| Platform | N/A |
| Release | N/A |

## Harness Delta

- Added E01 epic and US-001 story.

## Evidence

```bash
$ python3 -m unittest discover tests
Ran 2 tests in 0.001s
OK

$ scripts/bin/harness-cli story verify US-001
Story US-001 verification: pass
```
