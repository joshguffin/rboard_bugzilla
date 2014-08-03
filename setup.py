from reviewboard.extensions.packaging import setup

GITHUB_URL = 'https://github.com/joshguffin/rboard_bugzilla'
VERSION = "0.1"
PACKAGE = 'rboard_bugzilla'
EXTENSION = '{0} = {0}.extension:BugzillaExtension'.format(PACKAGE),

setup(
    name=PACKAGE,
    version=VERSION,
    description='Post to BZs',
    url=GITHUB_URL,
    author='Josh Guffin',
    author_email='josh.guffin@gmail.com',
    packages=[PACKAGE],
    install_requires=['bugzillatools>=0.4', 'ReviewBoard>=2.0.3'],
    entry_points={'reviewboard.extensions': [EXTENSION]}
)
