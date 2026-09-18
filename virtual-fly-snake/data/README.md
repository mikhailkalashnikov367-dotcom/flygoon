# Graph data

`example_vfb_graph.json` is a tiny schema-valid demo graph so the project runs offline. It is **not** a claim about real VFB connectivity.

To use actual Virtual Fly Brain data, export or query a selected, documented subgraph and save it as an edge-list JSON. Preserve stable VFB identifiers, connection weights if available, and provenance (query, release/date, filtering, aggregation). Then pass its path to `--graph`.
