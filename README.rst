launchpad-report
================

Gather csv statistics for launchpad project, aggregate teams info, list triage
actions.

Report example:

   ,Link,Title,Status,Priority,Team,Nick,Name,Triage actions
   bp,https://blueprints.launchpad.net/fuel/+spec/horizon-basic-auth-by-default,Please add basic auth to horizon UI,Unknown,Low,unknown,unassigned,unassigned,No assignee
   bp,https://blueprints.launchpad.net/fuel/+spec/external-mongodb-support,Implement possibility to set external MongoDB connection,Needs Code Review,Undefined,mos,iberezovskiy,Ivan Berezovskiy,"No priority, No series"
   bug,https://bugs.launchpad.net/fuel/+bug/1332097,Error during the deployment,Confirmed,Critical,library,fuel-library,Fuel Library Team,Related to non-current milestone (4.1.2)
   bug,https://bugs.launchpad.net/fuel/+bug/1342617,Need to add possibility to build tarballs for patching only,New,High,python,ikalnitsky,Igor Kalnitsky,Not triaged


Installation
============
In virtual env, run pip install -r requirements.txt. Check Known Issues.

Known Issues
============

lazr.authentication (requirement for launchpadlib) is broken on pypi. You can install it manually from `launchpad <https://launchpad.net/lazr.authentication/+download>`_:

   pip install https://launchpad.net/lazr.authentication/trunk/0.1.2/+download/lazr.authentication-0.1.2.tar.gz


How to use
==========
In order to get list of bugs per particular team lead:
$ python cli.py -c launchpad_report/leads.yaml --template=launchpad_report/leads.html

In order to get list of bugs affecting HCF:
$ python cli.py -c launchpad_report/hcf.yaml --template=launchpad_report/hcf.html
