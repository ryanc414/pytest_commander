# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_build_tree 1'] = {
    'child_branches': {
        'path': {
            'child_branches': {
                'to': {
                    'child_branches': {
                        'test_a.py': {
                            'child_branches': {
                                'TestSuite': {
                                    'child_branches': {
                                    },
                                    'child_leaves': {
                                        'test_one': {
                                            'longrepr': None,
                                            'nodeid': 'path/to/test_a.py::TestSuite::test_one',
                                            'short_id': 'test_one',
                                            'status': 'init'
                                        },
                                        'test_two': {
                                            'longrepr': None,
                                            'nodeid': 'path/to/test_a.py::TestSuite::test_two',
                                            'short_id': 'test_two',
                                            'status': 'init'
                                        }
                                    },
                                    'environment_state': 'inactive',
                                    'nodeid': 'path/to/test_a.py::TestSuite',
                                    'short_id': 'TestSuite',
                                    'status': 'init'
                                },
                                'test_three': {
                                    'child_branches': {
                                    },
                                    'child_leaves': {
                                        '1': {
                                            'longrepr': None,
                                            'nodeid': 'path/to/test_a.py::test_three[1]',
                                            'short_id': '1',
                                            'status': 'init'
                                        },
                                        '2': {
                                            'longrepr': None,
                                            'nodeid': 'path/to/test_a.py::test_three[2]',
                                            'short_id': '2',
                                            'status': 'init'
                                        },
                                        '3': {
                                            'longrepr': None,
                                            'nodeid': 'path/to/test_a.py::test_three[3]',
                                            'short_id': '3',
                                            'status': 'init'
                                        }
                                    },
                                    'environment_state': 'inactive',
                                    'nodeid': 'path/to/test_a.py::test_three',
                                    'short_id': 'test_three',
                                    'status': 'init'
                                }
                            },
                            'child_leaves': {
                                'test_one': {
                                    'longrepr': None,
                                    'nodeid': 'path/to/test_a.py::test_one',
                                    'short_id': 'test_one',
                                    'status': 'init'
                                },
                                'test_two': {
                                    'longrepr': None,
                                    'nodeid': 'path/to/test_a.py::test_two',
                                    'short_id': 'test_two',
                                    'status': 'init'
                                }
                            },
                            'environment_state': 'inactive',
                            'nodeid': 'path/to/test_a.py',
                            'short_id': 'test_a.py',
                            'status': 'init'
                        }
                    },
                    'child_leaves': {
                    },
                    'environment_state': 'inactive',
                    'nodeid': 'path/to',
                    'short_id': 'to',
                    'status': 'init'
                }
            },
            'child_leaves': {
            },
            'environment_state': 'inactive',
            'nodeid': 'path',
            'short_id': 'path',
            'status': 'init'
        }
    },
    'child_leaves': {
    },
    'environment_state': 'inactive',
    'nodeid': '',
    'short_id': 'root',
    'status': 'init'
}
