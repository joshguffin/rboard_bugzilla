from reviewboard.extensions.base import Extension
from reviewboard.extensions.hooks import SignalHook
from reviewboard.reviews.signals import review_request_published
from bzlib import bugzilla


MESSAGE = "A code review associated to this bug has been created at {0}"


class BugzillaExtension(Extension):

    is_configurable = True

    metadata = {
        'Name': 'Bugzilla Integrator',
        'Summary': 'posts to bz whenever the bz field changes',
    }

    def initialize(self):
        SignalHook(self, review_request_published, self.on_published)

    def on_published(self, review_request=None, **kwargs):
        pass


    def _post_bug(self, url, bug):
        settings = self.settings
        base_url = settings.site_url
        username = settings.username
        password = settings.password

        message = MESSAGE.format(url)
        bz_api = bugzilla.Bugzilla(base_url, username, password)
        bz_bug = bz_api.bug(bug)

        bz_bug.add_comment(message)
        bz_bug.update()
