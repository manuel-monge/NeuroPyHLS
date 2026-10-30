#!/usr/bin/env python3
"""Build a relational "code database" of a Python repository by static (AST) analysis.

Nothing in the target repository is imported or executed.

Tables produced (SQLite + one CSV per table):
  modules, classes, functions, libraries, library_api, primitives, algorithms   (entity tables)
  imports, calls, function_library_api, function_primitives, function_methods,
  algorithm_functions, algorithm_relations                                     (link tables)
  global_dataset                                                               (algorithm x everything)

Usage:
  python3 -I build_code_db.py <repo_root> <package_name> <out_dir> [--commit SHA]
"""

import argparse
import ast
import builtins
import csv
import json
import os
import re
import sqlite3
import sys
import tomllib
from collections import Counter, defaultdict

# ----------------------------------------------------------------------------- reference data

BUILTIN_NAMES = set(dir(builtins))
STDLIB = set(sys.stdlib_module_names)

# Library categories (top-level import name -> (category, description, pypi name))
LIBRARY_INFO = {
    "numpy": ("numerical arrays", "N-d arrays, vectorised math, FFT, linear algebra", "numpy"),
    "scipy": ("scientific computing", "Signal processing, optimisation, sparse, spatial, stats", "scipy"),
    "sklearn": ("machine learning", "Clustering, PCA/decomposition, nearest neighbours, classifiers", "scikit-learn"),
    "numba": ("JIT compilation", "LLVM JIT of numeric Python loops (@njit, prange)", "numba"),
    "torch": ("deep learning / GPU", "Tensors on CPU/GPU, conv layers, NN models", "torch"),
    "hdbscan": ("clustering", "Hierarchical density-based clustering", "hdbscan"),
    "networkx": ("graphs", "Graph algorithms (connected components, merges)", "networkx"),
    "pandas": ("dataframes", "Tabular data, metric tables", "pandas"),
    "matplotlib": ("plotting", "Static plots and widgets backend", "matplotlib"),
    "zarr": ("storage / I/O", "Chunked compressed array storage", "zarr"),
    "h5py": ("storage / I/O", "HDF5 files", "h5py"),
    "neo": ("electrophysiology I/O", "Readers for >40 ephys file formats", "neo"),
    "probeinterface": ("electrophysiology I/O", "Probe geometry / wiring description", "probeinterface"),
    "tqdm": ("utilities", "Progress bars", "tqdm"),
    "threadpoolctl": ("parallelism", "Limit BLAS/OpenMP threads in workers", "threadpoolctl"),
    "pyopencl": ("GPU", "OpenCL kernels", "pyopencl"),
    "pynwb": ("electrophysiology I/O", "Neurodata Without Borders files", "pynwb"),
    "packaging": ("utilities", "Version parsing", "packaging"),
    "pydantic": ("utilities", "Typed parameter models / validation", "pydantic"),
    "ipywidgets": ("plotting", "Jupyter interactive widgets", "ipywidgets"),
    "sortingview": ("plotting", "Web-based sorting visualisation", "sortingview"),
    "figurl": ("plotting", "Web figure URLs", "figurl"),
    "ephyviewer": ("plotting", "Qt ephys viewer", "ephyviewer"),
    "skops": ("machine learning", "Safe sklearn model persistence", "skops"),
    "huggingface_hub": ("machine learning", "Model download from HF hub", "huggingface_hub"),
    "cuda": ("GPU", "CUDA python bindings", "cuda-python"),
    "cupy": ("GPU", "NumPy-compatible GPU arrays", "cupy"),
    "MEArec": ("simulation", "MEA recording simulator", "MEArec"),
    "isosplit6": ("clustering", "ISO-SPLIT clustering", "isosplit6"),
    "pynapple": ("analysis", "Time-series neuro analysis", "pynapple"),
    "medicine": ("motion estimation", "MEDiCINe motion estimation (torch)", "medicine-neuro"),
    "spikeinterface_kilosort_components": ("spike sorting", "GPL Kilosort components (external)", "spikeinterface-kilosort-components"),
    "pyedflib": ("electrophysiology I/O", "EDF files", "pyedflib"),
    "lxml": ("storage / I/O", "XML parsing", "lxml"),
    "ibllib": ("electrophysiology I/O", "IBL streaming", "ibllib"),
    "hdmf_zarr": ("storage / I/O", "HDMF zarr backend for NWB", "hdmf-zarr"),
    "fsspec": ("storage / I/O", "Remote file systems", "fsspec"),
    "remfile": ("storage / I/O", "Remote HTTP file access", "remfile"),
    "boto3": ("storage / I/O", "AWS S3 client", "boto3"),
    "docker": ("containers", "Run sorters in Docker", "docker"),
    "spython": ("containers", "Run sorters in Singularity", "spython"),
    "psutil": ("utilities", "System / memory info", "psutil"),
    "requests": ("networking", "HTTP client", "requests"),
    "IPython": ("plotting", "Notebook display", "ipython"),
    "plotly": ("plotting", "Interactive plots", "plotly"),
    "datalad": ("storage / I/O", "Dataset download", "datalad"),
    "cv2": ("image processing", "OpenCV", "opencv-python"),
    "tensorflow": ("deep learning / GPU", "DeepInterpolation models", "tensorflow"),
    "deepinterpolation": ("deep learning / GPU", "DeepInterpolation denoising", "deepinterpolation"),
    "mountainsort4": ("spike sorting", "External sorter package", "mountainsort4"),
    "mountainsort5": ("spike sorting", "External sorter package", "mountainsort5"),
    "kilosort": ("spike sorting", "External sorter package (KS4)", "kilosort"),
    "tridesclous": ("spike sorting", "External sorter package", "tridesclous"),
    "herdingspikes": ("spike sorting", "External sorter package", "herdingspikes"),
    "pykilosort": ("spike sorting", "External sorter package", "pykilosort"),
    "dartsort": ("spike sorting", "External sorter package", "dartsort"),
}

