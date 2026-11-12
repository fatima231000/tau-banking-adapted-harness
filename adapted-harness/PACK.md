# τ-Banking agent harness: technical handoff pack

**Goal:** Find the knowledge representations, retrieval strategies, harness maintenance approaches, and balance between exploration and exploitation that best enable agents to work effectively. Exploration means seeking new information, resolving uncertainty, and investigating alternatives; exploitation means using established knowledge, procedures, and lessons from previous executions. The harness should help the model decide when to rely on what it knows and when to investigate further, while keeping its knowledge and memory current. The goal is not to beat the benchmark. Use τ-Banking as a limited test environment to develop and assess these approaches.

**Assignment:** Develop a harness that helps the agent use information effectively, exploring knowledge representation, retrieval, maintenance, and the balance between exploration and exploitation.

**Two-hour session:** We want to see two things. The first is engineering: how you iterate on DEV, inspecting failures, choosing an improvement, trying it, and using the results to guide the next iteration. The second is productionizing: what it would take to run your harness for real customers and keep changing it safely, which we'll discuss together. The directions below are pointers, not a checklist; you are not expected to cover them all. Focus on the areas that seem most useful based on what you observe. Test runs can continue beyond the two-hour window.

API credentials will be shared separately through 1Password. Setup, the baseline configuration and a DEV baseline run with readable traces are in [README.md](README.md).

## 1. What is τ-bench?

τ-bench evaluates an agent interacting with a simulated user and domain-specific tools under policy instructions. The agent must gather information, converse, and act to complete a customer request. The original release covered retail and airline tasks; later releases expanded the benchmark family. [1, 2]

The relevant target here is **τ-Banking, the banking domain introduced by τ-Knowledge**, available as `banking_knowledge`. It combines a banking knowledge base with tools that change account-related state. It is distinct from the original τ-bench release. [2, 3]

## 2. What does it measure?

The original benchmark evaluates outcomes by comparing the resulting database state against the task's expected outcome. Its reliability metric, **pass^k**, measures success across all k repeated attempts, rather than whether any one attempt succeeds. Pass^1 is single-attempt success; pass^k is different from best-of-k/pass@k. [1]

τ-Banking tests whether an agent can retrieve and apply information while conducting a conversation and producing the required state changes. Its corpus contains 698 documents across 21 product categories, approximately 195,000 tokens. The challenge combines document retrieval, policy reasoning, tool discovery and execution, and dependencies between steps. Some tools must first be discovered through documentation. [3]

A task is successful when the agent's actions result in a final database state that matches the task's expected database state. [5, Section 3]

### Current benchmark harness

The τ-Banking harness runs a conversation between an agent and a simulated customer. The agent receives instructions and tool access, retrieves banking policies and procedures from the knowledge base, and uses tool responses and conversation history to decide what to do next. Some tools must be located in the documentation and unlocked before use. Tool calls can update the simulated banking environment; the evaluator checks the resulting outcome against the task requirements. [1–3]

The framework supports configurable knowledge-access strategies, including embedding-based retrieval, keyword search, long-context processing, and filesystem exploration. The selected retrieval strategy, agent model, prompts, simulator, and execution budgets together define the baseline configuration. [2, 4]

In the **terminal setup**, the knowledge base is available as files, and the agent uses a shell tool with commands such as `grep`, `cat`, and `find` to locate policies and tool documentation. Banking operations still happen through the environment's banking tools; the terminal provides a way to find the information needed to use them. [5, Section 5]

**Providing all tools upfront** would mean putting every banking tool's definition directly in the agent's available tool list. In the paper's setup, some tools are available initially, while others must be discovered through the knowledge base before they can be invoked. The agent therefore has to find both the applicable procedure and the capability needed to carry it out. Terminal versus retrieval search concerns how the agent accesses knowledge; all-tools-upfront versus discoverable tools concerns which capabilities are exposed initially. [5, Section 3]

## 3. What we need you to develop

Build a harness that helps the agent answer: What do I know? What is still unknown? Which rules apply? What can I do next? What will that change? How will I verify the result?

Start from the baseline and let its failures decide what you build. Depending on what you see, some directions you might take (none is required):

- how knowledge is represented and retrieved;
- what the agent checks before it acts;
- how the agent keeps track of state and recovers when something unexpected happens;
- what the agent learns and remembers from earlier runs;
- how failures are diagnosed;
- how the harness stays current as policies change.

