# Graph Tools Starter: Assignment 3

Everything you need for Assignment 3: a graph store with five datasets, four provided tools, a tool template, a contract validator, and the Part A bootcamp. The class registry of tools lives in this repository too, under `registry/tools/`.

## Setup

You need Python 3.10 or later and Git.

1. **Get the code.** Unzip the provided `graph-tools-starter.zip` package and navigate into the folder:
   ```
   cd graph-tools-starter
   ```
2. **Create an environment and install the packages:**
   ```
   python -m venv .venv
   # PowerShell:
   .\.venv\Scripts\Activate.ps1
   # Command Prompt:
   .venv\Scripts\activate.bat
   # Git Bash:
   source .venv/Scripts/activate
   pip install -r requirements.txt
   ```
3. **Get a free LLM API key.** The default is Google Gemini: create a key at [Google AI Studio](https://aistudio.google.com/apikey). Copy `.env.example` to `.env` and paste the key into `LLM_API_KEY`. `.env.example` also shows how to use Groq, OpenRouter or Ollama instead. **Never commit `.env` or put a key in your code.**
4. **Run the smoke test:**
   ```
   python smoke_test.py
   ```
   Every check should pass. If only the LLM check fails, check your key and model name, or try another provider.

Run all commands from the repository root.

## What is in here

| Path | What it is |
| --- | --- |
| `graphkit/` | The shared library: graph store, contract helpers, validator, LLM and trace helpers. Do not edit it. |
| `data/` | The datasets; see [data/README.md](data/README.md). |
| `infra_tools/` | Four provided tools: `list_graphs`, `lookup_node`, `node_attributes`, `filter_nodes`. |
| `template/` | The starting point for your Part B tools. |
| `bootcamp/` | Part A; see [bootcamp/README.md](bootcamp/README.md). |
| `registry/tools/` | The class registry: everyone's Part B tools. |
| `tests/` | Tests for the provided code and for Part A. |
| `run_tool.py` | Run any tool from the command line. |
| `smoke_test.py` | Checks your setup. |

## The graph store

Tools never load files. They get graphs from the store they are given:

```python
g = store.get("airports")          # a read-only Graph
g.directed, g.weighted              # booleans
g.nodes()                           # list of node ids
g.number_of_nodes(), g.number_of_edges()
g.out_neighbors("MAA")              # {neighbour_id: weight} for edges leaving MAA
g.in_neighbors("MAA")               # {neighbour_id: weight} for edges arriving at MAA
g.undirected_neighbors("MAA")       # neighbours ignoring direction
g.edges()                           # iterator of (u, v, weight); an undirected edge appears once
g.weight("MAA", "DEL")              # weight, or None if there is no edge
g.label("MAA"), g.node_attrs("MAA") # "Chennai International Airport", {"label": ..., "city": ...}

sub_id = store.subgraph("airports", ["MAA", "DEL", "BOM"], "Three Indian airports")
sub_id = store.edge_subgraph("airports", [("MAA", "DEL")], "One route")
```

For undirected graphs, `out_neighbors`, `in_neighbors` and `neighbors` are the same. Unweighted graphs report weight 1.0.

## The tool contract

A tool is a folder with `tool.json` (the manifest the LLM reads) and `tool.py` (with `def run(store, graph_id, **params)`). `run` returns a dict built with `ok(...)` or `error(...)` from `graphkit.contract`:

```json
{"status": "ok", "result": [{"id": "MAA", "label": "Chennai International Airport", "score": 0.031}],
 "summary": "Chennai International Airport ranks first of 500 airports.",
 "result_graph_id": null, "error": null}
```

The full rules are in the assignment handout and at the top of `template/tool.py`. The validator checks them:

```
python -m graphkit.validate path/to/tool_folder
```

`tool.json` needs `name`, `implementation_id` (`<name>.<your_id>`), `author`, `tier`, `category`, `description`, `parameters` (JSON Schema) and `examples`: at least one example call, which the validator runs.

## Part B: your tools

1. Copy the template to your folder in the registry:
   ```
   cp -r template registry/tools/<tool_name>/<your_id>
   ```
   Use the exact tool name from the menu and your student id.
2. Write `tool.py`, `tool.json`, `README.md` and at least five tests in `tests/`. Implement the algorithm yourself: the standard library, NumPy and `graphkit` only. NetworkX is allowed in your tests, as the reference to compare with.
3. Check it:
   ```
   python -m graphkit.validate registry/tools/<tool_name>/<your_id>
   python -m pytest registry/tools/<tool_name>/<your_id>/tests
   python run_tool.py registry/tools/<tool_name>/<your_id> graph_id=airports top_k=5
   ```
4. **Submit via Zip.** Package your `bootcamp/` folder (including traces) and your `registry/tools/<tool_name>/<your_id>` folder into your submission zip file and upload it to the course portal. (Do not include `.env` or `.venv`).

Correctness is graded on hidden tests against NetworkX, on the provided datasets that suit your tool. Your tool must finish within 30 seconds on `airports`, the largest; algorithms that are inherently slow (such as Girvan–Newman) are tested on the small graphs only.

## Free-tier tips

- Free tiers allow only a limited number of requests per minute and per day; Google AI Studio shows your project's limits. Test one question at a time (`--only 1`) before running all of them.
- If you hit a limit, wait, or switch provider in `.env`.
- Smaller models call tools less reliably. If the model ignores tools or invents arguments, try a larger one.