# API category by dotted prefix (longest prefix wins)
API_CATEGORY = {
    "numpy.fft": "FFT", "scipy.fft": "FFT", "scipy.fftpack": "FFT",
    "numpy.linalg": "linear algebra", "scipy.linalg": "linear algebra", "scipy.sparse.linalg": "linear algebra",
    "numpy.random": "random numbers", "numpy.lib.stride_tricks": "array views",
    "scipy.signal": "signal processing / filtering", "scipy.ndimage": "image / n-d filtering",
    "scipy.interpolate": "interpolation", "scipy.optimize": "optimisation", "scipy.stats": "statistics",
    "scipy.spatial": "spatial / distances", "scipy.sparse": "sparse matrices", "scipy.special": "special functions",
    "scipy.cluster": "clustering", "scipy.io": "file I/O", "scipy.integrate": "integration",
    "sklearn.decomposition": "dimensionality reduction", "sklearn.cluster": "clustering",
    "sklearn.neighbors": "nearest neighbours", "sklearn.metrics": "ML metrics",
    "sklearn.random_projection": "dimensionality reduction", "sklearn.discriminant_analysis": "classification",
    "sklearn.mixture": "clustering", "sklearn.preprocessing": "feature scaling", "sklearn.linear_model": "regression",
    "sklearn.model_selection": "model selection", "sklearn.pipeline": "ML pipelines", "sklearn.ensemble": "classification",
    "sklearn.impute": "feature scaling", "sklearn.svm": "classification",
    "numba": "JIT compilation", "torch.nn": "neural networks", "torch": "tensors / GPU", "hdbscan": "clustering",
    "networkx": "graph algorithms", "pandas": "dataframes", "matplotlib": "plotting", "zarr": "storage / I/O",
    "h5py": "storage / I/O", "neo": "ephys file I/O", "probeinterface": "probe geometry", "pyopencl": "GPU kernels",
    "multiprocessing": "parallelism", "concurrent.futures": "parallelism", "threading": "parallelism",
    "threadpoolctl": "parallelism", "os": "OS / filesystem", "pathlib": "OS / filesystem", "shutil": "OS / filesystem",
    "json": "serialisation", "pickle": "serialisation", "warnings": "diagnostics", "time": "timing",
    "datetime": "timing", "copy": "object copying", "itertools": "iteration tools", "functools": "functional tools",
    "collections": "containers", "math": "scalar math", "inspect": "introspection", "importlib": "introspection",
    "typing": "type hints", "dataclasses": "data classes", "tempfile": "OS / filesystem", "subprocess": "processes",
    "platform": "OS / filesystem", "sys": "interpreter", "re": "text / regex", "string": "text / regex",
    "random": "random numbers", "uuid": "identifiers", "hashlib": "hashing", "weakref": "memory management",
    "gc": "memory management", "mmap": "memory mapping", "struct": "binary formats", "io": "streams",
    "tqdm": "progress", "packaging": "versioning", "pydantic": "parameter models", "abc": "abstract classes",
    "enum": "enumerations", "contextlib": "context managers", "operator": "functional tools", "traceback": "diagnostics",
    "logging": "diagnostics", "urllib": "networking", "zipfile": "archives", "tarfile": "archives",
    "signal": "processes", "atexit": "processes", "textwrap": "text / regex", "heapq": "containers",
    "bisect": "containers", "numbers": "type hints", "socket": "networking", "getpass": "interpreter",
    "fnmatch": "OS / filesystem", "glob": "OS / filesystem", "csv": "serialisation", "base64": "serialisation",
    "numpy": "array creation / math", "scipy": "scientific computing", "sklearn": "machine learning",
}

# Python primitives: syntax node type -> (category, description)
SYNTAX = {
    "For": ("control flow", "for loop"), "AsyncFor": ("control flow", "async for loop"),
    "While": ("control flow", "while loop"), "If": ("control flow", "if statement"),
    "IfExp": ("control flow", "conditional expression a if c else b"), "Break": ("control flow", "break"),
    "Continue": ("control flow", "continue"), "Return": ("control flow", "return"),
    "Match": ("control flow", "structural pattern matching"),
    "Try": ("exceptions", "try/except block"), "TryStar": ("exceptions", "try/except* block"),
    "Raise": ("exceptions", "raise statement"), "Assert": ("exceptions", "assert statement"),
    "With": ("context managers", "with statement"), "AsyncWith": ("context managers", "async with statement"),
    "ListComp": ("comprehensions", "list comprehension"), "DictComp": ("comprehensions", "dict comprehension"),
    "SetComp": ("comprehensions", "set comprehension"), "GeneratorExp": ("comprehensions", "generator expression"),
    "Lambda": ("functions", "lambda expression"), "Yield": ("generators", "yield"),
    "YieldFrom": ("generators", "yield from"), "Await": ("async", "await"),
    "Global": ("scoping", "global declaration"), "Nonlocal": ("scoping", "nonlocal declaration"),
    "JoinedStr": ("strings", "f-string"), "Starred": ("unpacking", "*args / star unpacking"),
    "Slice": ("indexing", "slice a:b:c"), "Subscript": ("indexing", "subscript x[i]"),
    "NamedExpr": ("assignment", "walrus operator :="), "AugAssign": ("assignment", "augmented assignment (+= etc.)"),
    "AnnAssign": ("assignment", "annotated assignment"), "Delete": ("assignment", "del statement"),
    "Dict": ("literals", "dict literal"), "List": ("literals", "list literal"), "Set": ("literals", "set literal"),
    "Tuple": ("literals", "tuple literal"), "Assign": ("assignment", "assignment"),
    "ClassDef": ("definitions", "nested class definition"), "FunctionDef": ("definitions", "nested function / closure"),
}
OPERATORS = {
    "Add": "+", "Sub": "-", "Mult": "*", "Div": "/", "FloorDiv": "//", "Mod": "%", "Pow": "**",
    "MatMult": "@ (matrix multiply)", "LShift": "<<", "RShift": ">>", "BitOr": "|", "BitAnd": "&", "BitXor": "^",
    "Eq": "==", "NotEq": "!=", "Lt": "<", "LtE": "<=", "Gt": ">", "GtE": ">=", "Is": "is", "IsNot": "is not",
    "In": "in", "NotIn": "not in", "And": "and", "Or": "or", "Not": "not", "USub": "unary -", "UAdd": "unary +",
    "Invert": "~ (bitwise not)",
}
BUILTIN_CATEGORY = {
    **{n: "builtin type / constructor" for n in "int float bool str bytes bytearray list dict set frozenset tuple complex object type range slice memoryview".split()},
    **{n: "builtin iteration" for n in "enumerate zip map filter reversed sorted iter next all any".split()},
    **{n: "builtin math" for n in "abs round min max sum pow divmod".split()},
    **{n: "builtin introspection" for n in "isinstance issubclass hasattr getattr setattr delattr callable id hash vars dir globals locals super property staticmethod classmethod".split()},
    **{n: "builtin I/O" for n in "print open input repr format ascii".split()},
    "len": "builtin sizing", "chr": "builtin conversion", "ord": "builtin conversion", "hex": "builtin conversion",
    "bin": "builtin conversion", "oct": "builtin conversion", "eval": "builtin dynamic code", "exec": "builtin dynamic code",
    "compile": "builtin dynamic code", "__import__": "builtin dynamic code", "breakpoint": "builtin debugging",
}

BRANCH_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.IfExp, ast.Try, ast.ExceptHandler, ast.With,
                ast.AsyncWith, ast.comprehension, ast.Assert, ast.Match)
NEST_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.With, ast.AsyncWith, ast.Match)


def api_category(dotted):
    parts = dotted.split(".")
    for i in range(len(parts), 0, -1):
        c = API_CATEGORY.get(".".join(parts[:i]))
        if c:
            return c
    return "other"


def first_line(doc):
    if not doc:
        return ""
    for ln in doc.strip().splitlines():
        if ln.strip():
            return ln.strip()[:200]
    return ""


# ----------------------------------------------------------------------------- pass 1: modules + definitions

