from __future__ import print_function

import json

from launchpadlib.launchpad import Launchpad
import yaml

from launchpad_report.checks import Checks
from launchpad_report.render import CSVRenderer
from launchpad_report.render import HTMLRenderer
from launchpad_report.render import JSONRenderer
from launchpad_report.utils import all_bug_statuses
from launchpad_report.utils import get_name
from launchpad_report.utils import is_series
from launchpad_report.utils import open_bug_statuses
from launchpad_report.utils import open_bug_statuses_for_HCF
from launchpad_report.utils import printn
from launchpad_report.utils import short_status
from launchpad_report.utils import untriaged_bug_statuses


class ConfigError(Exception):
    pass


class Report(object):
    def __init__(self, config_filename):
        with open(config_filename, "r") as f:
            self.config = yaml.load(f.read())

        self.teams = self.config['teams']
        self.trunc = self.config['trunc_report']

        cache_dir = self.config['cache_dir']

        if self.config['use_auth']:
            lp = Launchpad.login_with(
                'lp-report-bot', 'production',
                cache_dir, version='devel'
            )
        else:
            lp = Launchpad.login_anonymously(
                'lp-report-bot', 'production', version='devel'
            )
        #import pdb; pdb.set_trace()
        self.projects = [lp.projects[prj] for prj in self.config['project']]

        # for backward compatibility
        #self.project = lp.projects[self.config['project'][0]]

        self.blueprint_series = {}

    def render2html(self, filename, template_filename):
        HTMLRenderer(filename, template_filename).render(self.data)

    def render2csv(self, filename):
        CSVRenderer(filename).render(self.data)

    def render2json(self, filename):
        JSONRenderer(filename).render(self.data)

    def load(self, filename):
        jsonfile = open(filename)
        self.data = json.load(jsonfile)

    def iter_series(self, project):
        print("Collecting series data for %s:" % project)
        self.bps_series = {}
        milestones_series = {}
        for series in project.series:
            printn(" %s" % get_name(series))
            # Blueprints
            #for (counter, bp) in enumerate(series.all_specifications):
                #self.bps_series[get_name(bp)] = get_name(series)
            # Milestones
            for milestone in series.all_milestones:
                milestones_series[get_name(milestone)] = get_name(series)
        printn(" none")
        # Search for blueprints without series
        #for (counter, bp) in enumerate(self.project.all_specifications):
            #self.bps_series.setdefault(get_name(bp), None)
        print()
        return {
            'milestones': milestones_series,
        }

    def bp_report(self, all=False):
        report = []
        if all:
            blueprints = self.project.all_specifications
        else:
            blueprints = self.project.valid_specifications
        printn("Processing blueprints (%d):" % len(blueprints))
        for (counter, bp) in enumerate(blueprints, 1):
            if counter > self.trunc and self.trunc > 0:
                break
            if counter % 200 == 10:
                print()
            if counter % 10 == 0:
                printn("%4d" % counter)
            assignee = 'unassigned'
            assignee_name = 'unassigned'
            try:
                assignee = get_name(bp.assignee)
                assignee_name = bp.assignee.display_name
            except Exception:
                pass
            if bp.milestone:
                milestone = get_name(bp.milestone)
            else:
                milestone = 'None'
            team = 'unknown'
            for t in self.teams.keys():
                if assignee in self.teams[t]:
                    team = t
            triage = self.checks.run(bp, self.bps_series[get_name(bp)])
            report.append({
                'type': 'bp',
                'link': bp.web_link.encode('utf-8'),
                'id': bp.web_link[
                    bp.web_link.rfind('/') + 1:
                ].encode('utf-8'),
                'title': bp.title.encode('utf-8'),
                'milestone': milestone,
                'series': self.bps_series[get_name(bp)],
                'status': bp.implementation_status,
                'short_status': short_status(bp),
                'priority': bp.priority,
                'team': team.encode('utf-8'),
                'assignee': assignee.encode('utf-8'),
                'name': assignee_name.encode('utf-8'),
                'triage': ', '.join(triage).encode('utf-8')
            })
        print()
        return report

    def bug_report(self, project, all=False):
        report = []
        if all:
            bugs_list = [project.searchTasks(status=all_bug_statuses)]
        else:
            print("Using hardcoded 5.1 & 5.0.2 milestones...")
            milestone51 = project.getMilestone(name="5.1")    # 5.1
            milestone502 = project.getMilestone(name="5.0.2") # 5.0.2
            if self.config.get('hcf'):
                raise # It should not go here
                bugs51 = project.searchTasks(status=(
                    open_bug_statuses_for_HCF), milestone=milestone51,
                    importance=["Critical", "High"],
                    # We would ideally filter our system-tests tag,
                    # however I saw bugs which were just found during
                    # sytem-tests run which are being real bugs in Fuel
                    tags=["-docs", "-devops", "-fuel-devops", "-experimental"],
                    tags_combinator="All")
                bugs502 = project.searchTasks(status=(
                    open_bug_statuses_for_HCF), milestone=milestone502,
                    importance=["Critical", "High"],
                    tags=["-docs", "-devops", "-fuel-devops", "-experimental"],
                    tags_combinator="All")
            else:
                bugs51 = project.searchTasks(milestone=milestone51, status=all_bug_statuses)
                bugs502 = project.searchTasks(milestone=milestone502, status=all_bug_statuses)
                bugs_list = [bugs51, bugs502]

        for bugs in bugs_list:
            for (counter, bug) in enumerate(bugs, 1):
                if counter > self.trunc and self.trunc > 0:
                    break
                if counter % 200 == 10:
                    print()
                if counter % 10 == 0:
                    printn("%4d" % counter)

                created_by = 'unassigned'
                created_by_name = 'unassigned'
                try:
                    created_by = get_name(bug.owner)
                    # We want to exclude all from QA & 
                    #   fuel-devops & docs for HCF calcs
                    #if self.config.get('excludes') and assignee in self.config['excludes']:
                        #continue
                    created_by_name = bug.owner.display_name
                except Exception:
                    pass
                if bug.milestone:
                    milestone = get_name(bug.milestone)
                else:
                    milestone = 'None'
                team = 'unknown'
                self.bug_issues.setdefault(bug.bug.web_link, [])
                for t in self.teams.keys():
                    if created_by in self.teams[t]:
                        team = t
                title = bug.bug.title
                triage = []
                for task in bug.bug.bug_tasks:
                    series = task.target
                    if is_series(series):
                        series = get_name(series)
                        if task.target.project != project:
                            continue
                    else:
                        series = None
                        if task.target != project:
                            continue
                    triage += self.checks.run(task, series)
                report.append({
                    'type': 'bug',
                    'link': bug.web_link.encode('utf-8'),
                    'id': bug.web_link[
                        bug.web_link.rfind('/') + 1:
                    ].encode('utf-8'),
                    'title': title.encode('utf-8'),
                    'milestone': milestone,
                    'status': bug.status,
                    'short_status': short_status(bug),
                    'priority': bug.importance,
                    'team': team.encode('utf-8'),
                    'assignee': created_by.encode('utf-8'),
                    'name': created_by_name.encode('utf-8'),
                    'triage': ', '.join(triage).encode('utf-8'),
                })
        print()
        return report

    def generate(self, all=False):
        self.data = {'rows': []}
        self.bug_issues = {}
        self.data['config'] = self.config
        for project in self.projects:
            self.checks = Checks(self.iter_series(project))
            #self.data['rows'] += self.bp_report(all=all)
            self.data['rows'] += self.bug_report(project, all=all)
