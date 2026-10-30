# AI contribution and authorship declaration

NeuroPyHLS is developed with help from an AI assistant. This file states openly what that assistant does, what it is responsible for, what stays with the human team, and how its contributions can be traced. It applies to the code, documentation, data products and research material in this repository.

## Who

- **Assistant:** Claude, a large language model made by Anthropic, used through Claude Code (the desktop app and CLI). The model version is recorded in the contribution log below. At the time of writing it was Claude Opus 5.5.
- **Directed by:** Manuel Monge (project lead, OpenIC). Every AI session is started, steered and reviewed by a named human.

## What the assistant is in charge of

The lead delegates these tasks to the assistant. Its output is a draft until a human reviews it.

| Area | Assistant's role |
|---|---|
| Repository setup | Proposes and implements the structure, packaging, tooling, CI workflows and contributor documents, following decisions made by the lead |
| Compiler code | Drafts frontend, IR, passes, backends and verification code, together with tests |
| Code analysis | Builds and maintains the code databases in `tools/code_db/`: static analysis of reference repositories such as SpikeInterface |
| Literature support | Searches, reads and extracts papers into structured tables (the lit-db); writes summaries and comparisons |
| Documentation | Drafts the docs pages, READMEs and explanations of results |
| Housekeeping | Writes commit messages and PR descriptions, and keeps this log up to date |

## What stays with the human team

- Research direction, scope and priorities.
- Architecture and design decisions. The assistant proposes options; the lead decides.
- Accepting results. This covers deciding whether a port meets its error/SNR threshold, whether a hardware number is credible, and whether a literature claim is correctly represented.
- Reviewing and merging every pull request, and every push to `main`.
- Publications, presentations and any claim made in the project's name.
- Licensing decisions and choices about third-party code.

## Authorship

- **The assistant is not an author.** It is not listed in `CITATION.cff` or as an author of papers, reports or theses that come from this project. Authors must be able to take responsibility for the work, and an AI system cannot.
- **People are accountable for what they commit.** A person who commits or merges AI-assisted work is responsible for it as if they had written it, including its correctness and licence compliance.
- **Licensing is unchanged.** AI-assisted contributions are released under the repository's licences: Apache-2.0 for code, CC-BY-4.0 for `docs/`.
- **Publications.** Papers and reports should describe AI assistance in their methods or acknowledgements, following the venue's policy (IEEE, for example, requires disclosure in the acknowledgements).

## How contributions are traced

1. **Commits:** a commit containing assistant-written content ends with the trailer
   `Co-Authored-By: Claude <model> <noreply@anthropic.com>`.
2. **Pull requests:** a PR opened by the assistant ends with a "Generated with Claude Code" line. A PR whose author used AI assistance says so in its description.
3. **Contribution log:** the table below records each significant piece of AI-assisted work.
4. **Docs pages:** pages written mainly by the assistant say so in a note at the bottom.

## Safeguards

- AI output can be wrong in plausible ways. Code is checked by tests, linting, type checking and verification against golden vectors. Literature extractions are spot-checked against the source PDFs.
- The assistant does not copy GPL-licensed code into the repository, and ports only from permissively licensed sources with attribution (see the README).
- The project has no private data. Do not paste credentials, personal data, or unpublished third-party data into AI tools.

## Rules for collaborators using AI tools

Investigators and students may use AI assistants, including Claude or any other tool, under the same rules:

- Disclose the use, with the commit trailer and a sentence in the PR description.
- Understand and review everything you submit.
- Never present AI-generated work as your own in assessed work (theses, coursework) unless your institution's policy allows it, and follow that policy's disclosure rules.

## Contribution log

| Date | Work | Model | Reviewed by |
|---|---|---|---|
| 2026-10-15 | Literature search on neural-signal processing and its hardware/FPGA implementations; 56 papers read in full and extracted into the lit-db tables | Claude (Claude Code) | M. Monge |
| 2026-10-15 | Code analyses of CNN-ripple, realtime_decoder, fooof, spikeinterface and ghostipy (architecture, algorithm paths, HLS porting notes) | Claude (Claude Code) | M. Monge |
| 2026-10-30 | Code-database tools (`tools/code_db/`): static AST extractor, SpikeInterface database, algorithm explorer page | Claude Opus 5.5 | M. Monge |
| 2026-10-30 | Repository setup: options proposed for each topic, decisions made by the lead; skeleton, tooling, CI, docs site and contributor documents implemented | Claude Opus 5.5 | M. Monge |