class Repo:
    def __init__(self, src_root, package):
        self.src_root = src_root
        self.package = package
        self.modules = {}        # modname -> dict(path, tree, source, is_pkg)
        self.imports = {}        # modname -> {alias: dotted}
        self.defs = {}           # dotted -> ('function'|'class', node, module, classname|None)
        self.classes = {}        # dotted class -> dict(bases=[dotted or raw], methods={name: dotted}, attrs={})
        self.stars = {}          # modname -> [modules star-imported]
        self.func_aliases = {}   # dotted module attr -> class it wraps (define_function_from_class)

    def load(self):
        pkg_dir = os.path.join(self.src_root, self.package)
        for root, dirs, files in os.walk(pkg_dir):
            dirs[:] = sorted(d for d in dirs if d not in ("tests", "__pycache__"))
            for f in sorted(files):
                if not f.endswith(".py") or f.startswith("test_"):
                    continue
                path = os.path.join(root, f)
                rel = os.path.relpath(path, self.src_root)
                mod = rel[:-3].replace(os.sep, ".")
                is_pkg = f == "__init__.py"
                if is_pkg:
                    mod = mod[: -len(".__init__")]
                with open(path, encoding="utf-8") as fh:
                    src = fh.read()
                try:
                    tree = ast.parse(src, filename=rel)
                except SyntaxError as e:
                    print("skip (syntax)", rel, e, file=sys.stderr)
                    continue
                self.modules[mod] = dict(path=rel, tree=tree, source=src, is_pkg=is_pkg)

    def _resolve_relative(self, mod, level, target):
        if level == 0:
            return target
        base = mod.split(".")
        if not self.modules[mod]["is_pkg"]:
            base = base[:-1]
        if level > 1:
            base = base[: -(level - 1)]
        return ".".join(base + ([target] if target else []))

    def import_map(self, mod, nodes):
        m = {}
        for node in nodes:
            if isinstance(node, ast.Import):
                for a in node.names:
                    if a.asname:
                        m[a.asname] = a.name
                    else:
                        top = a.name.split(".")[0]
                        m[top] = top
            elif isinstance(node, ast.ImportFrom):
                base = self._resolve_relative(mod, node.level, node.module)
                for a in node.names:
                    if a.name == "*":
                        continue
                    m[a.asname or a.name] = f"{base}.{a.name}" if base else a.name
        return m

    def index(self):
        for mod, info in self.modules.items():
            tree = info["tree"]
            for node in tree.body:
                self._index_def(mod, node, None, mod)
            top_imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))
                           and not self._inside_def(tree, n)]
            self.imports[mod] = self.import_map(mod, top_imports)
            self.stars[mod] = [self._resolve_relative(mod, n.level, n.module) for n in top_imports
                               if isinstance(n, ast.ImportFrom) and any(a.name == "*" for a in n.names)]
        # module-level `f = define_function_from_class(source_class=C, ...)`: alias f -> class C
        for mod, info in self.modules.items():
            for node in info["tree"].body:
                if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                        and isinstance(node.value, ast.Call):
                    fn = expr_to_dotted(node.value.func) or ""
                    if not fn.split(".")[-1].startswith("define_function"):
                        continue
                    src = [k.value for k in node.value.keywords if k.arg == "source_class"] + node.value.args[:1]
                    if src and isinstance(src[0], ast.Name):
                        name = src[0].id
                        target = self.imports[mod].get(name, f"{mod}.{name}")
                        self.imports[mod].setdefault(node.targets[0].id, target)
                        self.func_aliases[f"{mod}.{node.targets[0].id}"] = target

    @staticmethod
    def _inside_def(tree, target):
        # cheap: lineno-based check is enough; build once per module
        return getattr(target, "_in_def", False)

    def _index_def(self, mod, node, cls, prefix):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            dotted = f"{prefix}.{node.name}"
            self.defs[dotted] = ("function", node, mod, cls)
            if cls:
                self.classes[cls]["methods"][node.name] = dotted
            for sub in ast.walk(node):
                if sub is not node and isinstance(sub, (ast.Import, ast.ImportFrom)):
                    sub._in_def = True
            for sub in node.body:
                self._index_nested(mod, sub, dotted)
        elif isinstance(node, ast.ClassDef):
            dotted = f"{prefix}.{node.name}"
            self.defs[dotted] = ("class", node, mod, cls)
            attrs = {}
            for b in node.body:
                if isinstance(b, ast.Assign) and len(b.targets) == 1 and isinstance(b.targets[0], ast.Name):
                    attrs[b.targets[0].id] = b.value
            self.classes[dotted] = dict(node=node, module=mod, bases_raw=node.bases, methods={}, attrs=attrs, bases=[])
            for b in node.body:
                self._index_def(mod, b, dotted, dotted)
        elif isinstance(node, (ast.If, ast.Try)):
            for b in ast.iter_child_nodes(node):
                if isinstance(b, (ast.stmt, ast.excepthandler)):
                    self._index_def(mod, b, cls, prefix)

    def _index_nested(self, mod, node, parent):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            dotted = f"{parent}.<locals>.{node.name}"
            self.defs[dotted] = ("function", node, mod, None)
            for sub in node.body:
                self._index_nested(mod, sub, dotted)
        elif isinstance(node, ast.stmt):
            for b in ast.iter_child_nodes(node):
                if isinstance(b, ast.stmt) or isinstance(b, ast.excepthandler):
                    self._index_nested(mod, b, parent)

    # resolve a dotted name through package re-exports to its defining location
    def canonical(self, dotted, _depth=0):
        if dotted in self.func_aliases and _depth <= 10:
            return self.canonical(self.func_aliases[dotted], _depth + 1)
        if dotted in self.modules and "." in dotted and _depth <= 10:
            # `pkg.whiten` may be the function re-exported by pkg/__init__, shadowing submodule pkg/whiten.py
            parent, head = dotted.rsplit(".", 1)
            if parent in self.modules:
                alias = self.imports.get(parent, {}).get(head)
                cands = [alias] if alias and alias != dotted else []
                cands += [f"{s}.{head}" for s in self.stars.get(parent, ())]
                for c in cands:
                    r = self.canonical(c, _depth + 1)
                    if r in self.defs:
                        return r
        if dotted in self.defs or dotted in self.modules or _depth > 10:
            return dotted
        parts = dotted.split(".")
        for i in range(len(parts) - 1, 0, -1):
            prefix = ".".join(parts[:i])
            if prefix in self.modules:
                head = parts[i]
                alias = self.imports.get(prefix, {}).get(head)
                if alias:
                    return self.canonical(".".join([alias] + parts[i + 1:]), _depth + 1)
                for star in self.stars.get(prefix, ()):
                    cand = self.canonical(".".join([star] + parts[i:]), _depth + 1)
                    if cand in self.defs or cand in self.modules:
                        return cand
                # attribute of a class
                cand = f"{prefix}.{head}"
                if cand in self.classes and i + 1 < len(parts):
                    m = self.lookup_method(cand, parts[i + 1])
                    if m:
                        return m
                return dotted
        return dotted

    def resolve_bases(self):
        for cls, info in self.classes.items():
            mod = info["module"]
            for b in info["bases_raw"]:
                d = expr_to_dotted(b)
                if not d:
                    continue
                head, _, rest = d.partition(".")
                imp = self.imports[mod]
                if head in imp:
                    full = imp[head] + ("." + rest if rest else "")
                elif f"{mod}.{head}" in self.defs:
                    full = f"{mod}.{d}"
                else:
                    full = d
                info["bases"].append(self.canonical(full))

    def mro(self, cls, _seen=None):
        _seen = _seen or set()
        out = [cls]
        for b in self.classes.get(cls, {}).get("bases", []):
            if b in self.classes and b not in _seen:
                _seen.add(b)
                out += self.mro(b, _seen)
            elif b not in self.classes:
                out.append(b)
        return out

    def lookup_method(self, cls, name):
        for c in self.mro(cls):
            m = self.classes.get(c, {}).get("methods", {}).get(name)
            if m:
                return m
        return None

    def subclass_of(self, cls, base_short):
        return any(c.split(".")[-1] == base_short for c in self.mro(cls)[1:])


def expr_to_dotted(e):
    parts = []
    while isinstance(e, ast.Attribute):
        parts.append(e.attr)
        e = e.value
    if isinstance(e, ast.Name):
        parts.append(e.id)
        return ".".join(reversed(parts))
    return None


# ----------------------------------------------------------------------------- pass 2: function bodies

