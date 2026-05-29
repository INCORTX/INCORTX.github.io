
### 2026-05-29 Post-Mortem (Widget Styling & Math Animation Fixes)
- **PROBLEM**: Pitch Synthesizer "Waveform Shape" buttons overflowed on small screens; UI colors misleading. s1-canvas animation failed to show bottleneck.
- **FAILED**: Using inline `display: flex;` with `flex: 1` caused wrapped buttons (Triangle) to stretch wildly across the full width of the row.
- **ROOT CAUSE**: Flexbox with `flex:1` greedily expands items on wrapped lines. Missing `flex-wrap: wrap` initially caused horizontal clipping.
- **SOLUTION**: Replaced flex wrapper with **CSS Grid (`grid-template-columns: 1fr 1fr`)** to enforce strict 2x2 symmetry. Fixed animation math and fixed sine shift `(t - 0.5)` logic.
- **NEXT TIME**: When designing 4-button groups inside constrained responsive grids, default to `display: grid; grid-template-columns: 1fr 1fr` rather than `flex-wrap` to guarantee uniform element sizes.
