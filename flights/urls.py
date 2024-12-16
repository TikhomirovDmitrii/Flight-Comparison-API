from django.urls import path
from . import views


urlpatterns = [
    path('parse/', views.parse_files, name='parse_files'),
    path('flights/', views.get_filtered_flights, name='get_filtered_flights'),
    path('flights/cheapest/', views.get_cheapest_flights, name='get_cheapest_flights'),
    path('flights/expensive/', views.get_expensive_flights, name='get_expensive_flights'),
    path('flights/fastest/', views.get_fastest_flights, name='get_fastest_flights'),
    path('flights/longest/', views.get_longest_flights, name='get_longest_flights'),
    path('flights/compare/', views.compare_flights_view, name='compare_flights_view'),
]