class BodyVisitor(ast.NodeVisitor):
    """Walks one function body (not nested defs) collecting calls, API uses, primitives."""

    def __init__(self, repo, mod, scope, cls, local_names):
        self.repo, self.mod, self.scope, self.cls = repo, mod, scope, cls
        self.local_names = local_names          # params + assigned names: shadow module/builtins
        self.calls = Counter()                  # internal dotted -> n
        self.api = Counter()                    # (dotted, kind) -> n
        self.prims = Counter()                  # primitive id -> n
        self.methods = Counter()                # unresolved obj.method -> n
        self.strings = set()
        self.complexity = 1
        self.max_nest = 0
        self._nest = 0
        self._seen_attr_nodes = set()

    # -- resolution
    def resolve(self, dotted):
        head, _, rest = dotted.partition(".")
        if head in ("self", "cls") and self.cls:
            if not rest:
                return None
            name = rest.split(".")[0]
            m = self.repo.lookup_method(self.cls, name)
            return ("internal", m) if m and "." not in rest else None
        if head in self.local_names:
            return None
        if head in self.scope:
            full = self.scope[head] + ("." + rest if rest else "")
        elif f"{self.mod}.{head}" in self.repo.defs:
            full = f"{self.mod}.{dotted}"
        elif head in BUILTIN_NAMES and not rest:
            return ("builtin", head)
        else:
            return None
        if full.split(".")[0] == self.repo.package:
            return ("internal", self.repo.canonical(full))
        return ("external", full)

    # -- visitors
    def generic_visit(self, node):
        name = type(node).__name__
        if name in SYNTAX:
            self.prims[f"syntax:{name}"] += 1
        if isinstance(node, BRANCH_NODES):
            self.complexity += 1
        if isinstance(node, ast.BoolOp):
            self.complexity += len(node.values) - 1
        if isinstance(node, (ast.BinOp, ast.AugAssign)):
            self.prims[f"operator:{type(node.op).__name__}"] += 1
        elif isinstance(node, ast.UnaryOp):
            self.prims[f"operator:{type(node.op).__name__}"] += 1
        elif isinstance(node, ast.BoolOp):
            self.prims[f"operator:{type(node.op).__name__}"] += 1
        elif isinstance(node, ast.Compare):
            for op in node.ops:
                self.prims[f"operator:{type(op).__name__}"] += 1
        elif isinstance(node, ast.ExceptHandler) and node.type is not None:
            for t in (node.type.elts if isinstance(node.type, ast.Tuple) else [node.type]):
                d = expr_to_dotted(t)
                if d and d in BUILTIN_NAMES:
                    self.prims[f"exception:{d}"] += 1
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value) < 60:
            self.strings.add(node.value)
        if isinstance(node, NEST_NODES):
            self._nest += 1
            self.max_nest = max(self.max_nest, self._nest)
            super().generic_visit(node)
            self._nest -= 1
        else:
            super().generic_visit(node)

    def visit_FunctionDef(self, node):      # nested def: count it, but don't descend
        self.prims["syntax:FunctionDef"] += 1
        for d in node.decorator_list:
            self.visit(d)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        self.prims["syntax:ClassDef"] += 1

    def visit_Raise(self, node):
        if node.exc is not None:
            target = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
            d = expr_to_dotted(target)
            if d and d in BUILTIN_NAMES:
                self.prims[f"exception:{d}"] += 1
        self.generic_visit(node)

    def visit_Call(self, node):
        d = expr_to_dotted(node.func)
        if d:
            r = self.resolve(d)
            self._seen_attr_nodes.add(id(node.func))
            if r is None:
                if isinstance(node.func, ast.Attribute):
                    if d.startswith("super."):
                        pass
                    self.methods[node.func.attr] += 1
            elif r[0] == "internal":
                self.calls[r[1]] += 1
            elif r[0] == "external":
                self.api[(r[1], "call")] += 1
            elif r[0] == "builtin":
                if r[1] in BUILTIN_NAMES and r[1][:1].isupper():
                    self.prims[f"exception:{r[1]}"] += 0  # constructed exception, counted on raise
                else:
                    self.prims[f"builtin:{r[1]}"] += 1
        elif isinstance(node.func, ast.Attribute):
            # e.g. super().foo(), x[0].bar()
            if isinstance(node.func.value, ast.Call) and isinstance(node.func.value.func, ast.Name) \
                    and node.func.value.func.id == "super" and self.cls:
                for b in self.repo.mro(self.cls)[1:]:
                    m = self.repo.classes.get(b, {}).get("methods", {}).get(node.func.attr)
                    if m:
                        self.calls[m] += 1
                        break
                self.prims["builtin:super"] += 1
                self._seen_attr_nodes.add(id(node.func))
                for a in node.args + [k.value for k in node.keywords]:
                    self.visit(a)
                self.prims["syntax:Call"] += 0
                return
            self.methods[node.func.attr] += 1
        self.generic_visit(node)

    def visit_Attribute(self, node):
        if id(node) not in self._seen_attr_nodes and isinstance(node.ctx, ast.Load):
            d = expr_to_dotted(node)
            if d:
                r = self.resolve(d)
                if r and r[0] == "external":
                    self.api[(r[1], "attribute")] += 1
                    return  # don't double-count inner prefix
                if r and r[0] == "internal" and r[1] in self.repo.defs:
                    self.calls[r[1]] += 0  # reference only
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load) and node.id not in self.local_names:
            if node.id in self.scope:
                full = self.scope[node.id]
                if full.split(".")[0] != self.repo.package and "." in full:
                    self.api[(full, "reference")] += 0
            elif node.id in ("True", "False", "None"):
                pass


