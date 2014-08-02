import logging

from reviewboard.extensions.base import Extension
from reviewboard.extensions.hooks import SignalHook
from reviewboard.reviews.signals import review_request_published
from reviewboard.changedescs.models import ChangeDescription
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
        '''
        Handle signal; post to bugzilla for any new bug dependencies
        '''
        if not review_request:
            return

        bugs = review_request.get_bug_list()
        if not bugs:
            return

        tracker_url = review_request.repository.bug_tracker
        if not tracker_url:
            return

        config = self.settings
        setting_names = ['site_url', 'username', 'password']
        for name in setting_names:
            if config.get(name):
                continue
            this = self.__class__.__name__
            logging.error("{0}: missing config setting '{0}'".format(this, name))
            return

        changes = review_request.changedescs
        try:
            latest_change = changes.filter(public=True).latest()
        except ChangeDescription.DoesNotExist:
            latest_change = None

        # this is the initial publication of the review_request
        if not latest_change:
            self._post_bugs(review_request, bugs)
            return

        fields = latest_change.fields_changed
        bug_changes = fields.get('bugs_closed', None)
        if not bug_changes:
            return

        added = bug_changes.get('added', None)
        added = [bug for sublist in added for bug in sublist]
        if added:
            self._post_bugs(review_request, added)


    def _post_bugs(self, review_request, bugs):
        key = 'rboard_bugzilla_posted_bugs'
        url = review_request.get_absolute_url()

        posted_bugs = review_request.extra_data.get(key)
        posted_bugs = posted_bugs.split(',') if posted_bugs else []

        for bug in bugs:
            if bug in posted_bugs:
                continue

            try:
                self._post_bug(url, bug)
            except Exception as error:
                msg = "{0}: Failed posting bug {1} for review {2}: {3}"
                this = self.__class__.__name__
                logging.error(msg.format(this, bug, review_request.id, error))
                continue

            posted_bugs.append(bug)

        review_request.extra_data[key] = ",".join([bug for bug in posted_bugs])
        review_request.save()


    def _post_bug(self, url, bug):
        settings = self.settings
        base_url = settings.get('site_url')
        username = settings.get('username')
        password = settings.get('password')

        message = MESSAGE.format(url)

        bz_api = bugzilla.Bugzilla(base_url, username, password)
        bz_bug = bz_api.bug(bug)

        bz_bug.add_comment(message)
        bz_bug.update()
