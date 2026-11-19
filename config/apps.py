from django.contrib.staticfiles.apps import StaticFilesConfig


class FriStaticFilesConfig(StaticFilesConfig):
    # site/ also holds the historical static reference and unused drafts.
    # They stay in the repository but are not copied to STATIC_ROOT by collectstatic.
    ignore_patterns = [
        *StaticFilesConfig.ignore_patterns,
        'screenshots',
        'index.html',
        'design-log.md',
        'content.js',
        'sponsor-orbit.js',
        'home-sidebar.css',
        'home-sidebar.js',
        'zxc.css',
        'zxc-ink.css',
        'zxc-poster.css',
        'zxc-wired.css',
        'assets/travis-scott-dumbo.mp3',
        'assets/sponsor-apple.png',
        'assets/zxc-eye-tile.svg',
        'assets/zxc-ink.webp',
        'assets/zxc-wired-figure.png',
        'assets/zxc-shadow-fiend-forward.webm',
        'assets/zxc-shadow-fiend-loop.webm',
        'assets/zxc-shadow-fiend-slow.webm',
    ]