One rule: information only the grader sees (the hidden customer instructions, the expected actions, the backend database) must never become agent input.

## 4. Limited evaluation plan and deliverables

Use the following project splits. SMOKE is a subset of DEV, not a separate held-out set. Iterate on DEV; keep TEST frozen and use it only at milestones. Do not run the full benchmark or launch broad repeated evaluations as part of routine development.

| Split | Size | Purpose and use |
| --- | --- | --- |
| SMOKE | 6 | Pipeline check: confirm setup, retrieval, tool execution, logging, and grading work end to end. |
| DEV | 24 | Failure analysis and unrestricted iteration on representations and the harness. Use targeted reruns for the failure being addressed. |
| TEST | 37 | Frozen evaluation at milestones only. Freeze the harness, representations, and memory before each run. |

### SMOKE (6): pipeline check

```text
task_014 task_024 task_057 task_072 task_081 task_087
```

### DEV (24): failure analysis, iterate freely

```text
task_014 task_015 task_016 task_018 task_024 task_026 task_028 task_048 task_057 task_066 task_070 task_071 task_072 task_074 task_075 task_078 task_081 task_082 task_083 task_084 task_087 task_098 task_099 task_101
```

### TEST (37): frozen, milestones only

```text
task_001 task_002 task_003 task_004 task_007 task_010 task_025 task_027 task_031 task_033 task_034 task_035 task_036 task_038 task_039 task_040 task_043 task_045 task_047 task_051 task_052 task_053 task_054 task_056 task_058 task_059 task_061 task_064 task_067 task_068 task_069 task_088 task_089 task_093 task_095 task_096 task_097
```

### Evaluation procedure

1. **Start from the recorded baseline.** The baseline configuration (domain, split IDs, agent and user-simulator models, retrieval configuration) is recorded in [README.md](README.md), and a DEV baseline run is provided. Record any change you make to the configuration, prompts or budgets. The TEST list contains 37 unique tasks and has no overlap with DEV. We hold a TEST baseline for comparison.
2. **Check the pipeline with SMOKE.** Before the session, establish that the pipeline runs on your machine and produces usable traces.
3. **Iterate on DEV.** Diagnose a concrete failure, change the relevant representation or harness component, and rerun affected cases. Use component comparisons only when they answer a specific design question. Build reusable memory from DEV executions.
4. **Evaluate TEST at milestones only.** Record the milestone and run budget in advance. Freeze the harness and all derived representations and memory before execution. Keep TEST cases out of development memory and task-specific tuning; do not rerun TEST after each change. Keep hidden user instructions, expected actions, and evaluator-only state out of agent context.
5. **Report representation and maintenance quality first.** Assess source grounding, state consistency, dependency handling, uncertainty, update/invalidation behavior, trace completeness, and the ability to diagnose failures. Include task outcomes, costs, and latency as supporting diagnostics. Label results by the actual split; do not present subset results as full-benchmark scores. Repeated-run reliability is optional and limited to a planned milestone budget.
6. **Keep adaptation experiments on DEV.** If changing policies or testing cross-execution learning, specify the changes, task order, reset rules, and available feedback. Freeze the resulting memory for TEST. Independent repeated trials must not learn from one another.

## 5. What to share

For this session, share:

- the harness changes you made, as commits on your own branch;
- a brief account of your DEV iterations: what failed, what you changed, what you observed, and what you would try next;
- your view on productionizing, as a short note or simply in the discussion.

Include available results and identify any TEST runs still in progress. Those runs can finish after the session.

**Success for this session:** show thoughtful iteration across DEV, using observed failures to improve how the harness supports the agent, and a credible view of what it would take to run and change that harness in production. Explain your choices and what you learned. The directions above are pointers for this work, not required deliverables within two hours.

## Sources

1. [Original τ-bench paper](https://arxiv.org/abs/2406.12045).
2. [Official τ-bench code and documentation](https://github.com/sierra-research/tau2-bench).
3. [Official τ-Knowledge overview and banking walkthrough](https://taubench.com/blog/tau-knowledge.html).
4. [Sierra: τ³-Bench knowledge and voice release](https://sierra.ai/blog/bench-advancing-agent-benchmarking-to-knowledge-and-voice).
5. [τ-Knowledge paper](https://arxiv.org/abs/2603.04370).
