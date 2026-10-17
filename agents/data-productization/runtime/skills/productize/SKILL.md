---
name: productize
description: Gather business requirements, discover relevant sources, and build or evolve a deployed Vulcan data product.
---

# Business conversation

For every new request or modification:

1. Establish the decision/problem, intended users and desired numbers or outputs. Reuse what the user already said.
2. Discover accessible Depots and existing products with CLI/MCP. Inspect connection metadata, tables and columns using the configured source tools. Present relevant choices with their business meaning; ask which to use when ambiguous.
3. Clarify definitions that change the answer: what counts as revenue, which records qualify, reporting detail, date/time meaning, refresh frequency, historical range and intended consumption. Ask only applicable questions, in small batches.
4. Infer joins, model structure and implementation from inspected metadata and Vulcan documentation. Ask about ambiguous business meaning; summarize material assumptions without requiring a formal specification sign-off.
5. Build or update, deploy, verify and explain where the product is available. Retain product context for follow-up changes.

Users choose between understandable options. Git, Secrets, compute selection, engine configuration and permissions are preconfigured or discovered by the service.
