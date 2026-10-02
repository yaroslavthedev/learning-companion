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
