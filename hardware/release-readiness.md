# Hardware release readiness matrix

**Current state: engineering definition only — not ready for fabrication.**

| Deliverable | State | What is needed to call it complete |
|---|---|---|
| Product architecture | Drafted | Review against deployment country and actual meter interface |
| Requirements: telemetry, AI, billing, tamper | Drafted | Confirm units, retention, forecast horizon, tariff/legal model |
| Controller and interface concept | Candidate | Confirm module SKU, memory, antenna keep-out and firmware needs |
| Cellular modem | Not selected | Confirm deployment country/operator, LTE bands, SIM/eSIM and certification |
| Power architecture | Provisional | Confirm external DC range, battery autonomy and environmental range |
| Native schematic | Not yet produced/verified | Create in KiCad with real symbols, footprints, values, power and protection circuitry; run ERC |
| Native PCB | Not yet produced/verified | Place actual footprints, route, define stack-up and RF/power zones; run DRC |
| 3D assembled and exploded views | Not yet produced/verified | Export from the checked PCB with verified 3D models; conceptual artwork is not a substitute |
| BOM | Preliminary | Exact manufacturer part numbers, lifecycle, availability, alternates and assembly notes |
| Gerbers and drill files | Not released | Export from checked PCB and inspect outputs against fabricator requirements |
| Pick-and-place / assembly drawing | Not released | Generate from final footprints and verify rotations/origins |
| Electrical bench verification | Not run | Build isolated low-voltage test fixture and record results |
| Radio validation | Not run | Test actual modem/SIM/operator/bands and antenna in intended region |
| Product certification | Not done | Qualified review of metrology, gas safety, EMC, radio, cybersecurity and local law |

## Release rule

Do not label the design manufacturing-ready until native CAD exists, ERC/DRC results are reviewed, generated manufacturing files are inspected, and the prototype has passed its recorded bench tests. A green software workflow alone does not prove electrical safety, RF performance, metrology accuracy or regulatory compliance.

## Safe first prototype

- Synthetic pulse generator only.
- Isolated low-voltage power and input.
- No live gas installation, mains wiring, unknown sensor signals or valve-control outputs.
- No purchase or fabrication without explicit owner approval.
