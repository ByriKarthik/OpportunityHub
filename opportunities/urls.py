from django.urls import path

from .views import (
    health_check,
    home,
    opportunity_detail,
    opportunity_list,
    saved_opportunities,
    scrape_iit,
    toggle_bookmark,
)

app_name = 'opportunities'

urlpatterns = [
    path("home/", home, name="home"),
    path('health/', health_check, name='health-check'),
    path("scrape-iit/", scrape_iit, name="scrape-iit"),
    path("saved/", saved_opportunities, name="saved-opportunities"),
    path("<int:pk>/bookmark/", toggle_bookmark, name="toggle-bookmark"),
    path("", opportunity_list, name="opportunity-list"),
    path("<int:pk>/", opportunity_detail, name="opportunity-detail"),
]
