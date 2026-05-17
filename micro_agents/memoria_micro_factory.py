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
from memoria_query import MemoriaQuery

def check_gate(vault_name, term):
    path = os.path.join('cartridges', f"{vault_name}.hat")
    query = MemoriaQuery(path)
    # Check Global Bloom Filter first
    if query.contains_keyword(term):
        print(f"[MEMORIA-GATE] '{term}' potentially present in {vault_name}.")
        return True
    print(f"[MEMORIA-GATE] '{term}' definitely NOT in {vault_name}.")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python {name}.py <vault_name> <term>")
    else:
        check_gate(sys.argv[1], sys.argv[2])
"""
}

def main():
    if len(sys.argv) < 3:
        print("Usage: python micro_agents/memoria_micro_factory.py <template_type> <agent_name>")
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
