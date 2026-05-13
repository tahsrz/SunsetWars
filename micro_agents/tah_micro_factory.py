import os
import sys

TEMPLATES = {
    "repl": """
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'PulseCommunicator'))
from evaluator import MetacircularEvaluator, parse_lisp

def main():
    cart_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cartridges')
    evaluator = MetacircularEvaluator(cart_dir)
    print("--- {name} REPL ---")
    while True:
        try:
            line = input("{name}> ")
            if line.lower() == 'exit': break
            print(evaluator.eval(parse_lisp(line)))
        except Exception as e: print(f"Error: {{e}}")
if __name__ == "__main__": main()
""",
    "gate": """
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'builder'))
from tah_query import TAHQuery

def check_gate(cartridge, term):
    path = os.path.join('cartridges', f"{{cartridge}}.tah")
    query = TAHQuery(path)
    # Check Bloom Filter first
    if query.bloom.check(term):
        print(f"[GATE] '{{term}}' potentially present in {{cartridge}}.")
        return True
    print(f"[GATE] '{{term}}' definitely NOT in {{cartridge}}.")
    return False

if __name__ == "__main__":
    check_gate(sys.argv[1], sys.argv[2])
"""
}

def main():
    if len(sys.argv) < 3:
        print("Usage: python tah_micro_factory.py <template_type> <agent_name>")
        print(f"Available templates: {', '.join(TEMPLATES.keys())}")
        return

    tpl_type = sys.argv[1]
    name = sys.argv[2]
    
    if tpl_type not in TEMPLATES:
        print(f"Error: Unknown template '{tpl_type}'")
        return

    content = TEMPLATES[tpl_type].format(name=name)
    file_path = f"micro_agents/{name}.py"
    
    with open(file_path, "w") as f:
        f.write(content.strip())
    
    print(f"Successfully generated micro-agent: {file_path}")

if __name__ == "__main__":
    main()
