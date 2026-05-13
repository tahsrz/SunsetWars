import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'PulseCommunicator'))
from evaluator import MetacircularEvaluator, parse_lisp

def main():
    cart_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cartridges')
    evaluator = MetacircularEvaluator(cart_dir)
    print("--- test_repl REPL ---")
    while True:
        try:
            line = input("test_repl> ")
            if line.lower() == 'exit': break
            print(evaluator.eval(parse_lisp(line)))
        except Exception as e: print(f"Error: {e}")
if __name__ == "__main__": main()