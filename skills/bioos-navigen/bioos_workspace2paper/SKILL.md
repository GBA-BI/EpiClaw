---
name: bioos_workspace2paper
description: Outline and draft a scientific manuscript based on analysis results from a Bio-OS workspace. Trigger when user says "Write a paper from my results".
---

# Bio-OS Workspace2Paper

## 0. Runtime (OpenClaw vs Cursor)

`list_files_from_workspace` / `download_files_from_workspace` 仅在 OpenClaw 插件中存在。在 **Cursor** 中用终端执行 `bioos file list` / `bioos file download`，见 [`CURSOR_RUNTIME.md`](../CURSOR_RUNTIME.md)。

## 1. Operating Principle
This procedure defines how to outline and draft a scientific manuscript describing computational workflows executed on Bio-OS workspaces.

## Execution Workflow (The SOP)

### 【Stage 1】Prerequisite Setup
To write a paper, workspace data must first be extracted.
1. **Metadata Extraction**: Explicitly declare that the **`bioos_workspace_parser`** skill is required to process the target workspace name. This will load the parser instructions into context. Follow those instructions to obtain a clean, structured manifest of the Workflows, Datasets, and Run Histories.
2. **Context Enrichment (File Fetching)**:
   * After parsing the workspace layout, you must use **`list_files_from_workspace`** (plugin) **or** `bioos file list --workspace-name … --output json` (Cursor terminal; see **Section 0**) to retrieve the file hierarchy within the workspace's bounded bucket.
   * Review the returned list and compile a target list of **text-based context files** that you think will help you understand the analysis performed in the workspace. You MUST target summaries (e.g., `__dashboard__.md`), logs, config files, or small CSV reports.
   * **CRITICAL CONSTRAINT**: Do NOT target large binary omics files (e.g., `.bam`, `.fastq.gz`, `.vcf.gz`, `.h5ad`). Do NOT target exceptionally large files.
   * Use **`download_files_from_workspace`** (plugin) **or** `bioos file download … --output json` (Cursor terminal) to pull your selected target list from the cloud directly into the local agent environment. Read these downloaded files to drastically improve your comprehension of the analysis performed in the workspace.

### 【Stage 2】Structure and Outline Generation
1. **Propose Structure**: Offer a standard format (Abstract, Intro, Methods, Results, Discussion).
2. **Detailed Outline**: Map the parsed Workflows into the "Methods" section, and the Output Datasets into the "Results" section. Ask the user for approval.

### 【Stage 3】Iterative Content Drafting
Draft the paper section-by-section using the parsed workspace profile metadata.
1. **Methods**: Translate WDL tasks, Docker images, and specific tools identified by the Parser into academic Methods text.
2. **Results**: Summarize the output files (e.g., "DESeq2 identified X genes"). Do NOT invent scientific significance.
3. **Intro/Discussion**: Guide the user to provide the biological narrative. Act merely as their scribe to refine their thoughts into formal language.

### 【Stage 4】Final Manuscript Assembly
1. **Combine**: Assemble all approved sections.
2. **Export**: Save the complete text to `manuscript_draft.md`.
3. **Conclude**: Inform the user the drafting session is complete.
