# NUB — Hard-Disk Version Control

No internet. No GitHub. No server required.

## Vocabulary
- **start** (init)
- **snap** (commit)
- **past** (log)
- **now** (status)
- **flow** (branch)
- **back** (rollback)

## Commands
    nub start                                 # start new repo
    nub config --name "Name" --email e@x.com  # set identity
    nub snap -m "message"                     # take a snapshot
    nub past                                  # look at project history
    nub now                                   # current flow and status
    nub show [hash]                           # inspect a snapshot
    nub flow list                             # list all flows
    nub flow create <name>                    # start a new flow
    nub flow switch <name>                    # switch flows
    nub flow delete <name>                    # delete a flow
    nub back --steps N                        # go back N snaps
    nub back --hash HASH                      # jump to any snap

## Multi-user rules
1. Each person runs `nub config` once on first use.
2. Coordinate before snapping to the same flow.
3. Use flows — keep main clean.
4. .vcs/objects is append-only. History is never deleted.
