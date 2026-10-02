import factory

from accounts.tests.factories import UserFactory


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "tags.Tag"

    owner = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"tag{n}")
