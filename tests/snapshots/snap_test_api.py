# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_report_skeleton 1'] = {
    'child_branches': {
        'test_a.py': {
            'child_branches': {
                'TestSuite': {
                    'child_branches': {
                    },
                    'child_leaves': {
                        'test_alpha': {
                            'longrepr': None,
                            'nodeid': 'test_a.py::TestSuite::test_alpha',
                            'short_id': 'test_alpha',
                            'status': 'init'
                        },
                        'test_beta': {
                            'longrepr': None,
                            'nodeid': 'test_a.py::TestSuite::test_beta',
                            'short_id': 'test_beta',
                            'status': 'init'
                        }
                    },
                    'environment_state': 'inactive',
                    'nodeid': 'test_a.py::TestSuite',
                    'short_id': 'TestSuite',
                    'status': 'init'
                }
            },
            'child_leaves': {
                'test_one': {
                    'longrepr': None,
                    'nodeid': 'test_a.py::test_one',
                    'short_id': 'test_one',
                    'status': 'init'
                },
                'test_two': {
                    'longrepr': None,
                    'nodeid': 'test_a.py::test_two',
                    'short_id': 'test_two',
                    'status': 'init'
                }
            },
            'environment_state': 'inactive',
            'nodeid': 'test_a.py',
            'short_id': 'test_a.py',
            'status': 'init'
        },
        'test_b.py': {
            'child_branches': {
            },
            'child_leaves': {
                'test_http_service': {
                    'longrepr': None,
                    'nodeid': 'test_b.py::test_http_service',
                    'short_id': 'test_http_service',
                    'status': 'init'
                },
                'test_one': {
                    'longrepr': None,
                    'nodeid': 'test_b.py::test_one',
                    'short_id': 'test_one',
                    'status': 'init'
                },
                'test_two': {
                    'longrepr': None,
                    'nodeid': 'test_b.py::test_two',
                    'short_id': 'test_two',
                    'status': 'init'
                }
            },
            'environment_state': 'inactive',
            'nodeid': 'test_b.py',
            'short_id': 'test_b.py',
            'status': 'init'
        }
    },
    'child_leaves': {
    },
    'environment_state': 'stopped',
    'nodeid': '',
    'short_id': 'pytest_examples',
    'status': 'init'
}

