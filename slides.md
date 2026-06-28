# WA\* at w=1.5 — The Reopen Cost Trap

A three-slide walkthrough of how a bounded-suboptimal WA\* search (w = 1.5) on the 15-puzzle gets trapped by an inflated g-cost, and how an `allow_reopen=True` policy rescues it.

---

## Slide 1 — The Greedy Detour

```mermaid
graph LR
    classDef startEnd  fill:#A2C2E8,stroke:#333,stroke-width:2px
    classDef process   fill:#F0F4F8,stroke:#4A6B82,stroke-width:2px
    classDef closed    fill:#ffb3b3,stroke:#cc0000,stroke-width:2px
    classDef stuck     fill:#e6e6e6,stroke:#999,stroke-width:2px,stroke-dasharray: 5 5

    START((START)):::startEnd

    GREEDY_SEARCH["greedy_path_discovery\nWeight bias forces fast expansion"]:::process
    NODE_X["node_x\nAdded to Closed List\nContains high g-cost, low h-cost"]:::closed

    PROPAGATE_COST["cost_propagation\nChildren inherit faulty g-cost"]:::process
    CHILDREN_STUCK["open_list_descendants\nf-cost inflated\nPushed to bottom of priority queue"]:::stuck

    END_GOAL((GOAL)):::startEnd

    START --> GREEDY_SEARCH --> NODE_X
    NODE_X --> PROPAGATE_COST --> CHILDREN_STUCK
    CHILDREN_STUCK ~~~ END_GOAL
```

**Key points**
- Weighted heuristic drives a greedy, suboptimal dive
- Node X closes with an inflated g-cost
- Descendants starve at the bottom of the queue

**Speaker notes**

This first slide sets up the trap. Because WA\* multiplies the heuristic by w = 1.5, the search is biased toward nodes that *look* close to the goal — those with a low h-cost — even when the path to reach them is expensive. The algorithm races down a greedy path and commits Node X to the Closed List carrying a high g-cost (the actual path cost so far) but a low h-cost (the estimated distance remaining). That low h-cost is exactly why it was expanded early.

The problem is that the inflated g-cost doesn't stay local. Every child of Node X inherits it through cost propagation, so their f-cost (g plus weighted h) is inflated as well. These descendants get pushed to the bottom of the priority queue and effectively go dormant. The true, cheaper path to this region of the puzzle hasn't been found yet — so the search is poised to wander. The dashed link to the goal signals that the descendants *could* reach it, but right now they have no priority to do so.

---

## Slide 2 — Locked Out, Wandering

```mermaid
graph LR
    classDef startEnd  fill:#A2C2E8,stroke:#333,stroke-width:2px
    classDef process   fill:#F0F4F8,stroke:#4A6B82,stroke-width:2px
    classDef router    fill:#FFEAA7,stroke:#D6A2E8,stroke-width:2px
    classDef waste     fill:#FFF3CD,stroke:#FFC107,stroke-width:2px
    classDef stuck     fill:#e6e6e6,stroke:#999,stroke-width:2px,stroke-dasharray: 5 5

    START((START)):::startEnd

    QUEUE_CHECK{queue_status?}:::router
    CHILDREN_STUCK["open_list_descendants\nDeferred due to high f-cost"]:::stuck

    BLIND_SEARCH["branch_exploration\nAlgorithm pivots to alternate paths"]:::process
    RESOURCE_WASTE["massive_node_expansion\nWasteful exploration of irrelevant states\nTotal: 58,579 Expansions"]:::waste

    EXHAUSTION_ROUTE{options_exhausted?}:::router

    END_GOAL((GOAL)):::startEnd

    START --> QUEUE_CHECK
    QUEUE_CHECK -- "prioritize low f-cost" --> BLIND_SEARCH
    BLIND_SEARCH --> RESOURCE_WASTE --> EXHAUSTION_ROUTE

    EXHAUSTION_ROUTE -- "no options left" --> CHILDREN_STUCK
    QUEUE_CHECK -. "deferred" .-> CHILDREN_STUCK

    CHILDREN_STUCK --> END_GOAL
```

