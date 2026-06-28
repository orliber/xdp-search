1A. Initial Suboptimal Path Discovery — High-Level Abstract ViewThe initial greedy phase of the $WA^$ algorithm ($w=1.5$). Due to the high weight, the search aggressively pursues a suboptimal path to a critical node (Node X). This phase highlights the propagation of an inflated $g$-cost down the search tree, ultimately stalling the descendants in the Open List before the true path is discovered.*קטע קודgraph TD
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
1B. No-Reopen Policy Execution — The Cost TrapExecution pipeline under the strict allow_reopen = False policy. Because Node X is locked in the Closed List, its descendants remain starved of priority. The router diverges to explore massive, irrelevant branches of the state space, resulting in severe resource waste (expanding 58,579 nodes) before finally defaulting back to the inflated descendants to reach the target.קטע קודgraph TD
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
1C. With-Reopen Policy Execution — Path Correction & BypassEnd-to-end flow under the allow_reopen = True policy. The router actively evaluates if newly discovered paths offer a lower $g$-cost to closed nodes. Upon discovering the optimal path to Node X, the algorithm extracts it from the Closed List, aggressively updates the $g$-cost of its children, and reprioritizes them, bypassing the wasteful branches entirely (reducing expansions to 52,063).קטע קודgraph TD
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