from django.urls import path
from .views import CurrentUserView

current_user_view = CurrentUserView.as_view({'get': 'me', 'patch': 'update_me'})

urlpatterns = [
    path('me/', current_user_view, name='current-user'),
]
