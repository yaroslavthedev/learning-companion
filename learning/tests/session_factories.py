import factory

from learning.tests.factories import GoalFactory


class LearningSessionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "learning.LearningSession"

    goal = factory.SubFactory(GoalFactory)
    duration_minutes = 30
    notes = ""
