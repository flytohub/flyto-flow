# CE Providers

Flyto2 Cloud CE assembles only local providers:

- Offline JWT authentication.
- Simple local access control.
- No-op external audit sink with local audit-chain services.
- SQLite workflow, template, notification, and execution storage.

Hosted and enterprise provider implementations are intentionally absent from
the generated repository. Shared APIs must use provider interfaces so private
editions can supply their implementations outside the CE tree.
