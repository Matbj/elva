from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.PasurMenuView.as_view(), name='index'),
    url(r'pasur/(?P<match_id>[^/]+)/$', views.PasurGameView.as_view(), name='pasur_match'),
    url(r'pasur/$', views.NewPasurGameView.as_view(), name='new_pasur_match'),
    url(r'create_user/$', views.CreateUserView.as_view(), name='create_user_new_match'),
    url(r'create_user/(?P<match_id>[^/]+)/$', views.CreateUserView.as_view(), name='create_user'),
]
