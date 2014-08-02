from django.conf.urls import patterns

from rboard_bugzilla.extension import BugzillaExtension
from rboard_bugzilla.forms import BugzillaSiteForm

urlpatterns = patterns('',
                       (r'^$', 'reviewboard.extensions.views.configure_extension',
                        {'ext_class': BugzillaExtension,
                         'form_class': BugzillaSiteForm,
                        }),
                      )
