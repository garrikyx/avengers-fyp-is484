# Issue tracker: Jira

Issues and specs for this repo live in Jira project **UBS** ("Avengers") at
https://avengersfyp.atlassian.net (cloudId `ec268efd-e5c8-4393-9ca3-fbdd9fc3721d`). Use the
Atlassian Rovo MCP tools for all operations; there is no CLI. GitHub Issues are not used.

## Conventions

- **Issue types**: Epic (groups related work), Story (user-facing feature; the default), Task, Bug, Subtask.
- **Statuses**: To Do → In Progress → In Review → Done.
- **Keys**: refer to issues as `UBS-<n>`. Branches are named `UBS-<n>-Short-Title`; commit subjects start with `UBS-<n>`.
- **Create an issue**: `createJiraIssue` with projectKey `UBS`, `issueTypeName`, `summary` and a markdown `description`. Put it under an epic via `parent`.
- **Read an issue**: `getJiraIssue` with the `UBS-<n>` key, including comments.
- **List / search issues**: `searchJiraIssuesUsingJql`, e.g. `project = UBS AND labels = needs-triage AND statusCategory != Done`.
- **Comment on an issue**: `addCommentToJiraIssue`.
- **Apply / remove labels**: `editJiraIssue` on the `labels` field. Jira creates a label on first use.
- **Change status / close**: `getTransitionsForJiraIssue`, then `transitionJiraIssue` (to Done, with a comment when closing as wontfix).

## Pull requests as a triage surface

**PRs as a request surface: no.** _(Set to `yes` if this repo treats external PRs as feature requests; `/triage` reads this flag.)_

## When a skill says "publish to the issue tracker"

Create a UBS Story (or a Bug for defects) with the Rovo tools.

## When a skill says "fetch the relevant ticket"

Read it as in **Read an issue** above.

## Wayfinding operations

Used by `/wayfinder`. The **map** is an Epic, and its **child** issues are the tickets.

- **Map**: an Epic labelled `wayfinder:map`, whose description holds the Notes / Decisions-so-far / Fog body.
- **Child ticket**: a Story or Task whose `parent` is the map epic, labelled `wayfinder:<type>` (`research`/`prototype`/`grilling`/`task`). Once claimed, it is assigned to the driving dev.
- **Blocking**: a Jira "Blocks" issue link (`createIssueLink`). A ticket is unblocked when every blocker is Done.
- **Frontier query**: `parent = <map> AND statusCategory != Done AND assignee is EMPTY`, minus any ticket with an open blocker; first in rank order wins.
- **Claim**: assign the ticket to yourself (`editJiraIssue` assignee, account id via `lookupJiraAccountId`), as the session's first write.
- **Resolve**: comment the answer, transition to Done, then append a context pointer (gist + link) to the map epic's Decisions-so-far.
