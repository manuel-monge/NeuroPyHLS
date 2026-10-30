# Code databases

Relational databases of Python repositories, built by static AST analysis. The target code is never imported or executed.

| Repo | Commit | Output |
|---|---|---|
| SpikeInterface/spikeinterface | `e1edb1a` (2026-10-30) | `spikeinterface_code.sqlite` + `csv/*.csv` (kept in the project document store, not in git; rebuild into `out/code-db/`) |

Rebuild or run on another repo:

```bash
python3 -I tools/code_db/build_code_db.py <clone> spikeinterface out/code-db/spikeinterface --commit <sha>
```

The algorithm catalogue (`build_algorithms()` in the script) is repo-specific. Everything else is generic.

## Entity tables (one row per thing, with its characteristics)

| Table | Key | Characteristics |
|---|---|---|
| `algorithms` | `algorithm_id` = `<type>:<name>` | name, algorithm_type, subtype, entry_point (class/function), entry_kind, discovered_by (which registry / base class / curated), registry_key, module_id, docstring, own_lines, n_functions_reachable, libraries_own, uses_numba, uses_torch |
| `functions` | `function_id` (dotted path) | module, subpackage, class, kind (function/method/classmethod/staticmethod/property/nested/module-level code), is_public, lines, n_params, varargs/kwargs, decorators, is_numba_jit, is_generator, cyclomatic_complexity, max_nesting, n_internal_calls, n_library_calls, docstring |
| `classes` | `class_id` | bases, full internal MRO, n_methods, n_lines, is_dataclass, docstring |
| `modules` | `module_id` | path, subpackage, lines, code lines, docstring |
| `libraries` | `library_id` (import name) | pypi_name, is_stdlib, category, description, declared_in (pyproject extras), import sites, lazy import sites, import_style (top-level/lazy/mixed), n_api_symbols, n_api_uses |
| `library_api` | `api_id`, e.g. `scipy.signal.sosfiltfilt` | library, submodule, symbol, category (FFT, filtering, linear algebra, clustering, ...), usage_kinds (call/attribute), n_uses, n_functions |
| `primitives` | `primitive_id` = `<kind>:<name>` | kind (`syntax`, `operator`, `builtin`, `exception`), category (control flow, comprehensions, indexing, operators, builtin iteration, ...), description, n_uses, n_functions |

## Link tables

| Table | Links |
|---|---|
| `calls` | function → internal function or class (`edge` = call / instantiate) |
| `imports` | module/function → imported name (`is_lazy` = import inside a function) |
| `function_library_api` | function → library API symbol (count) |
| `function_primitives` | function → Python primitive (count) |
| `function_methods` | function → `obj.method()` calls whose receiver type is unknown statically (mostly NumPy array methods: `.reshape`, `.astype`, ...) |
| `algorithm_functions` | algorithm → every function it reaches through the call graph, with `depth` (0 = its own code) and `reached_from` |
| `algorithm_relations` | algorithm → algorithm (e.g. a sorter calls a preprocessing step, or names a registered detection method in its params) |

## Global dataset

`global_dataset` has one row per (algorithm, element). `element_type` is `function`, `library`, `library_api`, `primitive` or `object_method`. Each row also has `min_depth` (how far from the algorithm's own code the element first appears), `n_uses` and `n_via_functions`.

Filter `min_depth = 0` to get what an algorithm does itself. Use `min_depth <= 2` to include the helpers it calls. Depth 3 mostly reaches `core` infrastructure, which is also flagged by `algorithm_functions.is_core`. Views: `v_algorithm_api`, `v_algorithm_primitives`, `v_algorithm_own_libraries`, `v_library_algorithms`.

## How algorithms are found

1. **Method registries:** `detect_peak_methods`, `matching_methods`, `clustering_methods`, the motion and localization `_methods_list`s, `_all_preprocesser_dict` (its comment groups become `subtype`), `_unit_location_methods`, `pca_metrics_list`, `misc_metrics_list`, `sorter_full_list`, and the split/merge method lists.
2. **Base classes:** subclasses of `BaseMetric`, `AnalyzerExtension`, `BasePreprocessor`, `PeakDetector`, `BaseTemplateMatching`, `LocalizeBase`, `BaseSorter` and `PipelineNode` that aren't in a registry.
3. **Curated function-level algorithms:** curation, comparison, noise and whitening, peak selection, motion interpolation, template estimation.

An algorithm's seed functions are the class's own methods, its `metric_function`, and methods inherited from non-core bases. From the seeds, a breadth-first search runs over the call graph up to depth 3. Instantiating a class counts as using all of that class's methods, so `FilterRecordingSegment.get_traces` is reached from `bandpass_filter`.

## Limits of static analysis

- Dispatch by string (`detect_peaks(method="locally_exclusive")`) is invisible to the call graph. It is recovered heuristically in `algorithm_relations` ("references method name").
- Method calls on objects of unknown type go into `function_methods`, not `library_api`. This means NumPy array methods are not attributed to `numpy`.
- About 70 internal calls stay unresolved, mainly dynamically generated `plot_*` widget functions.

## Example queries

```sql
-- Which SciPy/NumPy/sklearn/numba APIs does SC2's circus-omp matcher use, nearest first?
SELECT api_id, category, n_uses, min_depth FROM v_algorithm_api
WHERE algorithm_id='template matching:circus-omp' ORDER BY min_depth, n_uses DESC;

-- Which algorithms use torch, and how directly?
SELECT algorithm_id, min_depth, n_uses FROM v_library_algorithms WHERE library_id='torch' ORDER BY min_depth;

-- Primitive profile (loops, comprehensions, exceptions...) of every peak detector's own code
SELECT g.algorithm_id, p.category, SUM(g.n_uses) n FROM global_dataset g JOIN primitives p ON p.primitive_id=g.element_id
WHERE g.element_type='primitive' AND g.min_depth=0 AND g.algorithm_id LIKE 'peak detection:%' GROUP BY 1,2;

-- What does each native sorter compose?
SELECT * FROM algorithm_relations WHERE algorithm_id IN ('spike sorter:spykingcircus2','spike sorter:tridesclous2');
```
