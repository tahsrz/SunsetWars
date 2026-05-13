import sys
import os

# Add PulseCommunicator to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'PulseCommunicator'))
from evaluator import MetacircularEvaluator, parse_lisp

def main():
    cart_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cartridges')
    evaluator = MetacircularEvaluator(cart_dir)
    
    print("--- TAH Lisp Shell v1.0 ---")
    print("Commands: (QUERY \"cartridge\" \"term\"), (LIST-CARTRIDGES), (VERSION)")
    print("Type 'exit' to quit.")
    
    while True:
        try:
            line = input("tah> ")
            if line.lower() == 'exit':
                break
            if not line.strip():
                continue
                
            exp = parse_lisp(line)
            result = evaluator.eval(exp)
            
            if isinstance(result, list):
                for item in result:
                    print(f"\n{item}")
            else:
                print(f"\n{result}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