snapshots['test_run_test 1'] = [
    {
        'args': [
            {
                'child_branches': {
                    'test_a.py': {
                        'child_branches': {
                            'TestSuite': {
                                'child_branches': {
                                },
                                'child_leaves': {
                                    'test_alpha': {
                                        'longrepr': None,
                                        'nodeid': 'test_a.py::TestSuite::test_alpha',
                                        'short_id': 'test_alpha',
                                        'status': 'init'
                                    },
                                    'test_beta': {
                                        'longrepr': None,
                                        'nodeid': 'test_a.py::TestSuite::test_beta',
                                        'short_id': 'test_beta',
                                        'status': 'init'
                                    }
                                },
                                'environment_state': 'inactive',
                                'nodeid': 'test_a.py::TestSuite',
                                'short_id': 'TestSuite',
                                'status': 'init'
                            }
                        },
                        'child_leaves': {
                            'test_one': {
                                'longrepr': None,
                                'nodeid': 'test_a.py::test_one',
                                'short_id': 'test_one',
                                'status': 'running'
                            },
                            'test_two': {
                                'longrepr': None,
                                'nodeid': 'test_a.py::test_two',
                                'short_id': 'test_two',
                                'status': 'init'
                            }
                        },
                        'environment_state': 'inactive',
                        'nodeid': 'test_a.py',
                        'short_id': 'test_a.py',
                        'status': 'running'
                    },
                    'test_b.py': {
                        'child_branches': {
                        },
                        'child_leaves': {
                            'test_http_service': {
                                'longrepr': None,
                                'nodeid': 'test_b.py::test_http_service',
                                'short_id': 'test_http_service',
                                'status': 'init'
                            },
                            'test_one': {
                                'longrepr': None,
                                'nodeid': 'test_b.py::test_one',
                                'short_id': 'test_one',
                                'status': 'init'
                            },
                            'test_two': {
                                'longrepr': None,
                                'nodeid': 'test_b.py::test_two',
                                'short_id': 'test_two',
                                'status': 'init'
                            }
                        },
                        'environment_state': 'inactive',
                        'nodeid': 'test_b.py',
                        'short_id': 'test_b.py',
                        'status': 'init'
                    }
                },
                'child_leaves': {
                },
                'environment_state': 'stopped',
                'nodeid': '',
                'short_id': 'pytest_examples',
                'status': 'running'
            }
        ],
        'name': 'update',
        'namespace': '/'
    },
    {
        'args': [
            {
                'child_branches': {
                    'test_a.py': {
                        'child_branches': {
                            'TestSuite': {
                                'child_branches': {
                                },
                                'child_leaves': {
                                    'test_alpha': {
                                        'longrepr': None,
                                        'nodeid': 'test_a.py::TestSuite::test_alpha',
                                        'short_id': 'test_alpha',
                                        'status': 'init'
                                    },
                                    'test_beta': {
                                        'longrepr': None,
                                        'nodeid': 'test_a.py::TestSuite::test_beta',
                                        'short_id': 'test_beta',
                                        'status': 'init'
                                    }
                                },
                                'environment_state': 'inactive',
                                'nodeid': 'test_a.py::TestSuite',
                                'short_id': 'TestSuite',
                                'status': 'init'
                            }
                        },
                        'child_leaves': {
                            'test_one': {
                                'longrepr': None,
                                'nodeid': 'test_a.py::test_one',
                                'short_id': 'test_one',
                                'status': 'running'
                            },
                            'test_two': {
                                'longrepr': None,
                                'nodeid': 'test_a.py::test_two',
                                'short_id': 'test_two',
                                'status': 'init'
                            }
                        },
                        'environment_state': 'inactive',
                        'nodeid': 'test_a.py',
                        'short_id': 'test_a.py',
                        'status': 'running'
                    },
                    'test_b.py': {
                        'child_branches': {
                        },
                        'child_leaves': {
                            'test_http_service': {
                                'longrepr': None,
                                'nodeid': 'test_b.py::test_http_service',
                                'short_id': 'test_http_service',
                                'status': 'init'
                            },
                            'test_one': {
                                'longrepr': None,
                                'nodeid': 'test_b.py::test_one',
                                'short_id': 'test_one',
                                'status': 'init'
                            },
                            'test_two': {
                                'longrepr': None,
                                'nodeid': 'test_b.py::test_two',
                                'short_id': 'test_two',
                                'status': 'init'
                            }
                        },
                        'environment_state': 'inactive',
                        'nodeid': 'test_b.py',
                        'short_id': 'test_b.py',
                        'status': 'init'
                    }
                },
                'child_leaves': {
                },
                'environment_state': 'stopped',
                'nodeid': '',
                'short_id': 'pytest_examples',
                'status': 'running'
            }
        ],
        'name': 'update',
        'namespace': '/'
    },
    {
        'args': [
            {
                'child_branches': {
                    'test_a.py': {
                        'child_branches': {
                            'TestSuite': {
                                'child_branches': {
                                },
                                'child_leaves': {
                                    'test_alpha': {
                                        'longrepr': None,
                                        'nodeid': 'test_a.py::TestSuite::test_alpha',
                                        'short_id': 'test_alpha',
                                        'status': 'init'
                                    },
                                    'test_beta': {
                                        'longrepr': None,
                                        'nodeid': 'test_a.py::TestSuite::test_beta',
                                        'short_id': 'test_beta',
                                        'status': 'init'
                                    }
                                },
                                'environment_state': 'inactive',
                                'nodeid': 'test_a.py::TestSuite',
                                'short_id': 'TestSuite',
                                'status': 'init'
                            }
                        },
                        'child_leaves': {
                            'test_one': {
                                'longrepr': None,
                                'nodeid': 'test_a.py::test_one',
                                'short_id': 'test_one',
                                'status': 'passed'
                            },
                            'test_two': {
                                'longrepr': None,
                                'nodeid': 'test_a.py::test_two',
                                'short_id': 'test_two',
                                'status': 'init'
                            }
                        },
                        'environment_state': 'inactive',
                        'nodeid': 'test_a.py',
                        'short_id': 'test_a.py',
                        'status': 'passed'
                    },
                    'test_b.py': {
                        'child_branches': {
                        },
                        'child_leaves': {
                            'test_http_service': {
                                'longrepr': None,
                                'nodeid': 'test_b.py::test_http_service',
                                'short_id': 'test_http_service',
                                'status': 'init'
                            },
                            'test_one': {
                                'longrepr': None,
                                'nodeid': 'test_b.py::test_one',
                                'short_id': 'test_one',
                                'status': 'init'
                            },
                            'test_two': {
                                'longrepr': None,
                                'nodeid': 'test_b.py::test_two',
                                'short_id': 'test_two',
                                'status': 'init'
                            }
                        },
                        'environment_state': 'inactive',
                        'nodeid': 'test_b.py',
                        'short_id': 'test_b.py',
                        'status': 'init'
                    }
                },
                'child_leaves': {
                },
                'environment_state': 'stopped',
                'nodeid': '',
                'short_id': 'pytest_examples',
                'status': 'passed'
            }
        ],
        'name': 'update',
        'namespace': '/'
    }
]
