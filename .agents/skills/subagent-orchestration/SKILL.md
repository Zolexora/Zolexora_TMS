---
name: subagent-orchestration
description: Guidelines and patterns for orchestrating parallel subagents, managing background tasks, and reactive message handling in Google Antigravity.
---

# Subagent Orchestration & Background Task Management

This skill guides the Antigravity agent on how to effectively distribute tasks across subagents and manage asynchronous background execution.

## 1. When to Invoke Subagents

- **`research` subagent**: Use for broad repository exploration, deep code auditing, or reading multiple documentation files. Keeps the parent agent's context clean and focused.
- **`self` subagent**: Use when a complex task requires full capabilities (command execution, code writing) within an isolated context branch.
- **Custom Subagents (`define_subagent`)**: Define specialized agents with specific system prompts and tool subsets when repetitive or distinct roles are needed (e.g., Code Reviewer, Database Migrator).

## 2. Communication & Reactive Wakeup

- **Do NOT poll in a loop**: The Antigravity environment uses a reactive event model. Once a background task or subagent is launched, do not run loops checking status. The system will automatically wake up and resume execution when:
  - A subagent sends a message (`send_message`).
  - A background task completes or emits output.
- **Stop Calling Tools to Yield**: After launching background work, simply stop making tool calls to allow the environment to wait for events.

## 3. Delays and Recurring Actions

- **Never use `sleep` in shell commands**: Background sleep commands waste resources and create zombie processes.
- **Use the `schedule` Tool**:
  - One-shot timers: Use `DurationSeconds` with appropriate `TimerCondition` (`any`, sender ID, or `never`).
  - Recurring tasks: Use `CronExpression` to execute tasks on a schedule.

## 4. Worktree and Branch Modes

- `inherit`: Subagent operates directly in the parent workspace.
- `share`: Subagent operates in a shared repository worktree without duplicating storage.
- `branch`: Subagent operates in an isolated branch.