**Key points**
- No-reopen locks Node X permanently in Closed
- Search wastes 58,579 expansions on dead branches
- Inflated descendants reached only as a last resort

**Speaker notes**

This is the trap fully sprung, under the strict `allow_reopen = False` policy. When the priority queue is checked, the starved descendants of Node X have such high f-cost that the queue always prefers something else. So the search pivots into branch exploration — alternate regions of the state space that look cheaper but lead nowhere useful.

Because Node X is locked in the Closed List and can never be reconsidered, there's no mechanism to correct its inflated g-cost. The algorithm grinds through massive, irrelevant node expansion — 58,579 expansions in total — before its options are finally exhausted. Only then does it fall back to the deferred descendants and route through to the goal. The path is still valid and within the suboptimality bound, but the cost in work is enormous. The dotted "deferred" edge is the whole story: those children were always there, just never competitive enough to be picked until everything else was gone.

---

## Slide 3 — Reopen and Bypass

```mermaid
graph LR
    classDef startEnd  fill:#A2C2E8,stroke:#333,stroke-width:2px
    classDef process   fill:#F0F4F8,stroke:#4A6B82,stroke-width:2px
    classDef router    fill:#FFEAA7,stroke:#D6A2E8,stroke-width:2px
    classDef reopen    fill:#D4EDDA,stroke:#28A745,stroke-width:2px
    classDef fastTrack fill:#E3F2FD,stroke:#1E88E5,stroke-width:2px
    classDef abandoned fill:#f2f2f2,stroke:#ccc,stroke-width:1px,stroke-dasharray: 5 5

    START((START)):::startEnd

    NEW_PATH["new_path_discovery\nShorter route to Node X found"]:::process
    COST_CHECK{g_cost_improved?}:::router

    ABANDONED_BRANCH["branch_exploration\nIrrelevant branches"]:::abandoned

    REOPEN_NODE["node_x_reopen\nExtracted from Closed List\ng-cost heavily reduced"]:::reopen

    UPDATE_CHILDREN["update_descendants\nNew f-cost calculated\nNodes jump to head of queue"]:::fastTrack

    GOAL_RUSH["direct_path_execution\nBypasses dead-ends entirely\nTotal: 52,063 Expansions"]:::fastTrack

    END_GOAL((GOAL)):::startEnd

    START --> NEW_PATH --> COST_CHECK

    COST_CHECK -- "no" --> ABANDONED_BRANCH
    COST_CHECK -- "yes (allow_reopen=True)" --> REOPEN_NODE

    REOPEN_NODE --> UPDATE_CHILDREN --> GOAL_RUSH --> END_GOAL
```

**Key points**
- Cheaper path triggers a g-cost improvement check
- Node X reopens; descendants jump the queue
- Wasteful branches bypassed — 52,063 expansions

**Speaker notes**

Now we flip to `allow_reopen = True`, and the trap dissolves. As the search proceeds it discovers a shorter route to Node X. The router asks a single decisive question: does this new path improve the g-cost of an already-closed node? If not, that branch is abandoned as irrelevant. But here the answer is yes — so the algorithm extracts Node X from the Closed List and heavily reduces its g-cost.

That correction cascades. The descendants get a freshly computed f-cost, and because their g-cost is no longer inflated, they jump to the head of the priority queue instead of languishing at the bottom. The search then executes the direct path to the goal, bypassing the dead-end branches entirely. The payoff is concrete: expansions drop from 58,579 under no-reopen to 52,063 with reopen — roughly 6,500 fewer expansions, about an 11% reduction. The lesson is that with weighted heuristics, the ability to revisit closed nodes isn't a minor optimization; it's what keeps an early greedy mistake from dominating the entire search.
