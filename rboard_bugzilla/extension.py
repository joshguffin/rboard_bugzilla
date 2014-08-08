import logging

from django.contrib.sites.models import Site
from reviewboard.extensions.base import Extension
from reviewboard.extensions.hooks import SignalHook
from reviewboard.reviews.signals import review_request_published
from reviewboard.changedescs.models import ChangeDescription
from bzlib import bugzilla


MESSAGE = "A code review associated to this bug has been created at {0}"


def _extension_applies(review_request):
    if not review_request:
        return False

    if not review_request.repository:
        return False

    tracker_url = review_request.repository.bug_tracker
    return tracker_url


def _get_added_bug_list(review_request):
    '''
    Recover bug numbers that have been added during this publication
    '''
    changes = review_request.changedescs
    try:
        latest_change = changes.filter(public=True).latest()
    except ChangeDescription.DoesNotExist:
        # this is the initial publication of the review_request
        return review_request.get_bug_list()

    fields = latest_change.fields_changed
    bug_changes = fields.get('bugs_closed', None)
    if not bug_changes:
        return []

    added = bug_changes.get('added', None)
    return [bug for sublist in added for bug in sublist]


def _construct_full_url(review_request):
    '''
    Obtain the domain and method from the current site and append the request url
    '''
    current_site = Site.objects.get_current()
    siteconfig = current_site.config.get()
    domain_method = siteconfig.get("site_domain_method")
    review_url = review_request.get_absolute_url()

    return "{0}://{1}{2}".format(domain_method, current_site.domain, review_url)


class BugzillaExtension(Extension):

    is_configurable = True

    metadata = {
        'Name': 'Bugzilla Integrator',
        'Summary': 'posts to bz whenever the bz field changes',
    }


    def initialize(self):
        '''
        Register to be notified when a review request is published
        '''
        SignalHook(self, review_request_published, self.on_published)


    def on_published(self, review_request=None, **kwargs):
        '''
        Handle signal; post to bugzilla for any new bug dependencies
        '''
        if not _extension_applies(review_request):
            return

        bugs = _get_added_bug_list(review_request)
        if bugs:
            self._post_bugs(review_request, bugs)


    def _post_bugs(self, review_request, bugs):
        '''
        Post updates to bugs that we haven't already posted to
        '''
        key = 'rboard_bugzilla_posted_bugs'
        url = _construct_full_url(review_request)

        posted_bugs = review_request.extra_data.get(key)
        posted_bugs = posted_bugs.split(',') if posted_bugs else []

        for bug in bugs:
            if bug in posted_bugs:
                continue

            try:
                self._post_bug_to_bugzilla(url, bug)
            except Exception as error:
                # unfortunately bugzillatools sometimes raises raw Exceptions
                msg = "{0}: Failed posting bug {1} for review {2}: {3}"
                this = self.__class__.__name__
                logging.error(msg.format(this, bug, review_request.id, error))
                continue

            posted_bugs.append(bug)

        review_request.extra_data[key] = ",".join(posted_bugs)
        review_request.save()


    def _post_bug_to_bugzilla(self, review_url, bug):
        '''
        Post data to bugzilla
        '''
        settings = self.settings
        base_url = settings.get('site_url')
        username = settings.get('username')
        password = settings.get('password')

        bz_api = bugzilla.Bugzilla(base_url, username, password)
        bz_bug = bz_api.bug(bug)

        bz_bug.add_comment(MESSAGE.format(review_url))
        bz_bug.update()