def collect_local_names(fn):
    names = set()
    a = fn.args
    for arg in a.posonlyargs + a.args + a.kwonlyargs + ([a.vararg] if a.vararg else []) + ([a.kwarg] if a.kwarg else []):
        names.add(arg.arg)
    for n in ast.walk(fn):
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
            names.add(n.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n is not fn:
            names.add(n.name)
    # names bound by local imports are scope entries, not shadowing locals
    for n in ast.walk(fn):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            for al in n.names:
                names.discard(al.asname or al.name.split(".")[0])
    return names


# ----------------------------------------------------------------------------- algorithms

def build_algorithms(repo):
    """Registries + base-class discovery + a curated list of function-level algorithms."""
    P = repo.package
    algos = {}

    def add(aid, name, atype, subtype, entry, kind, source, registry_key=None, notes=""):
        if aid in algos:
            return
        algos[aid] = dict(algorithm_id=aid, name=name, algorithm_type=atype, subtype=subtype or "",
                          entry_point=entry, entry_kind=kind, discovered_by=source,
                          registry_key=registry_key or "", notes=notes)

    def cls_attr_str(cls, attr):
        for c in repo.mro(cls):
            v = repo.classes.get(c, {}).get("attrs", {}).get(attr)
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                return v.value
        return None

    def resolve_in(mod, name):
        imp = repo.imports[mod]
        if name in imp:
            return repo.canonical(imp[name])
        return repo.canonical(f"{mod}.{name}")

    def registry(mod, var):
        tree = repo.modules[mod]["tree"]
        src_lines = repo.modules[mod]["source"].splitlines()
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == var for t in node.targets):
                v = node.value
                out = []
                if isinstance(v, ast.Dict):
                    for k, val in zip(v.keys, v.values):
                        # nearest preceding "# comment" line inside the literal = group label
                        group = ""
                        for ln in range(k.lineno - 2, node.lineno - 1, -1):
                            s = src_lines[ln].strip()
                            if s.startswith("#"):
                                group = s.lstrip("# ").strip()
                                break
                        key = k.value if isinstance(k, ast.Constant) else resolve_in(mod, k.id)
                        out.append((key, resolve_in(mod, val.id), group, val.id))
                elif isinstance(v, (ast.List, ast.Tuple)):
                    group = ""
                    for e in v.elts:
                        for ln in range(e.lineno - 2, node.lineno - 1, -1):
                            s = src_lines[ln].strip()
                            if s.startswith("#"):
                                group = s.lstrip("# ").strip()
                                break
                        if isinstance(e, ast.Name):
                            out.append((None, resolve_in(mod, e.id), group, e.id))
                        elif isinstance(e, ast.Constant):
                            out.append((e.value, None, group, e.value))
                return out
        return []

    sc = f"{P}.sortingcomponents"
    # --- string-keyed registries of classes
    for mod, var, atype in [
        (f"{sc}.peak_detection.method_list", "detect_peak_methods", "peak detection"),
        (f"{sc}.matching.method_list", "matching_methods", "template matching"),
        (f"{sc}.clustering.method_list", "clustering_methods", "clustering"),
    ]:
        for key, target, _g, _r in registry(mod, var):
            add(f"{atype}:{key}", key, atype, "", target, "class", f"registry {var}", key)
    for mod, var, atype, attr in [
        (f"{sc}.motion.motion_estimation", "_methods_list", "motion estimation", "name"),
        (f"{sc}.peak_localization.method_list", "_methods_list", "peak localization", "name"),
        (f"{sc}.clustering.itersplit_tools", "split_methods_list", "cluster splitting", "name"),
        (f"{sc}.clustering.merging_tools", "find_pair_method_list", "cluster merging", "name"),
    ]:
        for _, target, _g, _r in registry(mod, var):
            key = cls_attr_str(target, attr) or target.split(".")[-1]
            add(f"{atype}:{key}", key, atype, "", target, "class", f"registry {var}", key)
    # --- function registries
    for key, target, _g, _r in registry(f"{P}.postprocessing.localization_tools", "_unit_location_methods"):
        add(f"unit localization:{key}", key, "unit localization", "", target, "function",
            "registry _unit_location_methods", key)
    for key, target, group, fname in registry(f"{P}.preprocessing.preprocessing_classes", "_all_preprocesser_dict"):
        add(f"preprocessing:{fname}", fname, "preprocessing", group, key, "class",
            "registry _all_preprocesser_dict", fname, notes=f"user-facing function {fname}()")
    # --- metric lists
    for mod, var, sub in [(f"{P}.metrics.quality.pca_metrics", "pca_metrics_list", "PCA-based"),
                          (f"{P}.metrics.quality.misc_metrics", "misc_metrics_list", "spike-train / amplitude")]:
        for _, target, _g, _r in registry(mod, var):
            key = cls_attr_str(target, "metric_name") or target.split(".")[-1]
            add(f"quality metric:{key}", key, "quality metric", sub, target, "class", f"registry {var}", key)
    # --- sorters
    for _, target, group, _r in registry(f"{P}.sorters.sorterlist", "sorter_full_list"):
        key = cls_attr_str(target, "sorter_name") or target.split(".")[-1]
        sub = "native (sortingcomponents)" if ".internal." in target else "external wrapper"
        add(f"spike sorter:{key}", key, "spike sorter", sub, target, "class", "registry sorter_full_list", key)

    # --- base-class discovery for everything not in a registry
    taken = {a["entry_point"] for a in algos.values()}
    base_rules = [  # (base short name, type, subtype fn)
        ("BaseMetric", None, None),
        ("BaseTemplateMatching", "template matching", None),
        ("PeakDetector", "peak detection", None),
        ("LocalizeBase", "peak localization", None),
        ("BasePreprocessor", "preprocessing", lambda c: "motion correction" if "motion" in c else "other"),
        ("AnalyzerExtension", "postprocessing extension", None),
        ("BaseSorter", "spike sorter", None),
        ("PipelineNode", "pipeline node", None),
    ]
    abstract = {"BaseMetric", "BaseTemplateMatching", "PeakDetector", "LocalizeBase", "BasePreprocessor",
                "AnalyzerExtension", "BaseSorter", "PipelineNode", "BaseSpikeVectorExtension",
                "BaseMetricExtension", "ComponentsBasedSorter", "KilosortBase", "WaveformsNode", "PeakSource",
                "TemporalPCBaseNode", "PeakDetectorWrapper", "BasePreprocessorSegment"}
    for cls in sorted(repo.classes):
        short = cls.split(".")[-1]
        if cls in taken or short in abstract or ".tests." in cls or ".benchmark." in cls:
            continue
        for base, atype, subfn in base_rules:
            if repo.subclass_of(cls, base):
                if base == "BaseMetric":
                    key = cls_attr_str(cls, "metric_name") or short
                    if ".metrics.template." in cls:
                        atype, sub = "template metric", ""
                    elif ".metrics.spiketrain." in cls:
                        atype, sub = "spike-train metric", ""
                    else:
                        atype, sub = "quality metric", ""
                elif base == "AnalyzerExtension":
                    key = cls_attr_str(cls, "extension_name") or short
                    sub = cls.split(".")[1]
                elif base == "BaseSorter":
                    key = cls_attr_str(cls, "sorter_name") or short
                    sub = "archived / extra"
                elif base == "PipelineNode":
                    key = short
                    sub = cls.split(".")[1] + "." + cls.split(".")[2]
                else:
                    key = cls_attr_str(cls, "name") or short
                    sub = subfn(cls) if subfn else ""
                add(f"{atype}:{key}", key, atype, sub, cls, "class", f"subclass of {base}", key)
                break

    # --- curated function-level algorithms (no registry/base class in the code)
    curated = [
        ("peak selection", "select_peaks", f"{sc}.peak_selection.select_peaks", "uniform / smart sampling variants"),
        ("noise estimation", "get_noise_levels", f"{P}.core.recording_tools.get_noise_levels", "MAD or std on random chunks"),
        ("whitening", "compute_whitening_matrix", f"{P}.preprocessing.whiten.compute_whitening_matrix", ""),
        ("curation", "auto_merge (compute_merge_unit_groups)", f"{P}.curation.auto_merge.compute_merge_unit_groups", "presets: similarity_correlograms, slay, ..."),
        ("curation", "remove_redundant_units", f"{P}.curation.remove_redundant.remove_redundant_units", ""),
        ("curation", "remove_excess_spikes", f"{P}.curation.remove_excess_spikes.remove_excess_spikes", ""),
        ("curation", "find_duplicated_spikes", f"{P}.curation.curation_tools.find_duplicated_spikes", ""),
        ("curation", "bombcell_label_units", f"{P}.curation.bombcell_curation.bombcell_label_units", "threshold rules from Bombcell"),
        ("curation", "model_based_label_units", f"{P}.curation.model_based_curation.model_based_label_units", "sklearn classifier"),
        ("curation", "threshold_metrics_label_units", f"{P}.curation.threshold_metrics_curation.threshold_metrics_label_units", ""),
        ("curation", "train_model", f"{P}.curation.train_manual_curation.train_model", "UnitRefine-style training"),
        ("sorting comparison", "make_hungarian_match", f"{P}.comparison.comparisontools.make_hungarian_match", "linear_sum_assignment"),
        ("sorting comparison", "make_best_match", f"{P}.comparison.comparisontools.make_best_match", ""),
        ("sorting comparison", "make_match_count_matrix", f"{P}.comparison.comparisontools.make_match_count_matrix", "numba spike matching"),
        ("sorting comparison", "compare_spike_trains", f"{P}.comparison.comparisontools.compare_spike_trains", ""),
        ("motion correction", "correct_motion_on_peaks", f"{sc}.motion.motion_interpolation.correct_motion_on_peaks", ""),
        ("motion correction", "interpolate_motion_on_traces", f"{sc}.motion.motion_interpolation.interpolate_motion_on_traces", "kriging / linear / nearest"),
        ("template estimation", "estimate_templates", f"{P}.core.waveform_tools.estimate_templates", ""),
    ]
    for atype, name, target, notes in curated:
        if target in repo.defs:
            add(f"{atype}:{name}", name, atype, "", target, "function", "curated", "", notes)
        else:
            print("curated algorithm not found:", target, file=sys.stderr)
    return algos


