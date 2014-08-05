import inspect


def is_bug(obj):
    return (
        obj.resource_type_link == u'https://api.launchpad.net/devel/#bug_task'
    )


def is_bp(obj):
    return (
        obj.resource_type_link ==
        u'https://api.launchpad.net/devel/#specification'
    )


class Checks(object):
    def __init__(self, mapping):
        self.mapping = mapping

    def run(self, obj, series):
        tests = inspect.getmembers(
            Checks,
            lambda x: inspect.ismethod(x) and
            x.__name__.startswith('is_')
        )
        actions = []
        for test in tests:
            actions.append(getattr(Checks, test[0])(obj, series))
        return actions

    @staticmethod
    def is_series_defined(obj, series):
        if is_bp(obj) and series is None:
            return "No series"

    @staticmethod
    def is_milestone_in_series(obj, series):
        if obj.milestone is None:
            return "No milestone for series (%s)" % series
        if series is None:
            return  # There is another check for missed series
        if obj.milestone.name not in Checks.mapping['milestones'][series]:
            return ("Wrong milestone (%s) for series (%s)" % (
                obj.milestone.name, series))

    @staticmethod
    def is_milestone_active(obj, series):
        if not obj.milestone.is_active and not obj.is_complete:
            return (
                "Open and targeted to closed milestone (%s) on series (%s)" %
                (obj.milestone.name, series)
            )

    @staticmethod
    def is_bug_targeted_to_focus_series(obj, series):
        if is_bug(obj) and obj.target.development_focus.name == series:
            return (
                "Targeted to the current development focus (%s)" %
                series)

    @staticmethod
    def is_priority_set(obj, series):
        valid_bp_priorities = [
            'Essential', 'High', 'Medium', 'Low'
        ]
        valid_bug_priorities = [
            'Critical', 'High', 'Medium', 'Low', 'Wishlist'
        ]
        if is_bp(obj) and obj.priority not in valid_bp_priorities:
            return "Priority (%s) is not valid for series (%s)" % (
                obj.priority, series)
        if is_bug(obj) and obj.importance not in valid_bug_priorities:
            return "Priority (%s) is not valid for series (%s)" % (
                obj.importance, series)

    @staticmethod
    def is_assignee_set(obj, series):
        if not obj.assignee:
            return "No assignee for series (%s)" % series

    @staticmethod
    def is_bug_confirmed(obj, series):
        if is_bug(obj) and obj.status == 'New':
            return "Not confirmed for series (%s)" % series
