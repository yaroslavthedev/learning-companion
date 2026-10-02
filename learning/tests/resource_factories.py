import factory

from learning.tests.factories import GoalFactory


class ResourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "learning.Resource"

    goal = factory.SubFactory(GoalFactory)
    title = factory.Sequence(lambda n: f"Resource {n}")
    url = factory.Sequence(lambda n: f"https://example.com/{n}")
    kind = "article"
