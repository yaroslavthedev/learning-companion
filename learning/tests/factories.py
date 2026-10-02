import factory

from accounts.tests.factories import UserFactory


class GoalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "learning.Goal"

    owner = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Goal {n}")
    description = ""


class LearningSessionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "learning.LearningSession"

    goal = factory.SubFactory(GoalFactory)
    duration_minutes = 30
    notes = ""


class ResourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "learning.Resource"

    goal = factory.SubFactory(GoalFactory)
    title = factory.Sequence(lambda n: f"Resource {n}")
    url = factory.Sequence(lambda n: f"https://example.com/{n}")
    kind = "article"
