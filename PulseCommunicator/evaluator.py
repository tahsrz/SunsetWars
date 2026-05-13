import sys
import os

# Add builder to path for TAHQuery
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'builder'))
from tah_query import TAHQuery

class MetacircularEvaluator:
    """
    SICP Metacircular Evaluator for TAH Queries.
    Syntax: (QUERY "cartridge_name" "terms")
    """
    def __init__(self, cartridge_dir):
        self.cartridge_dir = cartridge_dir
        self.env = {
            'QUERY': self.primitive_query,
            'VERSION': lambda: "TAH-EVAL v1.0",
            'LIST-CARTRIDGES': self.list_cartridges
        }

    def eval(self, exp):
        """The core eval loop."""
        if isinstance(exp, str):
            # Atomic symbol/keyword
            return self.env.get(exp.upper(), exp)
        elif not isinstance(exp, list):
            # Constant (number, string)
            return exp
        
        # Procedure call: (operator operand1 operand2 ...)
        procedure = self.eval(exp[0])
        args = [self.eval(arg) for arg in exp[1:]]
        
        if callable(procedure):
            return procedure(*args)
        raise ValueError(f"Unknown procedure: {exp[0]}")

    def primitive_query(self, cartridge_name, terms):
        """Primitive for TAH retrieval."""
        # Clean quotes from Lisp parser if they exist
        cartridge_name = cartridge_name.strip('"\'')
        terms = terms.strip('"\'')
        
        path = os.path.join(self.cartridge_dir, f"{cartridge_name}.tah")
        if not os.path.exists(path):
            return f"Error: Cartridge {cartridge_name} not found."
        
        query_engine = TAHQuery(path)
        results = query_engine.get_matches(terms)
        query_engine.close()
        return results

    def list_cartridges(self):
        return [f.replace('.tah', '') for f in os.listdir(self.cartridge_dir) if f.endswith('.tah')]

def parse_lisp(s):
    """Simple parser to turn (A B C) into ['A', 'B', 'C']."""
    s = s.replace('(', ' ( ').replace(')', ' ) ')
    tokens = s.split()
    def read_tokens(tokens):
        if not tokens: return None
        token = tokens.pop(0)
        if token == '(':
            L = []
            while tokens[0] != ')':
                L.append(read_tokens(tokens))
            tokens.pop(0) # pop ')'
            return L
        return token
    return read_tokens(tokens)

if __name__ == "__main__":
    cart_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cartridges')
    evaluator = MetacircularEvaluator(cart_dir)
    
    # Example Execution
    print("--- TAH Metacircular Evaluator ---")
    query = '(QUERY "user_memories" "coffee")'
    print(f"Eval: {query}")
    print(f"Result: {evaluator.eval(parse_lisp(query))}")
