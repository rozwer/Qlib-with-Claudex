# Planner Subagent

Subagent responsible for hypothesis generation and experiment design in the Factor RD loop.
Invoked via the Agent tool with `subagent_type=Explore`.

## Role

Receives a TraceView (compressed summary of past experiments) and generates a new factor hypothesis and experiment specification.

## Input

Passed as a prompt when calling the Agent tool:

- **TraceView JSON**: SOTA metrics, recent experiment results, list of failed hypotheses
- **Scenario**: Column list (open, close, high, low, volume, vwap)
- **data_quality**: Availability of each column (`usable_columns` list). Columns with high missing rates have `usable=false`
- **Round index**: Current round number
- **Artifact path**: Output directory

## Output Files

Written directly by the subagent:

1. `round_<N>/hypothesis.json` — Hypothesis definition (see qlib-hypothesis-gen.md for schema)
2. `round_<N>/experiment.json` — Experiment specification (factor_name, formulation, variables)

## Constraints

- Do not repeat previously failed hypotheses (failed_hypotheses_summary in TraceView)
- factor_name must be a valid Python identifier `[a-z][a-z0-9_]*`
- Only propose formulas without look-ahead bias
- Do not propose hypotheses that depend on columns marked `usable=false` in `data_quality`
- Output must be valid JSON

## Invocation Pattern

```
Agent tool:
  prompt: |
    You are the Planner subagent.
    Analyze the following TraceView and propose a new factor hypothesis.

    TraceView: {trace_view_json}
    Usable columns (have real data): {usable_columns}
    Unusable columns: {unusable_columns} (high missing rate, usage prohibited)
    Output directory: {artifact_dir}/round_{N}/

    Write hypothesis.json and experiment.json using the Write tool.
    Follow the schema defined in .claude/skills/qlib-hypothesis-gen.md.
    Do not propose hypotheses that depend on unusable columns.
```
