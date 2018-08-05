from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.pasur, name='index'),
    url(r'pasur/$', views.pasur, name='new_pasur_match'),
    url(r'pasur/(?P<match_id>[^/]+)/$', views.pasur, name='pasur_match'),
    url(r'create_user/$', views.CreateUserView.as_view(), name='create_user_new_match'),
    url(r'create_user/(?P<match_id>[^/]+)/$', views.CreateUserView.as_view(), name='create_user'),
]
