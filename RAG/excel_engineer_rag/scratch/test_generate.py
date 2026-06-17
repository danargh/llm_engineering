import json
import re
from graphlib import TopologicalSorter
import sys
import os

# Add parent to path for excel_rag
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from excel_rag.formula_utils import excel_formula_to_js_hint, extract_references
except ImportError:
    # mock it
    def excel_formula_to_js_hint(f): return str(f).replace("=", "", 1)
    def extract_references(f): return []

def make_safe_var(name):
    # 'Units Converter'!B2 -> Units_Converter_B2
    s = str(name).replace("'", "").replace(" ", "_").replace("!", "_")
    return re.sub(r'[^A-Za-z0-9_]', '', s)

def generate():
    cells = {}
    with open("index/vibration_cells_full.jsonl", "r") as f:
        for line in f:
            c = json.loads(line)
            cells[c["address"]] = c

    # graph
    ts = TopologicalSorter()
    safe_vars = {}
    
    # We will build a set of all required inputs
    inputs = set()
    formula_nodes = set()

    for addr, c in cells.items():
        # register cell
        safe_addr = make_safe_var(addr)
        safe_vars[addr] = safe_addr
        
        formula = c.get("formula", "")
        if formula:
            formula_nodes.add(addr)
            deps = c.get("dependencies", [])
            if not deps:
                # Try extracting if not present
                deps = extract_references(formula)
                
            for d in deps:
                # Add edges
                ts.add(addr, d)
                if d not in cells:
                    inputs.add(d)
        else:
            inputs.add(addr)
            ts.add(addr) # no dependencies

    try:
        ordered = list(ts.static_order())
    except Exception as e:
        print("Cycle detected", e)
        ordered = list(cells.keys()) # fallback
        
    print(f"Total ordered nodes: {len(ordered)}")
    print(f"Total explicit inputs: {len(inputs)}")
    print(f"Total formula nodes: {len(formula_nodes)}")
    
    # Generate JS
    js_lines = []
    js_lines.append("/**")
    js_lines.append(" * Vibration Calculation Module")
    js_lines.append(" */")
    js_lines.append("")
    js_lines.append("export function calculateVibration(inputs) {")
    
    for node in ordered:
        safe_node = make_safe_var(node)
        if node in inputs:
            js_lines.append(f"    let {safe_node} = inputs.{safe_node};")
        elif node in formula_nodes:
            c = cells[node]
            hint = excel_formula_to_js_hint(c["formula"])
            # Replace variables in hint
            # This is very naive, just for prototype
            deps = c.get("dependencies", [])
            for d in sorted(deps, key=len, reverse=True):
                safe_d = make_safe_var(d)
                hint = hint.replace(d, safe_d)
            js_lines.append(f"    let {safe_node} = {hint}; // {c.get('label', '')}")
            
    js_lines.append("    return {")
    for node in formula_nodes:
        safe_node = make_safe_var(node)
        js_lines.append(f"        {safe_node}: {safe_node},")
    js_lines.append("    };")
    js_lines.append("}")
    
    with open("vibration-module.js", "w") as f:
        f.write("\n".join(js_lines))
        
    print("Wrote vibration-module.js")

if __name__ == "__main__":
    generate()
