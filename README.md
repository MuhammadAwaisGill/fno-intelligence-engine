# D365 F&O Developer Intelligence Engine

A local, offline MCP (Model Context Protocol) server that grounds AI coding
assistants (Cursor, Claude Code, GitHub Copilot) on real Dynamics 365
Finance & Operations AOT metadata — so they stop hallucinating field names,
method signatures, and Chain of Command (CoC) wrappers when generating
X++ code.

**Status: early build, Part 1 (metadata ingestion) in progress. Not yet a
working MCP server.** See [Project Status](#project-status) below.

## The problem

D365 F&O stores its entire application model (tables, classes, forms,
extended data types) as XML under `PackagesLocalDirectory` — often
500,000+ objects per environment. AI coding assistants have never seen
this XML; they only know generic X++ syntax from training. Ask one to
extend a table or write a Chain of Command wrapper, and it will
confidently reference fields and methods that don't exist in your
environment. This isn't a prompting problem — the AI is missing data,
not instructions.

## The approach

1. **Ingestion** (this repo, in progress) — parse raw AxTable/AxClass XML
   into structured, correct JSON using `lxml`, with regex extraction for
   Chain of Command patterns embedded in X++ source text.
2. **Indexing** (planned) — load parsed metadata into SQLite + FTS5 for
   sub-10ms local lookups.
3. **Exposure** (planned) — expose the index to AI agents as MCP tools
   (`get_table_schema`, `find_coc_methods`, etc.) over stdio.
4. **Advanced modules** (planned) — a pattern-based X++ best-practices
   linter, then a cross-model dependency graph.

## What's actually built right now

- `schema/table_schema.json` — JSON Schema for parsed AxTable metadata,
  validated against a real `VendTrans` table export
- `schema/class_schema.json` — JSON Schema for parsed AxClass / Chain of
  Command metadata. **Not yet validated against a full real class file**
  (see file header for details)
- `parse_table.py` — working parser: AxTable XML → schema-conformant JSON
- `parse_class.py` — regex-based CoC extractor. **Written but not yet run
  against real class bytes** — treat every regex here as unproven
- `validate.py` — validates parser output against the JSON Schema

## Project status

This project is a work in progress, built as a learning exercise while
studying D365 F&O development. Some concrete facts worth stating plainly:

- **A mature, actively maintained open-source project already solves this
  problem at a larger scope**: [dynamics365ninja/d365fo-mcp-server](https://github.com/dynamics365ninja/d365fo-mcp-server)
  (26 MCP tools, live environment connection, form pattern engine, safe
  metadata writes via Microsoft's `IMetadataProvider`). This repo does not
  claim to improve on it or compete with it.
- This project differs in scope and design, not necessarily in quality:
  Python instead of TypeScript, read-only and built against static AOT
  XML exports rather than a live environment connection, and currently
  limited to the ingestion layer only.
- The value of this project, honestly stated, is in understanding the
  problem and the parsing/indexing approach deeply enough to explain the
  design decisions — not in being first or unique.

## Requirements

- Python 3.10+
- `lxml`
- `jsonschema` (for schema validation during development)

```bash
pip install lxml jsonschema
```

## Fixtures

Fixtures are AOT XML exports from a local, offline Hyper-V VM running
Microsoft's standard USMF/DAT demo data, plus a custom model built from
scratch with no third-party or organizational IP. See
`fixtures/tables/` and `fixtures/classes/` — populate these locally with
your own exports; they are not included in this template.

## License

MIT
