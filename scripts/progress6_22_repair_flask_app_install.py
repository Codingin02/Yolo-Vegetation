import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLASK_APP = ROOT / "src" / "ulp_project" / "flask_app.py"

MARKER_START = "PROGRESS 6.22 VISION API RUNTIME START"
MARKER_END = "PROGRESS 6.22 VISION API RUNTIME END"

text = FLASK_APP.read_text(encoding="utf-8")

# Bersihkan patch 6.22 lama kalau ada.
if MARKER_START in text and MARKER_END in text:
    lines = text.splitlines()
    cleaned = []
    skip = False
    for line in lines:
        if MARKER_START in line:
            skip = True
            continue
        if MARKER_END in line:
            skip = False
            continue
        if not skip:
            cleaned.append(line)
    text = "\n".join(cleaned).rstrip() + "\n"
    FLASK_APP.write_text(text, encoding="utf-8")

tree = ast.parse(text)

create_app = None
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name == "create_app":
        create_app = node
        break

if create_app is None:
    raise SystemExit("CREATE_APP_FUNCTION_NOT_FOUND")

return_nodes = [n for n in ast.walk(create_app) if isinstance(n, ast.Return)]
return_app_nodes = []

for node in return_nodes:
    value = node.value
    if isinstance(value, ast.Name) and value.id == "app":
        return_app_nodes.append(node)

if not return_app_nodes:
    raise SystemExit("RETURN_APP_INSIDE_CREATE_APP_NOT_FOUND")

return_node = sorted(return_app_nodes, key=lambda n: n.lineno)[-1]
lines = text.splitlines()
return_line = lines[return_node.lineno - 1]
indent = return_line[:len(return_line) - len(return_line.lstrip())]

if len(indent) == 0:
    raise SystemExit("RETURN_APP_INDENT_ZERO_STOP")

install_lines = [
    indent + "# PROGRESS 6.22 VISION API RUNTIME START",
    indent + "try:",
    indent + "    from ulp_project.progress6_22_vision_api_runtime import install_progress6_22_vision_api_runtime",
    indent + "    install_progress6_22_vision_api_runtime(app)",
    indent + "except Exception as _progress6_22_vision_error:",
    indent + "    try:",
    indent + "        app.logger.exception(" + repr("PROGRESS_6_22_VISION_API_RUNTIME_INSTALL_FAILED: %s") + ", _progress6_22_vision_error)",
    indent + "    except Exception:",
    indent + "        pass",
    indent + "# PROGRESS 6.22 VISION API RUNTIME END",
]

new_lines = lines[:return_node.lineno - 1] + install_lines + lines[return_node.lineno - 1:]
new_text = "\n".join(new_lines).rstrip() + "\n"

FLASK_APP.write_text(new_text, encoding="utf-8")

ast.parse(new_text)

print("PATCHED_FLASK_APP_INSIDE_CREATE_APP")
print(f"RETURN_APP_LINE_WAS={return_node.lineno}")
print(f"INDENT_LEN={len(indent)}")
