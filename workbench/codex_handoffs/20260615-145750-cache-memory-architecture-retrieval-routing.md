You are Codex working inside the SunsetWars repository.
Use the retrieved TAH/Memoria context below as priority ground truth before reading large source files.
Cite cartridge names when the retrieved context materially informs your answer or implementation.

USER QUERY: cache memory architecture retrieval routing

RETRIEVAL METADATA:
{
  "tokens": [
    "cache",
    "memory",
    "architecture"
  ],
  "concepts": [
    "computer hardware",
    "data storage",
    "system design"
  ],
  "intent": "retrieve information",
  "ollamaModel": "phi4-mini:latest",
  "fallbackReason": null,
  "atlasDiagnostics": {
    "totalSegments": 25,
    "visitedSegments": 10,
    "rejectedSegments": 0,
    "candidateExperts": 7,
    "payloadReads": 7,
    "routeIndex": 3,
    "routeKey": 272503790756741888,
    "targetComplexity": 0.9444444444444444,
    "binaryTrace": [
      {
        "mid": 12,
        "keyMin": 274197113995318188,
        "keyMax": 274197113995449260,
        "decision": "target-lower",
        "discardedSegments": 13
      },
      {
        "mid": 5,
        "keyMin": 274161379865318276,
        "keyMax": 274161921033393036,
        "decision": "target-lower",
        "discardedSegments": 7
      },
      {
        "mid": 2,
        "keyMin": 271944764289503628,
        "keyMax": 271945305455383428,
        "decision": "target-higher",
        "discardedSegments": 3
      },
      {
        "mid": 3,
        "keyMin": 271945305455513996,
        "keyMax": 274161371143394180,
        "decision": "match",
        "discardedSegments": 0
      }
    ],
    "discardedLowerSegments": 3,
    "discardedUpperSegments": 20,
    "rejectedByReason": {},
    "fallbackUsed": false
  }
}

RETRIEVED TAH CONTEXT:
No matching TAH context was retrieved.

TASK:
Answer or implement the user query using this context, then verify the result in the repo.