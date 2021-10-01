# tutorial-python-locust

[![build workflow](https://github.com/Xray-App/tutorial-python-locust/actions/workflows/python-app.yml/badge.svg)](https://github.com/Xray-App/tutorial-python-locust/actions/workflows/python-app.yml)
[![license](https://img.shields.io/badge/License-BSD%203--Clause-green.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Gitter chat](https://badges.gitter.im/gitterHQ/gitter.png)](https://gitter.im/Xray-App/community)

## Overview

Code that supports the tutorial [Performance and load testing with Locust](https://docs.getxray.app/display/XRAYCLOUD/Performance+and+load+testing+with+Locust) showcasing the integration between [Xray Test Management](https://www.getxray.app/) on Jira and Locust, using a custom report.

## Prerequisites

In order to run this tutorial, you need to have Python and Locust (and Docker if you want to integrate with Graphana and Graphite).

## Running

Tests can be run using the command `locust`.

```bash
locust -f LocustScript.py --headless -u 50 -r 1 -t 1m --csv=example
```

## Submitting results to Jira

Results can be submitted to Jira so that they can be shared with the team and their impacts be easily analysed.
This can be achieved using [Xray Test Management](https://www.getxray.app/) as shown in further detail in this [tutorial](https://docs.getxray.app/display/XRAYCLOUD/Performance+and+load+testing+with+Locust).

## Contact

Any questions related with this code, please raise issues in this GitHub project. Feel free to contribute and submit PR's.
For Xray specific questions, please contact [Xray's support team](https://jira.getxray.app/servicedesk/customer/portal/2).

## LICENSE

[BSD 3-Clause](LICENSE)
