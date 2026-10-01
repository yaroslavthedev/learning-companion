from django.urls import reverse
from pytest_django.asserts import assertContains, assertTemplateUsed


def test_home_page_returns_200_with_app_name(client):
    response = client.get(reverse("home"))

    assertContains(response, "Learning Companion", status_code=200)


def test_home_page_extends_base_with_pico_css(client):
    response = client.get(reverse("home"))

    assertTemplateUsed(response, "base.html")
    assertContains(response, "pico")
