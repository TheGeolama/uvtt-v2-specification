# Universal Visibility Flags and Cross-Entity Event Targeting

## 1. Introduction

In the UVTT v2 standard, a map is not just a static painting; it is a state machine. This document defines the two core systems that VTT developers must implement to support interactive maps:

1. **Universal Visibility Flags:** The permissions system that dictates who can see and interact with an object.
2. **Cross-Entity Targeting:** The event-driven architecture that allows one object (like a pressure plate) to change the state of another (like a locked door).

---

## 2. Universal Visibility Flags

Every single object in the v2 schema—whether it is a CAD vector in `geometry.json` (like a Wall or Portal) or an interactive point in `entities.json` (like a Light, Spawn, or Event)—must support the `visibility` property.

### 2.1 The Three States

VTT rendering pipelines must strictly respect these three string values:

- **`"visible"` (Default):** The object is fully rendered and broadcast to all connected clients. Players can see the wall, hear the audio zone, or trigger the event.
- **`"gm_only"`:** The object is loaded into the VTT, but the rendering and audio pipelines must **mask it from player clients**. It is only visible/audible on the Game Master's client.
  - _Use Cases:_ Hidden trap triggers, secret doors, invisible light sources used for ambient mood, or GM reference notes.
- **`"hidden"`:** The object is completely disabled for _everyone_ (including the GM's physical rendering, though it should remain selectable in a layer list). It casts no light, blocks no vision, and triggers no events.
  - _Use Cases:_ Multi-phase boss fight geometry, collapsed tunnels, or deactivated traps.

### 2.2 Security Implementation Note

To prevent tech-savvy players from sniffing network traffic to find secret doors, a compliant VTT server should ideally strip `gm_only` objects from the payload before transmitting the JSON to player clients.

---

## 3. Cross-Entity Event Targeting

The v2 standard allows entities to trigger state changes in other objects. This is handled via the `events` array in `entities.json`.

An Event is essentially a spatial trigger zone (a point with a radius). When a token interacts with it, it fires a payload at a `target_id`. Because UUIDs are unique across the entire `.uvtt2z` archive, an Event can target _anything_—a light, a portal, or a spawn.

### 3.1 The Event Schema

Here is the structure of an Event designed to act as a pressure plate that opens a locked door:

```json
{
  "events": [
    {
      "id": "uuid-event-9999",
      "x": 250,
      "y": 250,
      "trigger_radius": 50,
      "trigger_type": "on_enter",
      "visibility": "gm_only",
      "targets": [
        {
          "target_id": "uuid-portal-5678",
          "action": "set_state",
          "value": "open"
        }
      ]
    }
  ]
}
```
