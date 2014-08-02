from django.forms.fields import CharField
from djblets.extensions.forms import SettingsForm


class BugzillaSiteForm(SettingsForm):
    site_url = CharField(help_text="URL of the bugzilla site")
    username = CharField(help_text="Username used to post links")
    password = CharField(help_text="Password used to post links")
