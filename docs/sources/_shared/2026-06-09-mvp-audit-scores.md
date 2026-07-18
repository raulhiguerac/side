---
title: MVP readiness audit — real code scores per service (2026-06-09)
captured-from: conversation
captured-on: 2026-06-09
participants: [raul, claude]
---

## Context
Full audit of all 4 microservices and frontend based on actual code reading (not docs/memory). Scored 1-10 for MVP readiness.

## Key conclusions

| Service | Score | Status |
|---|---|---|
| catalog-service | 8/10 | MVP-ready. 2 Alembic migrations, all 3 domains wired. Gap: no integration tests. |
| users-service | 8/10 | 4 domains, 6 Alembic migrations, all routers mounted. Gap: swallowed errors in cache/logout paths (intentional). |
| properties-service | 6/10 | Core complete. ads injection implemented — `pass` blocks are silent cache fail handlers, not empty logic (correct pattern: cache as optimization not blocker). Gap: promotions domain has no effective cache invalidation. |
| analytics-service | 7/10 | Online predict endpoint wired and functional. Gap: batch UC has no HTTP endpoint; Kafka worker (`runner.py`) not started in `main.py` startup. |
| frontend | 6/10 | FeedView, MapView, AvmView, auth views all connected to real APIs. Gap: no error/loading states, no property detail view. |

- **ads.py `except Exception: pass` pattern is correct** — cache is an optimization layer; if Redis is down the service degrades to direct DB reads without blocking. Same pattern used across all services.
- To reach 8/10 on both backend and frontend: add error states to main views + wire Kafka worker to analytics startup.

## Next steps
- Wire Kafka worker in analytics-service `main.py` startup.
- Add error/loading states to FeedView and MapView.
- Property detail view.
- Seed Bogotá properties data.
