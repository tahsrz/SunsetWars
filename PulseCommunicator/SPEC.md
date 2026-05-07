# PulseCommunicator Specification (SICP Edition)

## 1. The Stream Abstraction (Async Messaging)
The communicator treats all incoming data (from terminal, builder, or external hooks) as **Delayed Sequences (Streams)**.
- **Constructor**: `cons-stream(a, b)` implemented via C# `IEnumerable` or Python `yield`.
- **Logic**: Decouple the *time* at which a message is produced from the *time* it is processed. This allows the TAH terminal to remain responsive while heavy binary seeks occur in the background.

## 2. The Metacircular Evaluator (Query Engine)
Instead of static query parsing, the communicator implements a lightweight evaluator to handle polymorphic retrieval.
- **The Loop**: `eval(exp, env)` -> `apply(proc, args)`.
- **Environment**: Maps query keywords to specific TAH cartridges and retrieval strategies (e.g., BM25 for text, Haversine for coords).
- **Extensibility**: Users can define new "Tactical Procedures" (e.g., `(find-near "Dallas" :radius 50)`) without recompiling the terminal.

## 3. Directory Structure
- `/PulseCommunicator/streams`: Messaging logic.
- `/PulseCommunicator/evaluator`: The query engine.
- `/PulseCommunicator/bridge.py`: The top-level coordinator.
