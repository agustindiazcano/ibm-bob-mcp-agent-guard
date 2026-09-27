import ast
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class PolicyViolation:
    rule: str
    lineno: int
    detail: str

class PolicyVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str, source_roots: list[str]):
        self.file_path = file_path
        self.source_roots = source_roots
        self.violations = []
        self.has_random_seed = False
        self.random_calls = []

    def add_violation(self, node: ast.AST, rule: str, detail: str):
        self.violations.append(PolicyViolation(rule, getattr(node, "lineno", 0), detail))

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            base = alias.name.split('.')[0]
            if base in ("hashlib", "zlib", "binascii"):
                self.add_violation(node, "fingerprint", f"Importing {alias.name} is forbidden")
            if base in ("subprocess", "ctypes"):
                self.add_violation(node, "process-escape", f"Importing {alias.name} is forbidden")
            if base in ("socket", "requests", "ftplib", "smtplib") or alias.name.startswith("urllib") or alias.name.startswith("http.client"):
                self.add_violation(node, "network", f"Importing {alias.name} is forbidden")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            base = node.module.split('.')[0]
            if base in ("hashlib", "zlib", "binascii"):
                self.add_violation(node, "fingerprint", f"Importing from {node.module} is forbidden")
            if base in ("subprocess", "ctypes"):
                self.add_violation(node, "process-escape", f"Importing from {node.module} is forbidden")
            if base in ("socket", "requests", "ftplib", "smtplib") or node.module.startswith("urllib") or node.module.startswith("http.client"):
                self.add_violation(node, "network", f"Importing from {node.module} is forbidden")
        self.generic_visit(node)

    def _check_source_target(self, node: ast.AST, arg: ast.AST):
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            val = arg.value
            if val.endswith(".py") or any(val.startswith(root) for root in self.source_roots):
                self.add_violation(node, "source-read", f"Reading source file {val} is forbidden")
        elif isinstance(arg, ast.JoinedStr):
            # Very conservative: if it's dynamic, we just flag it if any part looks like a py extension or root
            pass # We could check if any part contains .py, but for now we only check literal constants to avoid false positives

    def visit_Call(self, node: ast.Call):
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        
        full_name = self._get_full_name(node.func)

        # process-escape
        if full_name in ("os.system", "os.popen", "os._exit", "sys.exit") or full_name.startswith("os.exec") or full_name.startswith("os.spawn"):
            self.add_violation(node, "process-escape", f"Calling {full_name} is forbidden")
        
        # source-read
        if full_name == "io.open" or full_name.startswith("inspect.getsource") or full_name == "inspect.getfile" or (isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "linecache"):
            self.add_violation(node, "source-read", f"Calling {full_name} is forbidden")
        if func_name in ("open", "read_text", "read_bytes"):
            if node.args:
                self._check_source_target(node, node.args[0])

        # skip
        if full_name == "pytest.skip":
            self.add_violation(node, "skip", "pytest.skip is forbidden")

        # xfail
        if full_name == "pytest.xfail":
            reason = next((k.value.value for k in node.keywords if k.arg == "reason" and isinstance(k.value, ast.Constant) and isinstance(k.value.value, str)), "")
            if not reason.startswith("possible bug: "):
                self.add_violation(node, "xfail-reason", "xfail without reason='possible bug: ...' is forbidden")

        # unseeded-random
        if full_name == "time.sleep":
            self.add_violation(node, "unseeded-random", "Calling time.sleep is forbidden")
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name) and node.func.value.id == "random":
            if func_name == "seed":
                self.has_random_seed = True
            else:
                self.random_calls.append(node)

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if node.name.startswith("pytest_"):
            self.add_violation(node, "pytest-hook", f"Defining {node.name} is forbidden")
        
        is_conftest = Path(self.file_path).name == "conftest.py"
        if is_conftest:
            has_fixture = any(
                (isinstance(d, ast.Name) and d.id == "fixture") or 
                (isinstance(d, ast.Attribute) and isinstance(d.value, ast.Name) and d.value.id == "pytest" and d.attr == "fixture") or
                (isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and isinstance(d.func.value, ast.Name) and d.func.value.id == "pytest" and d.func.attr == "fixture") or
                (isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == "fixture")
                for d in node.decorator_list
            )
            if not has_fixture:
                self.add_violation(node, "pytest-hook", "In conftest.py, only fixtures are allowed")

        if node.name.startswith("test_"):
            has_assert = False
            for child in ast.walk(node):
                if isinstance(child, ast.Assert):
                    has_assert = True
                    break
                if isinstance(child, ast.Call):
                    full = ""
                    if isinstance(child.func, ast.Attribute) and isinstance(child.func.value, ast.Name):
                        full = f"{child.func.value.id}.{child.func.attr}"
                    if full in ("pytest.raises", "pytest.warns"):
                        has_assert = True
                        break
            if not has_assert:
                self.add_violation(node, "assert-free", f"Test {node.name} has no assert or pytest.raises")

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "pytest_plugins":
                self.add_violation(node, "pytest-hook", "Assigning to pytest_plugins is forbidden")
        
        is_conftest = Path(self.file_path).name == "conftest.py"
        if is_conftest:
            if not (isinstance(node.value, ast.Constant) or isinstance(node.value, ast.List) or isinstance(node.value, ast.Dict) or isinstance(node.value, ast.Tuple) or isinstance(node.value, ast.Set)):
                # We only allow imports, constants, and fixtures in conftest.
                self.add_violation(node, "pytest-hook", "In conftest.py, only constants, imports, and fixtures are allowed")
        self.generic_visit(node)

    def _get_full_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            val = self._get_full_name(node.value)
            return f"{val}.{node.attr}" if val else node.attr
        return ""

    def _check_decorators(self, node):
        for dec in node.decorator_list:
            f = dec.func if isinstance(dec, ast.Call) else dec
            full = self._get_full_name(f)
            
            if full in ("pytest.mark.skip", "pytest.mark.skipif"):
                self.add_violation(node, "skip", f"Decorator {full} is forbidden")
            
            if full == "pytest.mark.xfail":
                reason = ""
                if isinstance(dec, ast.Call):
                    reason = next((k.value.value for k in dec.keywords if k.arg == "reason" and isinstance(k.value, ast.Constant) and isinstance(k.value.value, str)), "")
                if not reason.startswith("possible bug: "):
                    self.add_violation(node, "xfail-reason", "xfail without reason='possible bug: ...' is forbidden")

    def visit_ClassDef(self, node: ast.ClassDef):
        self._check_decorators(node)
        is_conftest = Path(self.file_path).name == "conftest.py"
        if is_conftest:
            self.add_violation(node, "pytest-hook", "Classes are not allowed in conftest.py")
        self.generic_visit(node)
        
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.visit_FunctionDef(node)


def check_test_source(content: str, file_path: str, *, source_roots: list[str]) -> list[PolicyViolation]:
    """AST-only check of a test file the model wants to write. Never executes it."""
    try:
        tree = ast.parse(content, filename=file_path)
    except SyntaxError:
        return []

    visitor = PolicyVisitor(file_path, source_roots)
    visitor.visit(tree)
    
    # Check decorators for all functions (including test functions)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            visitor._check_decorators(node)

    if visitor.random_calls and not visitor.has_random_seed:
        for call in visitor.random_calls:
            visitor.add_violation(call, "unseeded-random", "random.* calls with no random.seed(...) are forbidden")

    return visitor.violations
