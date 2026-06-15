# Sunset Wars Runtime Magic Matrix

## Purpose

Sunset Wars should treat prompt-style slot aggregation as the editor-facing form of a runtime behavior system. The same idea used for Roles, Skills, and Behaviors can become a combat loadout matrix where each equipped module contributes a small, validated payload to the active spell profile.

The design goal is not to stream rich item objects through the combat loop. The UI can keep names, rarity, descriptions, drag state, and inventory metadata. The runtime should receive a compact payload that can hot-swap active spell behavior with predictable cost.

## Core Model

The player equips four modules into fixed spell slots:

| Slot | Name | Responsibility |
| :--- | :--- | :--- |
| `0` | Core | Damage family, scaling baseline, affinity rules |
| `1` | Trajectory | Projectile, beam, cone, orbit, trap, or area delivery |
| `2` | Modifier A | Mechanical mutation such as split, pierce, chain, linger |
| `3` | Modifier B | Secondary mutation, resonance, cost tradeoff, or passive hook |

Fixed slots are intentional. A tuple is cheaper and less ambiguous than a dynamic object during combat, and it maps cleanly to UE5 arrays, replicated structs, and deterministic save payloads.

```ts
export type SpellSlot = 0 | 1 | 2 | 3;

export interface MagicModule {
  id: string;
  name: string;
  slot: SpellSlot;
  complexityCost: number;
  systemFlags: number;
  payload: {
    baseDamage?: number;
    speedModifier?: number;
    projectileCount?: number;
    aoeRadius?: number;
    statusEffectId?: number;
    vfxIndex: number;
  };
}

export interface PlayerActiveMatrix {
  maxTokenCapacity: number;
  currentComplexity: number;
  slots: [
    MagicModule | null,
    MagicModule | null,
    MagicModule | null,
    MagicModule | null
  ];
}
```

## Runtime Payload Boundary

The active combat system should compile equipped modules into a lean payload before execution. This gives the editor, Zustand store, backend, and UE5 bridge a shared contract without forcing each frame to walk inventory objects.

```ts
export interface CompiledSpellPayload {
  version: 1;
  moduleIds: [string | null, string | null, string | null, string | null];
  complexity: number;
  flags: number;
  baseDamage: number;
  speedMultiplier: number;
  projectileCount: number;
  aoeRadius: number;
  statusEffectIds: number[];
  vfxIndices: number[];
}
```

Compile rules:

- `complexity` is the sum of equipped module costs.
- `flags` is the bitwise OR of `systemFlags`.
- Numeric payload fields use explicit defaults, then apply additive or multiplicative modifiers.
- `statusEffectIds` and `vfxIndices` are compact integer references into engine-side tables.
- The compiler rejects payloads above `maxTokenCapacity` instead of letting an overloaded spell reach the execution loop.

## TAH Block Shape

Sunset Wars can store magic modules as TAH-indexed knowledge shards while exporting runtime payloads as strict blocks. The important split is:

- `.tah/.hat` cartridge: searchable design intelligence, module descriptions, balance notes, source history.
- Runtime magic block: compact behavior data used by gameplay code.

Example authoring block:

```tah
@@sunset_wars.magic_module
id: ember_core
slot: 0
complexityCost: 18
systemFlags: 0x0001
payload.baseDamage: 22
payload.vfxIndex: 4
tags: fire, core, burn, starter
summary: Fire core that establishes direct heat damage and unlocks burn synergies.
@@end
```

Example compiled block:

```json
{
  "version": 1,
  "moduleIds": ["ember_core", "helix_trajectory", "split_modifier", null],
  "complexity": 67,
  "flags": 19,
  "baseDamage": 22,
  "speedMultiplier": 1.15,
  "projectileCount": 3,
  "aoeRadius": 0,
  "statusEffectIds": [2],
  "vfxIndices": [4, 11, 19]
}
```

## Zustand Store Boundary

Use Zustand for editor and loadout interaction, not as the combat runtime. The store owns inventory, selected modules, capacity warnings, and compiled preview state. Combat receives only `CompiledSpellPayload`.

```ts
import { create } from 'zustand';

interface MagicMatrixState {
  equipped: PlayerActiveMatrix['slots'];
  inventory: MagicModule[];
  maxTokenCapacity: number;
  currentComplexity: number;
  compiled: CompiledSpellPayload;
  equipModule: (module: MagicModule) => boolean;
  unequipSlot: (slot: SpellSlot) => void;
}
```

The store should return `false` from `equipModule` when the loadout would exceed capacity. UI can show the overload warning, but the state should remain valid.

## UE5 Bridge

For Unreal, mirror the compiled payload as a small struct:

```cpp
USTRUCT(BlueprintType)
struct FSunsetCompiledSpellPayload
{
  GENERATED_BODY()

  UPROPERTY(BlueprintReadOnly) int32 Version = 1;
  UPROPERTY(BlueprintReadOnly) int32 Complexity = 0;
  UPROPERTY(BlueprintReadOnly) int32 Flags = 0;
  UPROPERTY(BlueprintReadOnly) float BaseDamage = 0.0f;
  UPROPERTY(BlueprintReadOnly) float SpeedMultiplier = 1.0f;
  UPROPERTY(BlueprintReadOnly) int32 ProjectileCount = 1;
  UPROPERTY(BlueprintReadOnly) float AoeRadius = 0.0f;
  UPROPERTY(BlueprintReadOnly) TArray<int32> StatusEffectIds;
  UPROPERTY(BlueprintReadOnly) TArray<int32> VfxIndices;
};
```

Execution loop responsibilities:

- Projectile handlers read trajectory and count from compiled values.
- Damage handlers read base damage, flags, and status IDs.
- VFX handlers resolve `vfxIndices` against Niagara or material parameter tables.
- Replication sends module IDs or compiled payload depending on prediction needs.

## Bitmask Guidance

Reserve low bits for common execution behavior and higher bits for rare/special systems:

| Bit | Flag |
| :--- | :--- |
| `0x0001` | Fire affinity |
| `0x0002` | Frost affinity |
| `0x0004` | Arcane affinity |
| `0x0008` | Void affinity |
| `0x0010` | Multi-projectile |
| `0x0020` | Area effect |
| `0x0040` | Applies status |
| `0x0080` | Persistent field |
| `0x0100` | Homing or tracking |
| `0x0200` | Resource refund or drain mutation |

## Implementation Path

1. Keep module authoring expressive and searchable in TAH-backed shards.
2. Compile selected modules into a strict JSON payload for TypeScript and UE5.
3. Use fixed slots for hot-swapping and deterministic replication.
4. Use capacity/complexity as the balancing equivalent of token budget.
5. Treat VFX, status effects, projectile classes, and shader behavior as integer table references in the runtime payload.

This gives Sunset Wars the same compositional strength as prompt-slot systems while turning the final export into an active spell-casting profile instead of a text prompt.
