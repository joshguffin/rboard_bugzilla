from reviewboard.extensions.base import Extension
from reviewboard.extensions.hooks import SignalHook
from reviewboard.reviews.signals import review_request_published


class BugzillaExtension(Extension):
    metadata = {
        'Name': 'Bugzilla Integrator',
        'Summary': 'posts to bz whenever the bz field changes',
    }

    def initialize(self):
        SignalHook(self, review_request_published, self.on_published)

    def on_published(self, review_request=None, **kwargs):
        pass
