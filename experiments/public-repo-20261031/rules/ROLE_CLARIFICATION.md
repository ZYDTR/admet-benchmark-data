# Analysis-role subagent authorization

The retrieval, publication and training-execution roles do not receive permission for new training, HPO, external labels, official uploads, service operations or agent/thread/CLI-model delegation. The user explicitly authorizes the independent analysis Chat Pro to use its own subagents for read-only research and cross-checks; this is an analysis-role exception, not permission to train, access servers, score new data, publish or delegate execution. Retrieval/publication still remain single leaf executors.

The gateway alone operates the designated analysis chat. The retrieval/publication executor does not send messages to Chat.
