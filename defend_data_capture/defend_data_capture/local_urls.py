import debug_toolbar
from defend_data_capture.urls import *

urlpatterns += [
    path('__debug__/', include(debug_toolbar.urls)),
]