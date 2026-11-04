# Published Class Tool Registry (Assignment 3 / Group Project)

This directory contains the collected, anonymized tool implementations submitted by students for **Assignment 3: Graph Analytics Tools**. These tools form the shared toolbox for the group project.

---

## Directory Structure

```text
tools/
├── <tool_name>/
│   ├── <implementation_ID>/
│   │   ├── tool.py       # Main algorithm entry point: run(store, graph_id, **params)
│   │   ├── tool.json     # Tool manifest schema and description
│   │   └── README.md     # Documentation and usage instructions
│   └── ...
```

- Each tool is grouped under its official menu name from Assignment 3 (e.g. `betweenness_centrality`, `louvain`, `reachability`, etc.).
- Folder names within each tool correspond to an anonymized ID.
- Every tool adheres to the standard GraphKit tool contract.


---

## How to Use in Your Group Project

To incorporate this registry into your group project starter kit:
- Copy the contents of `tools/` into your project's `registry/tools/` folder.