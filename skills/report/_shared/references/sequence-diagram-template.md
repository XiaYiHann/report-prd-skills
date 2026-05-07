# Sequence Diagram Template

Use this reference when a report needs a canonical sequence diagram or a mainline architecture figure for an execution path. The source exemplar is the Ares signal-to-order chain: Signal Agent -> API -> Redis -> Worker -> Risk -> Exchange. The reusable principle is the grammar, not the domain vocabulary.

## Core Pattern

A strong sequence diagram answers one question: in what order do actors exchange messages, and where does execution stop until a decision returns?

Required properties:

- 4 to 8 participants, arranged left to right in execution order.
- One vertical lifeline per participant.
- A numbered main path from trigger to durable side effect.
- Explicit self-steps for local validation, deduplication, persistence, hydration, or materialization.
- One visually obvious blocking decision point before the irreversible action.
- A return arrow from the decision owner to the orchestrator.
- A caption that names the object and states the governing conclusion.
- One short paragraph after the figure that states what the reader should remember.

The Ares exemplar can be summarized as:

```text
Signal Agent -> API -> Redis -> Worker -> Risk -> Exchange
trigger -> validate/persist -> enqueue -> consume/workflow -> evaluate -> allow/block/clamp -> submit order
```

## Canonical Narrative Wrapper

Before the figure:

```latex
图~\ref{fig:<slug>} 回答的问题是：[动作] 从外部触发到最终落地，跨模块的消息顺序与返回路径是什么？
```

Figure wrapper:

```latex
\begin{figure}[H]
\centering
\input{figures/<slug>.tex}%
\caption{[对象] 的跨模块时序图，突出 [阻塞决策点] 是 [不可逆动作] 前的阻塞决策点。}
\label{fig:<slug>}
\end{figure}
```

After the figure:

```latex
读者应带走的判断是：[阻塞决策点] 属于主路径同步裁决；任何拒绝裁决都会终止后续 [不可逆动作]，任何调整裁决都必须把调整后的参数显式传回编排方。
```

## TikZ Template

Prefer direct coordinates for final TikZ figures. Keep the spacing readable and avoid adding branches to the main path.

```latex
\begin{tikzpicture}[
  x=2.55cm,
  y=0.72cm,
  every node/.style={font=\footnotesize},
  participant/.style={reportnode, minimum width=1.55cm, align=center},
  lifeline/.style={draw=ReportGray, dashed},
  msg/.style={reportarrow, ->},
  ret/.style={reportarrow, <-}
]

% Participants
\node[participant] (actor) at (0,0) {Actor};
\node[participant] (api)   at (1,0) {API};
\node[participant] (queue) at (2,0) {Queue};
\node[participant] (orc)   at (3,0) {Worker};
\node[participant] (gate)  at (4,0) {Gate};
\node[participant] (side)  at (5,0) {Side\\Effect};

% Lifelines
\foreach \x in {0,1,2,3,4,5} {
  \draw[lifeline] (\x,-0.4) -- (\x,-8.0);
}

% Main path
\draw[msg] (0,-0.9) -- node[above, font=\tiny] {1. trigger} (1,-0.9);
\draw[msg] (1,-1.5) -- ++(0,-0.55)
  node[midway, right, font=\tiny] {2. validate + persist};
\draw[msg] (1,-2.5) -- ++(0,-0.55)
  node[midway, right, font=\tiny] {3. fan-out / create task};
\draw[msg] (1,-3.3) -- node[above, font=\tiny] {4. enqueue} (2,-3.3);
\draw[msg] (2,-4.1) -- node[above, font=\tiny] {5. consume} (3,-4.1);
\draw[msg] (3,-4.7) -- ++(0,-0.55)
  node[midway, right, font=\tiny] {6. start workflow};
\draw[msg] (3,-5.7) -- ++(0,-0.55)
  node[midway, right, font=\tiny] {7. hydrate + materialize};
\draw[msg] (3,-6.5) -- node[above, font=\tiny] {8. evaluate} (4,-6.5);
\draw[ret] (3,-7.2) -- node[above, font=\tiny] {9. allow / block / clamp} (4,-7.2);
\draw[msg] (3,-7.8) -- node[above, font=\tiny] {10. irreversible action} (5,-7.8);
\end{tikzpicture}
```

## Audit Checklist

When auditing a report sequence diagram, mark it as weak if any item is missing:

- The diagram has no explicit question before it.
- Participants exceed 8 without a split into overview and detail.
- The diagram mixes static architecture boundaries with runtime order.
- A decision point is shown as an ordinary step when it blocks later execution.
- The return value of the decision is omitted.
- Failure branches crowd the main path instead of being moved to an exception table or secondary figure.
- The caption describes the picture but does not state the conclusion.
- The paragraph after the figure fails to explain the operational implication.

## Mainline Architecture Figure Template

Use this when the section needs an architecture or workflow overview before the detailed sequence diagram. This figure answers: what are the major stages, and which stage gates the irreversible action?

Canonical shape:

```text
Trigger -> Ingest -> Queue/Delivery -> Orchestrate -> Gate Decision -> Side Effect
```

Rules:

- Draw the gate as a decision node, not a generic process node.
- Place the gate immediately before the irreversible or externally visible action.
- Keep the figure to 5 to 7 nodes.
- Caption pattern: `图 X. [对象] 的主链路，突出 [门禁] 是 [动作] 前的阻塞决策点。`
- Pair it with a sequence diagram when the report also needs to explain message order.

Do not use the architecture figure as a substitute for the sequence diagram. The architecture figure explains boundary and stage; the sequence diagram explains order and return semantics.
