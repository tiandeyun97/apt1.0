from django.urls import path
from . import views

app_name = 'data_analysis'
 
urlpatterns = [
    path('', views.index, name='index'),
    path('consumption-trend/', views.consumption_trend, name='consumption_trend'),
    path('optimizer-ranking/', views.optimizer_ranking, name='optimizer_ranking'),
] 