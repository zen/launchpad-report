from __future__ import print_fuction

import argparse
from launchpadlib.launchpad import Launchpad
import yaml


def bulk():
    bulkfile = open('bulk.yaml')
    tasks = yaml.load(bulkfile)
    lp = Launchpad.login_with('lp-report-bot', 'production', version='devel')
    for prj_name in tasks.keys():
        prj = lp.projects[prj_name]
        prj_tasks = tasks[prj_name]
        for bp_name in prj_tasks['bp'].keys():
            bp = prj.getSpecification(name=bp_name)
            bp_tasks = prj_tasks['bp'][bp_name]
            if 'series' in bp_tasks:
                bp.proposeGoal(goal=prj.getSeries(name=bp_tasks['series']))
            if 'milestone' in bp_tasks:
                if bp_tasks['milestone'] != 'None':
                    bp.milestone = prj.getMilestone(name=bp_tasks['milestone'])
                    bp.lp_save()
                    bp.proposeGoal(goal=bp.milestone.series_target)
                else:
                    bp.milestone = None
                    bp.lp_save()
            if 'approve' in bp_tasks:
                pass

lp = None
prj = None


def update_bp(item_id, params):
    bp = prj.getSpecification(name=item_id)
    if params.milestone:
        print("Updating (%s) milestone to (%s)" % (
            item_id, params.milestone
        ))
        if params.milestone != 'None':
            bp.milestone = prj.getMilestone(name=params.milestone)
            bp.lp_save()
            bp.proposeGoal(goal=bp.milestone.series_target)
        else:
            bp.milestone = None
            bp.lp_save()
    if params.series:
        print("Updating (%s) series to (%s)" % (
            item_id, params.series
        ))
        if params.series != 'None':
            bp.proposeGoal(goal=prj.getSeries(name=params.series))
        else:
            bp.proposeGoal(goal=None)
    if params.approved:
        print("Approving (%s)" % item_id)
        bp.direction_approved = True
        bp.definition_status = 'Approved'
        bp.lp_save()
    if params.create:
        print("Creation of blueprints is not implemented")
    if params.delete:
        print("Removal of blueprints is not available")
    if params.priority:
        print("TODO")
    if params.status:
        print("Setting implementation status of (%s) to (%s)" % (
            item_id, params.status
        ))
        bp.implementation_status = params.status
        bp.lp_save()


def update_bug(item_id, params):
    try:
        (bug_id, series_name) = item_id.split(":")
    except ValueError:
        (bug_id, series_name) = (item_id, None)
    bug = lp.bugs[bug_id]
    if series_name is None:
        series = prj
    else:
        series = prj.getSeries(name=series_name)
    bug_task = filter(lambda x: x.target == series, bug.bug_tasks)[0]
    if params.milestone:
        print("Updating (%s) milestone to (%s)" % (
            item_id, params.milestone
        ))
        if params.milestone != 'None':
            bug_task.milestone = prj.getMilestone(name=params.milestone)
            bug_task.lp_save()
        else:
            bug.milestone = None
            bug.lp_save()
    if params.series:
        print("Not suitable for bugs")
    if params.approved:
        print("Not suitable for bugs")
    if params.create:
        bug.addTask(target=series)
    if params.delete:
        bug_task.delete()
    if params.priority:
        print("TODO")
    if params.status:
        print("Setting status of (%s) to (%s)" % (
            item_id, params.status
        ))
        bug.status = params.status
        bug.lp_save()


def main():
    description = """
    Command line tool to operate with bugs and blueprints
    """
    parser = argparse.ArgumentParser(epilog=description)
    parser.add_argument('project', type=str)
    parser.add_argument('cmd', type=str, choices=['get', 'set'])
    parser.add_argument('item_type', type=str, choices=['bp', 'bug'])
    parser.add_argument('item_id', type=str, nargs='+')
    parser.add_argument('--milestone', type=str)
    parser.add_argument('--series', type=str)
    parser.add_argument('--approve', dest='approved', action='store_true')
    parser.add_argument('--create', action='store_true')
    parser.add_argument('--delete', action='store_true')
    parser.add_argument('--priority', type=str)
    parser.add_argument('--status', type=str)
    params, other_params = parser.parse_known_args()
    global lp
    global prj
    lp = Launchpad.login_with('lp-client', 'production', version='devel')
    prj = lp.projects[params.project]
    if params.cmd == 'set':
        for item_id in params.item_id:
            if params.item_type == 'bp':
                update_bp(item_id, params)
            if params.item_type == 'bug':
                update_bug(item_id, params)


if __name__ == "__main__":
    main()
