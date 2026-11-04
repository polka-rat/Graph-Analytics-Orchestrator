# Part A: Bootcamp

Do this before Part B. It teaches the tool contract (needed for Part B) and LLM function calling (needed for the project). Expect 4 to 6 hours. Run every command from the repository root.

## 1. Set up

Follow **Setup** in the main README, then run `python smoke_test.py`. Every check must pass, including the LLM one.

## 2. Build `node_degree`

Edit `bootcamp/node_degree/tool.py` and `bootcamp/node_degree/tool.json`.

**What it must do.** Given `graph_id` and `node` (a node id), return how many edges touch the node:

- Undirected graph: `result` is `{"id": ..., "label": ..., "degree": <number of neighbours>}`.
- Directed graph: `result` is `{"id": ..., "label": ..., "out_degree": ..., "in_degree": ..., "degree": <out + in>}`.
- `summary` is one plain sentence, e.g. `Chennai International Airport (MAA) has 28 outgoing and 27 incoming edges.`
- An unknown node, unknown graph or unknown parameter returns `error(...)`, never a crash. For an unknown node, say how to fix it (use `lookup_node`).

**The manifest.** Replace every `TODO` and `YOUR_ID` in `tool.json`. The description is what the LLM reads when it decides whether to call your tool, so say what the tool computes, which questions it answers, and what it returns on

 directed and undirected graphs. Add an example on a directed graph.

**Check it:**

```
python run_tool.py bootcamp/node_degree graph_id=airports node=MAA
python -m graphkit.validate bootcamp/node_degree
python -m pytest tests/bootcamp
```

All tests must pass.

## 3. Call it from an LLM

Complete the `answer()` function in `bootcamp/bootcamp_agent.py`; the comments there walk you through the loop. Test on one question first, to save your free-tier quota:

```
python bootcamp/bootcamp_agent.py --only 1
python bootcamp/bootcamp_agent.py
```

Each question's trace is written to `bootcamp/traces/q<N>.jsonl`. Read your traces: does each answer actually follow from the tool calls?

## 4. Reflect

Fill in `bootcamp/reflection.md` (150 to 250 words) about one thing that went wrong or surprised you. Things worth trying if everything went smoothly: ask about "Bombay" instead of Mumbai, a city that is not in the data, or a question no tool can answer.

## Submit (Moodle, by Mon, Oct 26, 11:59 PM IST)

Upload one zip of the `bootcamp/` folder, containing:

- `node_degree/tool.py` and `node_degree/tool.json`
- `bootcamp_agent.py`
- `traces/q1.jsonl`, `traces/q2.jsonl`, `traces/q3.jsonl`
- `reflection.md`

Do not include your `.env` file or API key.
