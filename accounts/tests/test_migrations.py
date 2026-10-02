import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

BEFORE = [("accounts", "0002_profile")]
AFTER = [("accounts", "0003_create_missing_profiles")]


def migrate(targets):
    executor = MigrationExecutor(connection)
    executor.migrate(targets)
    return executor.loader.project_state(targets).apps


@pytest.fixture
def old_apps():
    """Schema as it was before 0003, restored to the latest state afterwards."""
    apps = migrate(BEFORE)
    yield apps
    executor = MigrationExecutor(connection)
    executor.migrate(executor.loader.graph.leaf_nodes())


@pytest.mark.django_db(transaction=True)
def test_migration_creates_profile_for_existing_user_without_one(old_apps):
    # Historical models: the post_save signal doesn't fire, like for users
    # created before Profile existed.
    user_model = old_apps.get_model("accounts", "User")
    user_model.objects.create(username="old-superuser")

    new_apps = migrate(AFTER)

    profile_model = new_apps.get_model("accounts", "Profile")
    assert profile_model.objects.filter(user__username="old-superuser").count() == 1


@pytest.mark.django_db(transaction=True)
def test_migration_keeps_existing_profile_and_creates_no_duplicate(old_apps):
    user_model = old_apps.get_model("accounts", "User")
    profile_model = old_apps.get_model("accounts", "Profile")
    user = user_model.objects.create(username="alice")
    profile_model.objects.create(user=user, name="Alice Example")

    new_apps = migrate(AFTER)

    profiles = new_apps.get_model("accounts", "Profile").objects.filter(
        user__username="alice"
    )
    assert profiles.count() == 1
    assert profiles.get().name == "Alice Example"
