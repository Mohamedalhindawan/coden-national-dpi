"""Review-only AST import comparison; no package is imported or executed."""
import ast
import io
import zipfile

PREFIX = "browser_use_sdk"


def inspect_imports(sources):
    refs = set()
    for filename, source in sorted(sources.items()):
        for node in ast.walk(ast.parse(source, filename=filename)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == PREFIX or alias.name.startswith(PREFIX + "."):
                        refs.add((alias.name, None))
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                if node.module == PREFIX or node.module.startswith(PREFIX + "."):
                    for alias in node.names:
                        refs.add((node.module, alias.name))
    return sorted(refs, key=lambda x: (x[0], x[1] or ""))


def compare_imports(refs, sources):
    modules = {}
    for name, source in sources.items():
        if not name.endswith(".py"):
            continue
        name = name[:-3].replace("/", ".").removesuffix(".__init__")
        exports = set()
        for node in ast.parse(source).body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                exports.add(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                exports.update(a.asname or a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.Assign):
                exports.update(t.id for t in node.targets if isinstance(t, ast.Name))
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                exports.add(node.target.id)
        modules[name] = exports
    missing, uncertain = set(), set()
    for module, symbol in refs:
        if module not in modules:
            missing.add(module)
        elif symbol and symbol not in modules[module] and module + "." + symbol not in modules:
            uncertain.add(module + ":" + symbol)
    return {"missing_modules": sorted(missing), "unverified_symbols": sorted(uncertain),
            "runtime_compatibility_verified": False}


def read_python(wheel):
    sources = {}
    with zipfile.ZipFile(io.BytesIO(wheel)) as z:
        entries = z.infolist()
        if len(entries) > 50000 or sum(e.file_size for e in entries) > 256*1024*1024:
            raise ValueError("archive size limit")
        for entry in entries:
            if entry.filename.endswith(".py"):
                if entry.file_size > 2*1024*1024 or entry.filename in sources:
                    raise ValueError("source size or duplicate")
                sources[entry.filename] = z.read(entry).decode("utf-8-sig")
    return sources
