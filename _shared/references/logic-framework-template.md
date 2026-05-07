# Logic Framework Diagram Template

Use this reference when a report needs a compact logic framework diagram for state transitions, lifecycle rules, gate decisions, or recovery semantics. The source exemplars are Ares Figure 8.2 and Figure 8.3:

- Signal Delivery: `queued -> dispatching -> published`, with `failed -> queued` retry and stale `dispatching -> queued` recovery.
- Execution Task: `created -> risk-eval -> decision`, with `allow -> placed`, `block -> blocked`, and `clamp` handled as adjusted execution.

The reusable principle is: make invariants visible in the diagram, not only in prose.

## Core Pattern

A logic framework diagram answers one question: what states exist, which transitions are legal, and which guard or invariant controls the transition?

Required properties:

- 3 to 7 state nodes.
- Directed arrows for legal transitions only.
- Short verb labels on arrows, such as `claim`, `publish`, `error`, `retry`, `evaluate`, `allow`, `block`.
- Decision nodes for gates, not ordinary process nodes.
- Dashed arrows for recovery, retry, timeout, or compensation paths.
- A caption that states the governing invariant, not merely the object name.
- One sentence after the figure explaining the operational consequence.

## When To Use

Use this template for:

- entity lifecycle diagrams
- task status machines
- approval or risk-gate logic
- retry and stale-state recovery
- contract-level constraints such as "only state X can be consumed"

Do not use this template for cross-module message order. Use `sequence-diagram-template.md` when order across actors is the main question.

## State Machine Template

This template models a lifecycle with a retry or recovery path.

```latex
\begin{figure}[H]
\centering
\begin{tikzpicture}[
  node distance=2cm,
  every node/.style={font=\footnotesize}
]
\node[reportnode] (queued) {queued};
\node[reportnode, right=of queued] (active) {active};
\node[reportnode, right=of active] (done) {done};
\node[reportnode, below=of active] (failed) {failed};

\draw[reportarrow, ->] (queued) -- node[midway, above, font=\tiny] {claim} (active);
\draw[reportarrow, ->] (active) -- node[midway, above, font=\tiny] {publish} (done);
\draw[reportarrow, ->] (active) -- node[midway, right, font=\tiny] {error} (failed);
\draw[reportarrow, ->, dashed] (failed) -- node[midway, below, font=\tiny] {retry} (queued);
\draw[reportarrow, ->, dashed, bend left=18] (active) to
  node[midway, above, font=\tiny] {timeout / stale} (queued);
\end{tikzpicture}
\caption{[实体] 状态转换。关键约束：只有 \texttt{done} 状态才能被下游消费；\texttt{active} 超过阈值时间会被回收重新变为 \texttt{queued}。}
\label{fig:<entity>-state}
\end{figure}
```

After the figure:

```latex
图~\ref{fig:<entity>-state} 表明该实体的下游可见性由状态机控制；恢复路径只回到可重新处理的安全状态。
```

## Gate Decision Template

This template models a task whose next state depends on a blocking decision.

```latex
\begin{figure}[H]
\centering
\begin{tikzpicture}[
  node distance=2cm,
  every node/.style={font=\footnotesize}
]
\node[reportnode] (created) {created};
\node[reportnode, right=of created] (eval) {evaluating};
\node[reportdecision, right=of eval] (gate) {Gate};
\node[reportnode, above right=of gate] (passed) {passed};
\node[reportnode, right=of gate] (adjusted) {adjusted};
\node[reportnode, below right=of gate] (blocked) {blocked};

\draw[reportarrow, ->] (created) -- node[midway, above, font=\tiny] {hydrate} (eval);
\draw[reportarrow, ->] (eval) -- node[midway, above, font=\tiny] {evaluate} (gate);
\draw[reportarrow, ->] (gate) -- node[midway, above left, font=\tiny] {allow} (passed);
\draw[reportarrow, ->] (gate) -- node[midway, above, font=\tiny] {clamp} (adjusted);
\draw[reportarrow, ->] (gate) -- node[midway, below left, font=\tiny] {block} (blocked);
\end{tikzpicture}
\caption{[任务] 状态转换。[门禁] 是阻塞点：\texttt{allow} 进入后续动作，\texttt{block} 终止执行，\texttt{clamp} 走调整后动作。}
\label{fig:<task>-state}
\end{figure}
```

After the figure:

```latex
图~\ref{fig:<task>-state} 表明门禁裁决改变后续状态空间；任何未被显式建模的分支都不应由下游自行解释。
```

## Caption Patterns

Use conclusion-oriented captions:

- `图 X. [实体] 状态转换。关键约束：只有 [state] 状态才能被下游消费；[transient state] 超过阈值时间会被回收重新变为 [safe state]。`
- `图 X. [任务] 状态转换。[门禁] 是阻塞点：[allow] 进入 [action]，[block] 终止执行，[clamp] 走调整后分支。`
- `图 X. [对象] 逻辑框架，突出 [约束] 如何决定 [后续行为]。`

## Audit Checklist

Mark a logic framework diagram as weak if any item is missing:

- It shows states but omits the invariant that makes the states meaningful.
- It shows arrows without verb labels.
- It uses the same visual style for normal transitions and recovery paths.
- It draws a gate as a process node instead of a decision node.
- It mentions retry, timeout, or stale recovery in prose but omits it from the diagram.
- It hides a terminating branch such as `block`, `reject`, `failed`, or `cancelled`.
- Its caption names the figure but does not state the key constraint.
- It mixes lifecycle state with cross-module timing; split into a logic framework diagram and a sequence diagram.
