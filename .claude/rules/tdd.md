# TDD rules (always apply)

- No production code without a failing test that requires it. Order: test (red)
  → code (green) → refactor.
- A test must fail for the right reason before the code is written. A syntax or
  import error in the test doesn't count as red.
- Never weaken, skip (`skip`, `xfail`) or delete a test, or change its
  assertions, to make it pass. If a test seems wrong, stop and ask the tech lead.
- Test behaviour through public interfaces (HTTP responses via the Django test
  client, model methods), not private helpers.
- Use factory_boy factories for test data. Tests don't depend on each other or
  on test order.
- External services (OpenAI) are always mocked. Tests run offline.
- A ticket is not done until `uv run pytest` passes in full, not only the new tests.
