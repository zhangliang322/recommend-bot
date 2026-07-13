# Architecture

```text
CSV / external collectors
  -> normalized ProductCandidate
  -> scoring service
  -> recommendation service
  -> card render service
  -> push adapter
```

The WeChat/AstrBot layer should only handle messages, commands, permissions, and sending. Ranking, copy, safety, and image generation stay framework-independent.

