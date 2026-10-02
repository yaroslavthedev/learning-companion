def test_ci_demo_fails_on_purpose():
    # Temporary (#20): proves the CI pytest step goes red. Reverted next commit.
    assert 1 + 1 == 3
