import logging
import sys

logger = logging.getLogger(__name__)

cached_names = {
}


def is_bug(obj):
    return (
        obj.resource_type_link == u'https://api.launchpad.net/devel/#bug_task'
    )


def is_bp(obj):
    return (
        obj.resource_type_link ==
        u'https://api.launchpad.net/devel/#specification'
    )


def is_project(obj):
    return (
        obj.resource_type_link ==
        u'https://api.launchpad.net/devel/#project'
    )


def is_series(obj):
    return (
        obj.resource_type_link ==
        u'https://api.launchpad.net/devel/#project_series'
    )


def get_name(obj):
    key = obj._wadl_resource._url
    if key not in cached_names:
        logger.debug("Miss name: " + key)
        cached_names[key] = obj.name
    else:
        logger.debug("Hit name: " + key)
    return cached_names[key]


def printn(text):
    sys.stdout.write(text)
    sys.stdout.flush()
