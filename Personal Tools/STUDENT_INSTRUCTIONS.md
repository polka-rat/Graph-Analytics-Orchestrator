# Assignment 3: Student Instructions & Workflow Guide

This guide summarizes what you need to build, where to write your code, what files you must **not** touch, and how to submit your work via zip.

---

## 1. Quick Setup

1. **Unzip the starter package** and open a terminal in the `graph-tools-starter` root directory.
2. **Set up Python environment (Python 3.10+)**:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # Windows Command Prompt:
   .venv\Scripts\activate.bat
   # Windows Git Bash:
   source .venv/Scripts/activate
   # Linux / macOS:
   source .venv/bin/activate

   pip install -r requirements.txt
   ```
3. **Configure your free LLM API key**:
   - Copy `.env.example` to `.env` (never commit or share this file).
   - Get a free Gemini key from [Google AI Studio](https://aistudio.google.com/apikey).
   - Paste your key into `LLM_API_KEY=` in `.env`.
4. **Verify your setup**:
   ```bash
   python smoke_test.py
   ```
   All checks must pass before you begin.

---

## 2. Where to Write Your Code

### Part A: Bootcamp (Do This First)
All Part A work lives strictly inside the `bootcamp/` folder:

| File to Edit | Task |
| :--- | :--- |
| `bootcamp/node_degree/tool.py` | Implement connection counting: `degree` for undirected graphs, and `out_degree`, `in_degree`, `degree` for directed graphs. |
| `bootcamp/node_degree/tool.json` | Complete the manifest: fill in your student ID, tool description, parameters, and examples. |
| `bootcamp/bootcamp_agent.py` | Implement the agent loop in `answer()` to call tools using function calling against `questions.txt`. |
| `bootcamp/reflection.md` | A 150–250 word reflection on one error, surprise, or recovery that occurred while running your agent. |

**How to test Part A:**
```bash
# Test your node_degree tool
python run_tool.py bootcamp/node_degree graph_id=airports node=MAA
python -m graphkit.validate bootcamp/node_degree
python -m pytest tests/bootcamp

# Run your agent and generate traces (use --only 1 to test single questions)
python bootcamp/bootcamp_agent.py --only 1
python bootcamp/bootcamp_agent.py
```
*Traces will be automatically generated at `bootcamp/traces/q1.jsonl`, `q2.jsonl`, and `q3.jsonl`.*

---

### Part B: Your Allocated Tools (Registry Submission)
Implement the graph algorithm(s) allocated to you:

1. **Create your tool folder**:
   Copy the `template/` folder into `registry/tools/` using your exact tool name and student ID:
   ```text
   registry/tools/<tool_name>/<your_student_id>/
       ├── tool.py
       ├── tool.json
       ├── README.md
       └── tests/
           └── test_<tool_name>.py
   ```
2. **Implement your algorithm**:
   - Write the algorithm yourself in pure Python and standard NumPy.
   - Write at least **five unit tests** in `tests/test_<tool_name>.py` (NetworkX is permitted in `tests/` to verify correctness).
3. **Validate your tool locally**:
   ```bash
   python -m graphkit.validate registry/tools/<tool_name>/<your_student_id>
   python -m pytest registry/tools/<tool_name>/<your_student_id>/tests
   python run_tool.py registry/tools/<tool_name>/<your_student_id> graph_id=karate
   ```

---

## 3. What You Must NOT Touch

Automated grading enforces strict boundaries:
* ❌ **DO NOT edit `graphkit/`**: This is the shared standard library. Any modifications will break when your tool is evaluated in the instructor grading suite.
* ❌ **DO NOT edit `infra_tools/` or `data/`**: These are read-only datasets and helper tools provided to everyone.
* ❌ **DO NOT import NetworkX in `tool.py`**: You may only import NetworkX inside `tests/` for verification against ground truth. Your algorithm in `tool.py` must be written by you.
* ❌ **DO NOT perform disk file I/O or network calls**: Tools must only access graphs via `store.get(graph_id)` and must never open `.csv` or `.dat` files directly.

---

## 4. Academic Integrity & Automated Verification Checks

Submissions are evaluated through an automated test and grading suite. Note the following strict requirements:

1. **No External Graph Libraries**: Static AST inspection will scan `tool.py` for any hidden or inline imports of `networkx`, `scipy.sparse`, `igraph`, or `graph_tool`.
2. **Deterministic Output & Tie-Breaking**:
   - For all ranking/top-$k$ tools: if two nodes have identical scores, **ties must be broken by sorting `node id` in ascending order**.
   - Floats must be rounded to **6 decimal places** (`round(score, 6)`).
3. **Contract Adherence**:
   - All returned nodes must be formatted as dictionaries using `node_ref(g, node, ...)`, containing both `"id"` and `"label"`.
   - Never crash with an unhandled exception. Return `error("helpful error message")` instead.
4. **Authentic Traces & Reflection Grounding**:
   - `bootcamp/traces/q1..3.jsonl` are audited for authentic LLM tool calling. Synthetic, truncated, or fabricated traces will fail the trace audit.
   - Your `bootcamp/reflection.md` **must cite an exact line number and timestamp** from one of your generated trace files.

---

## 5. Submission Instructions (Zip Format)

You will **not** push to GitHub. You will submit your assignment as a single `.zip` file on the course portal (Moodle/Canvas).

### What to include in your submission zip:
```text
your_student_id.zip
├── bootcamp/
│   ├── node_degree/
│   │   ├── tool.py
│   │   └── tool.json
│   ├── bootcamp_agent.py
│   ├── traces/
│   │   ├── q1.jsonl
│   │   ├── q2.jsonl
│   │   └── q3.jsonl
│   └── reflection.md
└── registry/
    └── tools/
        └── <tool_name>/
            └── <your_student_id>/
                ├── tool.py
                ├── tool.json
                ├── README.md
                └── tests/
                    └── test_<tool_name>.py
```

⚠️ **CRITICAL WARNING**:
- **DO NOT include your `.env` file** (never share your private API key).
- **DO NOT include `.venv/`, `__pycache__/`, or `.pytest_cache/`**.

After the deadline, all student tool folders in `registry/tools/` will be collected, validated, and merged into a unified class registry for the Group Project.
