---
name: system-optimization
description: Performance, optimization, slow queries, indexes, pagination, caching, EXPLAIN, pg_trgm, hot paths. Use when optimizing runtime behavior, diagnosing slowness, or planning/measuring system performance improvements across backend, database, and frontend.
---

# System Optimization

Use this skill when the goal is to make the system faster without guessing.

Typical triggers:

- "optimiza el sistema"
- "esta lento"
- "hay que mejorar performance"
- "indexa la base"
- "agrega paginacion"
- "revisa queries lentas"
- "usa explain analyze"
- "hay demasiados registros"

## Goal

Improve performance through measured, reversible changes aligned with real bottlenecks.

## Core rules

1. Measure before optimizing.
2. Prefer the smallest high-impact fix first.
3. Optimize the true bottleneck, not the most visible layer.
4. Do not replace database work with Python work unless the data is already in memory and ordered.
5. Validate improvements with evidence.
6. Keep changes reversible and documented.

## Optimization order

### 1. Confirm the bottleneck

Classify the slowness first:

- database query time;
- too much data transferred;
- frontend rendering too many rows;
- repeated requests;
- missing indexes;
- expensive text search;
- N+1 queries;
- unnecessary recomputation.

Do not jump to indexing or caching before identifying which of these is actually happening.

### 2. Fix by layer

Use this order unless evidence says otherwise:

1. reduce result size;
2. add pagination;
3. improve query shape;
4. add or refine indexes;
5. remove redundant requests or duplicated computation;
6. add caching only when reads are repeated and staleness is acceptable.

## Database optimization checklist

When the bottleneck is PostgreSQL:

1. inspect the real query;
2. run `EXPLAIN (ANALYZE, BUFFERS)` when possible;
3. compare filters, joins, and sort columns to existing indexes;
4. prefer composite indexes for real query shapes;
5. use partial indexes for active/open/current states;
6. use `pg_trgm` for `%texto%` searches when volume justifies it;
7. avoid adding many low-value single-column indexes.

### Query-to-index mapping

For each proposed index, state explicitly:

- table;
- columns;
- whether it is partial;
- which query it accelerates;
- why an existing index does not already cover it.

### Avoid

- indexing every column blindly;
- indexing booleans alone;
- duplicating equivalent indexes;
- using Python loops to replace indexed SQL filters;
- adding GIN/trigram indexes without a real text-search path.

## Frontend optimization checklist

When the bottleneck is UI/data loading:

1. verify whether the page loads the entire dataset;
2. add backend pagination if missing;
3. make the frontend consume paginated endpoints;
4. reset page when filters change;
5. avoid large client-side filtering over full datasets;
6. keep search inputs debounced when needed.

## Backend/service optimization checklist

When the bottleneck is service code:

1. search for repeated queries inside loops;
2. collapse N+1 patterns;
3. prefetch related rows when justified;
4. avoid materializing large sets only to count or filter them in Python;
5. keep permission and tenant filters intact.

## Safe workflow

### 1. Reproduce

- identify the slow screen, endpoint, or command;
- confirm the current behavior with real data volume.

### 2. Inspect

- backend query path;
- frontend request pattern;
- current indexes;
- whether the dataset is paginated.

### 3. Change minimally

- one optimization slice at a time;
- do not mix unrelated refactors into a performance fix.

### 4. Validate

- typecheck and tests;
- if possible, compare timing or plan before/after;
- document what changed and why.

## Recommended outputs

When using this skill, produce:

1. bottleneck diagnosis;
2. chosen optimization slice;
3. exact files or migrations touched;
4. validation evidence;
5. next optimization candidates, only after the first slice is proven.

## Project-specific guidance

- For `Envases`, start with pagination and query shape before advanced caching.
- For `Jornadas`, prioritize `vehicle sessions`, `route operations`, `route incidents`, `load serials`, and `waybills`.
- For text search on large operational tables, consider `pg_trgm` only after confirming `%texto%` patterns.
- For `stock`, favor compound indexes aligned to `(tenant_id, warehouse_id, product_id)` and ledger order-by paths.
- For `crm` and `productos`, broad `ILIKE` search may need a second pass with trigram indexes once list pagination already exists.

## Definition of done

A performance change is done only when:

- the bottleneck is identified;
- the fix is implemented with minimal scope;
- validation passes;
- the change is documented;
- the result is measurably or structurally better than before.