# ----------------------------------------------------------------------------- main build

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo_root")
    ap.add_argument("package")
    ap.add_argument("out_dir")
    ap.add_argument("--commit", default="")
    ap.add_argument("--max-depth", type=int, default=3)
    args = ap.parse_args()

    src_root = os.path.join(args.repo_root, "src") if os.path.isdir(os.path.join(args.repo_root, "src")) else args.repo_root
    repo = Repo(src_root, args.package)
    repo.load()
    repo.index()
    repo.resolve_bases()
    P = args.package

    # declared dependencies (pyproject)
    declared = defaultdict(list)
    pp = os.path.join(args.repo_root, "pyproject.toml")
    if os.path.exists(pp):
        with open(pp, "rb") as fh:
            meta = tomllib.load(fh).get("project", {})
        def norm(req):
            return re.split(r"[ <>=;!\[@~]", req.strip())[0].lower().replace("_", "-")
        for r in meta.get("dependencies", []):
            declared[norm(r)].append("core")
        for extra, reqs in meta.get("optional-dependencies", {}).items():
            for r in reqs:
                if not r.startswith(P):
                    declared[norm(r)].append(extra)

    # ---------------- modules
    modules = []
    for mod, info in repo.modules.items():
        src = info["source"]
        lines = src.splitlines()
        modules.append(dict(
            module_id=mod, path=info["path"], subpackage=mod.split(".")[1] if mod.count(".") >= 1 else "",
            is_package_init=int(info["is_pkg"]), n_lines=len(lines),
            n_code_lines=sum(1 for l in lines if l.strip() and not l.strip().startswith("#")),
            docstring=first_line(ast.get_docstring(info["tree"]))))

    # ---------------- functions (+ module-level pseudo functions)
    functions, calls, f_api, f_prims, f_methods, f_strings, imports_rows = [], [], [], [], [], {}, []

    def scope_for(mod, fn_node):
        scope = dict(repo.imports[mod])
        local_imports = [n for n in ast.walk(fn_node) if isinstance(n, (ast.Import, ast.ImportFrom))]
        scope.update(repo.import_map(mod, local_imports))
        return scope, local_imports

    def record_imports(mod, func_id, nodes, lazy):
        for n in nodes:
            m = repo.import_map(mod, [n])
            for alias, full in m.items():
                top = full.split(".")[0]
                imports_rows.append(dict(module_id=mod, function_id=func_id or "", imported=full,
                                         library_id=top, is_internal=int(top == P), is_lazy=int(lazy),
                                         lineno=n.lineno))

    def analyse(func_id, mod, node, cls, kind):
        if node is None:   # module-level code
            body_nodes = [n for n in repo.modules[mod]["tree"].body
                          if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
            fake = ast.Module(body=body_nodes, type_ignores=[])
            scope, local_names = dict(repo.imports[mod]), set()
            v = BodyVisitor(repo, mod, scope, None, local_names)
            for b in body_nodes:
                if not isinstance(b, (ast.Import, ast.ImportFrom)):
                    v.visit(b)
            target = fake
        else:
            scope, local_imports = scope_for(mod, node)
            record_imports(mod, func_id, local_imports, lazy=True)
            v = BodyVisitor(repo, mod, scope, cls, collect_local_names(node))
            for d in node.decorator_list:
                v.visit(d)
            for b in node.body:
                v.visit(b)
            target = node
        for callee, n in v.calls.items():
            if callee != func_id:
                calls.append((func_id, callee, n))
        for (api, k), n in v.api.items():
            if n:
                f_api.append((func_id, api, k, n))
        for p, n in v.prims.items():
            if n:
                f_prims.append((func_id, p, n))
        for m, n in v.methods.items():
            f_methods.append((func_id, m, n))
        f_strings[func_id] = v.strings
        return v

    for mod in repo.modules:
        tree = repo.modules[mod]["tree"]
        top = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) and not getattr(n, "_in_def", False)]
        record_imports(mod, None, top, lazy=False)
        fid = f"{mod}.<module>"
        v = analyse(fid, mod, None, None, "module")
        functions.append(dict(function_id=fid, name="<module>", qualname="<module>", module_id=mod,
                              subpackage=mod.split(".")[1] if "." in mod else "", class_id="", kind="module-level code",
                              is_public=0, is_nested=0, lineno=1, end_lineno=len(repo.modules[mod]["source"].splitlines()),
                              n_lines=0, n_params=0, has_varargs=0, has_kwargs=0, n_defaults=0, decorators="",
                              is_numba_jit=0, is_generator=0, is_async=0, has_return_annotation=0,
                              cyclomatic_complexity=v.complexity, max_nesting=v.max_nest,
                              n_internal_calls=sum(v.calls.values()), n_library_calls=sum(n for (a, k), n in v.api.items() if k == "call"),
                              docstring=""))

    for fid, (kind, node, mod, cls) in repo.defs.items():
        if kind != "function":
            continue
        decos = [expr_to_dotted(d.func if isinstance(d, ast.Call) else d) or "?" for d in node.decorator_list]
        if cls:
            fkind = "staticmethod" if "staticmethod" in decos else "classmethod" if "classmethod" in decos \
                else "property" if "property" in decos else "method"
        else:
            fkind = "nested function" if "<locals>" in fid else "function"
        v = analyse(fid, mod, node, cls, fkind)
        a = node.args
        scope, _ = scope_for(mod, node)
        deco_full = [scope.get(d.split(".")[0], d.split(".")[0]) + ("." + d.split(".", 1)[1] if "." in d else "") for d in decos]
        is_gen = any(isinstance(n, (ast.Yield, ast.YieldFrom)) for n in ast.walk(node)
                     if not (isinstance(n, (ast.FunctionDef, ast.Lambda)) and n is not node))
        functions.append(dict(
            function_id=fid, name=node.name, qualname=fid[len(mod) + 1:], module_id=mod,
            subpackage=mod.split(".")[1] if "." in mod else "", class_id=cls or "", kind=fkind,
            is_public=int(not node.name.startswith("_") or (node.name.startswith("__") and node.name.endswith("__"))),
            is_nested=int("<locals>" in fid), lineno=node.lineno, end_lineno=node.end_lineno,
            n_lines=node.end_lineno - node.lineno + 1,
            n_params=len(a.posonlyargs) + len(a.args) + len(a.kwonlyargs) - (1 if cls and fkind in ("method", "classmethod", "property") else 0),
            has_varargs=int(a.vararg is not None), has_kwargs=int(a.kwarg is not None),
            n_defaults=len(a.defaults) + sum(1 for d in a.kw_defaults if d is not None),
            decorators=";".join(deco_full), is_numba_jit=int(any(d.startswith("numba") for d in deco_full)),
            is_generator=int(is_gen), is_async=int(isinstance(node, ast.AsyncFunctionDef)),
            has_return_annotation=int(node.returns is not None),
            cyclomatic_complexity=v.complexity, max_nesting=v.max_nest,
            n_internal_calls=sum(v.calls.values()),
            n_library_calls=sum(n for (api, k), n in v.api.items() if k == "call"),
            docstring=first_line(ast.get_docstring(node))))

    func_ids = {f["function_id"] for f in functions}

    # ---------------- classes
    classes = []
    for cid, info in repo.classes.items():
        node = info["node"]
        classes.append(dict(
            class_id=cid, name=node.name, module_id=info["module"], subpackage=cid.split(".")[1],
            bases=";".join(info["bases"]), mro=";".join(repo.mro(cid)[1:]), n_methods=len(info["methods"]),
            lineno=node.lineno, n_lines=node.end_lineno - node.lineno + 1,
            is_dataclass=int(any("dataclass" in (expr_to_dotted(d.func if isinstance(d, ast.Call) else d) or "") for d in node.decorator_list)),
            docstring=first_line(ast.get_docstring(node))))

    # instantiating a class == using all of its methods (covers Segment.get_traces etc.)
    call_rows = []
    for caller, callee, n in calls:
        if callee in repo.classes:
            call_rows.append(dict(caller_id=caller, callee_id=callee, callee_kind="class", n=n, edge="instantiate"))
        elif callee in func_ids:
            call_rows.append(dict(caller_id=caller, callee_id=callee, callee_kind="function", n=n, edge="call"))
        else:
            call_rows.append(dict(caller_id=caller, callee_id=callee, callee_kind="unresolved", n=n, edge="call"))
    call_rows = [r for r in call_rows if r["n"] > 0 or r["edge"] == "instantiate"]

    # ---------------- libraries + API
    lib_usage = defaultdict(lambda: dict(n_import_sites=0, n_lazy=0, modules=set()))
    for r in imports_rows:
        if r["is_internal"]:
            continue
        u = lib_usage[r["library_id"]]
        u["n_import_sites"] += 1
        u["n_lazy"] += r["is_lazy"]
        u["modules"].add(r["module_id"])
    api_usage = defaultdict(lambda: dict(n_uses=0, functions=set(), kinds=set()))
    for fid, api, k, n in f_api:
        u = api_usage[api]
        u["n_uses"] += n
        u["functions"].add(fid)
        u["kinds"].add(k)
    for api in api_usage:
        top = api.split(".")[0]
        if top not in lib_usage:
            lib_usage[top]  # library referenced only via API (e.g. imported in __init__)
    libraries = []
    for lib, u in sorted(lib_usage.items()):
        cat, desc, pypi = LIBRARY_INFO.get(lib, ("standard library" if lib in STDLIB else "other", "", lib))
        if lib in STDLIB:
            cat = "standard library"
            desc = desc or api_category(lib)
        n_api = sum(v["n_uses"] for a, v in api_usage.items() if a.split(".")[0] == lib)
        libraries.append(dict(
            library_id=lib, pypi_name=pypi if lib not in STDLIB else "", is_stdlib=int(lib in STDLIB),
            category=cat, description=desc,
            declared_in=";".join(sorted(set(declared.get(pypi.lower().replace("_", "-"), [])))),
            n_import_sites=u["n_import_sites"], n_lazy_import_sites=u["n_lazy"],
            n_modules=len(u["modules"]), n_api_symbols=sum(1 for a in api_usage if a.split(".")[0] == lib),
            n_api_uses=n_api,
            import_style="lazy only" if u["n_import_sites"] and u["n_lazy"] == u["n_import_sites"]
            else "top-level only" if u["n_lazy"] == 0 else "mixed"))
    library_api = []
    for api, u in sorted(api_usage.items()):
        parts = api.split(".")
        library_api.append(dict(
            api_id=api, library_id=parts[0], submodule=".".join(parts[:-1]), symbol=parts[-1],
            category=api_category(api), usage_kinds=";".join(sorted(u["kinds"])),
            n_uses=u["n_uses"], n_functions=len(u["functions"])))

    # ---------------- primitives
    prim_usage = defaultdict(lambda: dict(n=0, f=set()))
    for fid, p, n in f_prims:
        prim_usage[p]["n"] += n
        prim_usage[p]["f"].add(fid)
    primitives = []
    for p, u in sorted(prim_usage.items()):
        kind, name = p.split(":", 1)
        if kind == "syntax":
            cat, desc = SYNTAX[name]
        elif kind == "operator":
            cat, desc = "operators", OPERATORS.get(name, name)
        elif kind == "builtin":
            cat, desc = BUILTIN_CATEGORY.get(name, "builtin other"), f"{name}()"
        else:
            cat, desc = "exceptions", f"builtin exception {name}"
        primitives.append(dict(primitive_id=p, kind=kind, name=name, category=cat, description=desc,
                               n_uses=u["n"], n_functions=len(u["f"])))

    # ---------------- algorithms + reachability
    algos = build_algorithms(repo)
    graph = defaultdict(set)
    for r in call_rows:
        if r["callee_kind"] == "class":
            for m in repo.classes[r["callee_id"]]["methods"].values():
                graph[r["caller_id"]].add(m)
        elif r["callee_kind"] == "function":
            graph[r["caller_id"]].add(r["callee_id"])
    # nested functions belong to their parent
    for fid in func_ids:
        if "<locals>" in fid:
            graph[fid.rsplit(".<locals>.", 1)[0]].add(fid)

    def seed_functions(algo):
        e = algo["entry_point"]
        seeds = []
        if algo["entry_kind"] == "class":
            seeds = list(repo.classes.get(e, {}).get("methods", {}).values())
            info = repo.classes.get(e, {})
            # metric_function / main_function style attributes pointing at functions
            for attr in ("metric_function",):
                v = None
                for c in repo.mro(e):
                    v = repo.classes.get(c, {}).get("attrs", {}).get(attr)
                    if v is not None:
                        break
                if isinstance(v, ast.Name):
                    t = repo.canonical(repo.imports[repo.classes[c]["module"]].get(v.id, f"{repo.classes[c]['module']}.{v.id}"))
                    if t in func_ids:
                        seeds.append(t)
            # inherited methods the class relies on but doesn't override, from algorithm-specific (non-core) bases
            for b in repo.mro(e)[1:]:
                if b in repo.classes and ".core." not in b and b.split(".")[-1] not in (
                        "BasePreprocessor", "BasePreprocessorSegment", "AnalyzerExtension", "BaseSorter",
                        "PipelineNode", "BaseMetric", "BaseMetricExtension"):
                    for name, m in repo.classes[b]["methods"].items():
                        if name not in repo.classes[e]["methods"]:
                            seeds.append(m)
        elif e in func_ids:
            seeds = [e]
        return seeds

    algo_funcs = []
    for aid, algo in algos.items():
        seeds = seed_functions(algo)
        algo["n_seed_functions"] = len(seeds)
        dist = {s: 0 for s in seeds}
        via = {s: s for s in seeds}
        frontier = list(seeds)
        for d in range(1, args.max_depth + 1):
            nxt = []
            for f in frontier:
                for g in graph.get(f, ()):
                    if g not in dist:
                        dist[g] = d
                        via[g] = f
                        nxt.append(g)
            frontier = nxt
        for f, d in dist.items():
            algo_funcs.append(dict(algorithm_id=aid, function_id=f, depth=d, reached_from=via[f] if d else "",
                                   is_core=int(f.split(".")[1] == "core") if "." in f else 0))
        algo["n_functions_reachable"] = len(dist)

    # algorithm -> algorithm (composition): string constants that are registry keys of another algorithm, in own code,
    # plus direct reachability of another algorithm's entry point
    key_index = defaultdict(list)
    for aid, a in algos.items():
        if a["registry_key"] and a["discovered_by"].startswith("registry"):
            key_index[a["registry_key"]].append(aid)
    entry_index = {}
    for aid, a in algos.items():
        entry_index.setdefault(a["entry_point"], aid)
        for m in repo.classes.get(a["entry_point"], {}).get("methods", {}).values() if a["entry_kind"] == "class" else ():
            entry_index.setdefault(m, aid)
    relations = set()
    af_by_algo = defaultdict(list)
    for r in algo_funcs:
        af_by_algo[r["algorithm_id"]].append(r)
    for aid, rows in af_by_algo.items():
        own = [r["function_id"] for r in rows if r["depth"] == 0]
        for f in own:
            for s in f_strings.get(f, ()):
                for other in key_index.get(s, ()):
                    if other != aid:
                        relations.add((aid, other, "references method name (string constant)"))
        for r in rows:
            other = entry_index.get(r["function_id"])
            if other and other != aid and r["depth"] > 0 and r["depth"] <= 2:
                relations.add((aid, other, f"calls entry point (depth {r['depth']})"))
    algo_rel = [dict(algorithm_id=a, related_algorithm_id=b, relation=k) for a, b, k in sorted(relations)]

    # ---------------- global dataset: algorithm x {function, library, api, primitive, method}
    by_func_api = defaultdict(list)
    for fid, api, k, n in f_api:
        by_func_api[fid].append((api, n))
    by_func_prim = defaultdict(list)
    for fid, p, n in f_prims:
        by_func_prim[fid].append((p, n))
    by_func_meth = defaultdict(list)
    for fid, m, n in f_methods:
        by_func_meth[fid].append((m, n))
    func_meta = {f["function_id"]: f for f in functions}
    glob = []
    for aid, rows in af_by_algo.items():
        a = algos[aid]
        agg = defaultdict(lambda: [0, 99, set()])  # (etype, eid) -> [count, min_depth, via functions]
        for r in rows:
            f, d = r["function_id"], r["depth"]
            e = agg[("function", f)]
            e[0] += 1
            e[1] = min(e[1], d)
            for api, n in by_func_api.get(f, ()):
                for key in (("library_api", api), ("library", api.split(".")[0])):
                    e = agg[key]
                    e[0] += n
                    e[1] = min(e[1], d)
                    e[2].add(f)
            for p, n in by_func_prim.get(f, ()):
                e = agg[("primitive", p)]
                e[0] += n
                e[1] = min(e[1], d)
                e[2].add(f)
            for m, n in by_func_meth.get(f, ()):
                e = agg[("object_method", m)]
                e[0] += n
                e[1] = min(e[1], d)
                e[2].add(f)
        for (etype, eid), (n, d, fs) in agg.items():
            glob.append(dict(algorithm_id=aid, algorithm_name=a["name"], algorithm_type=a["algorithm_type"],
                             element_type=etype, element_id=eid, min_depth=d, n_uses=n,
                             n_via_functions=len(fs) if etype != "function" else 1,
                             element_subpackage=(func_meta[eid]["subpackage"] if etype == "function" and eid in func_meta else "")))

    # ---------------- algorithm summary columns
    for aid, a in algos.items():
        own = [g for g in glob if g["algorithm_id"] == aid and g["min_depth"] == 0]
        a["libraries_own"] = ";".join(sorted({g["element_id"] for g in own if g["element_type"] == "library"}))
        cls_or_fn = a["entry_point"]
        a["module_id"] = repo.defs.get(cls_or_fn, (None, None, ""))[2] if cls_or_fn in repo.defs else ""
        node = repo.defs.get(cls_or_fn, (None, None))[1]
        a["docstring"] = first_line(ast.get_docstring(node)) if node is not None else ""
        a["own_lines"] = sum(func_meta[r["function_id"]]["n_lines"] for r in af_by_algo[aid]
                             if r["depth"] == 0 and r["function_id"] in func_meta)
        a["uses_numba"] = int(any(func_meta.get(r["function_id"], {}).get("is_numba_jit") for r in af_by_algo[aid] if r["depth"] <= 1))
        a["uses_torch"] = int("torch" in {g["element_id"] for g in glob if g["algorithm_id"] == aid and g["element_type"] == "library" and g["min_depth"] <= 1})

    # ---------------- write
    os.makedirs(args.out_dir, exist_ok=True)
    tables = {
        "modules": modules, "classes": classes, "functions": functions, "libraries": libraries,
        "library_api": library_api, "primitives": primitives, "algorithms": list(algos.values()),
        "imports": imports_rows, "calls": call_rows,
        "function_library_api": [dict(function_id=f, api_id=a, usage_kind=k, n=n) for f, a, k, n in f_api],
        "function_primitives": [dict(function_id=f, primitive_id=p, n=n) for f, p, n in f_prims],
        "function_methods": [dict(function_id=f, method_name=m, n=n) for f, m, n in f_methods],
        "algorithm_functions": algo_funcs, "algorithm_relations": algo_rel, "global_dataset": glob,
    }
    db_path = os.path.join(args.out_dir, f"{P}_code.sqlite")
    if os.path.exists(db_path):
        os.remove(db_path)
    con = sqlite3.connect(db_path)
    csv_dir = os.path.join(args.out_dir, "csv")
    os.makedirs(csv_dir, exist_ok=True)
    for name, rows in tables.items():
        if not rows:
            continue
        cols = list(rows[0].keys())
        con.execute(f'CREATE TABLE {name} ({", ".join(cols)})')
        con.executemany(f'INSERT INTO {name} VALUES ({",".join("?" * len(cols))})',
                        [[r.get(c) for c in cols] for r in rows])
        with open(os.path.join(csv_dir, f"{name}.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
    con.executescript("""
    CREATE INDEX ix_af ON algorithm_functions(algorithm_id);
    CREATE INDEX ix_fa ON function_library_api(function_id);
    CREATE INDEX ix_fp ON function_primitives(function_id);
    CREATE INDEX ix_gd ON global_dataset(algorithm_id, element_type);
    CREATE INDEX ix_calls ON calls(caller_id);
    CREATE VIEW v_algorithm_own_libraries AS
      SELECT algorithm_id, element_id AS library_id, n_uses FROM global_dataset
      WHERE element_type='library' AND min_depth=0;
    CREATE VIEW v_algorithm_primitives AS
      SELECT g.algorithm_id, g.element_id AS primitive_id, p.category, g.n_uses, g.min_depth
      FROM global_dataset g JOIN primitives p ON p.primitive_id=g.element_id WHERE g.element_type='primitive';
    CREATE VIEW v_algorithm_api AS
      SELECT g.algorithm_id, g.element_id AS api_id, a.library_id, a.category, g.n_uses, g.min_depth
      FROM global_dataset g JOIN library_api a ON a.api_id=g.element_id WHERE g.element_type='library_api';
    CREATE VIEW v_library_algorithms AS
      SELECT element_id AS library_id, algorithm_id, algorithm_type, n_uses, min_depth
      FROM global_dataset WHERE element_type='library';
    """)
    meta = dict(package=P, commit=args.commit, max_depth=args.max_depth, counts={k: len(v) for k, v in tables.items()})
    con.execute("CREATE TABLE meta (key, value)")
    con.executemany("INSERT INTO meta VALUES (?,?)", [(k, json.dumps(v)) for k, v in meta.items()])
    con.commit()
    con.close()
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
