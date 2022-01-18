import os, textwrap
import numpy as np
import unittest

from typing import Set, List
from pathlib import Path
try:
    from context import dpgen2
except ModuleNotFoundError:
    # case of upload everything to argo, no context needed
    pass
from dflow.python import (
    FatalError,
)
from dpgen2.exploration.scheduler import (
    ConstTrustLevelStageScheduler,
    ExplorationScheduler,
)
from dpgen2.exploration.stage import ExplorationStage
from dpgen2.exploration.report import ExplorationReport
from dpgen2.utils.lmp_task_group import LmpTaskGroup
from dpgen2.utils.trust_level import TrustLevel
from dpgen2.utils.conf_selector import TrustLevelConfSelector

class MockedLmpTaskGroup(LmpTaskGroup):
    pass

class MockedLmpTaskGroup1(LmpTaskGroup):
    pass

class MockedStage(ExplorationStage):
    def make_lmp_task_group(self):
        return MockedLmpTaskGroup()

class MockedStage1(ExplorationStage):
    def make_lmp_task_group(self):
        return MockedLmpTaskGroup1()

class MockedExplorationReport(ExplorationReport):
    def __init__(self):
        self.failed = 1.
        self.accurate = 0.
        self.candidate = 0.

    def failed_ratio (
            self, 
            tag = None,
    ) -> float :
        return self.failed

    def accurate_ratio (
            self,
            tag = None,
    ) -> float :
        return self.accurate

    def candidate_ratio (
            self,
            tag = None,
    ) -> float :
        return self.candidate


class TestConstTrustLevelStageScheduler(unittest.TestCase):
    def test_success(self):
        self.trust_level = TrustLevel(0.1, 0.3)
        self.scheduler = ConstTrustLevelStageScheduler(
            MockedStage(),
            self.trust_level,
        )    
        foo_report = MockedExplorationReport()
        foo_report.accurate = 1.
        foo_report.failed = 0.
            
        conv, ltg, sel = self.scheduler.plan_next_iteration()
        self.assertEqual(conv, False)
        self.assertTrue(isinstance(ltg, MockedLmpTaskGroup))
        self.assertTrue(isinstance(sel, TrustLevelConfSelector))        
        self.assertEqual(sel.trust_level.level_f_lo, 0.1)
        self.assertEqual(sel.trust_level.level_f_hi, 0.3)
        self.assertTrue(sel.trust_level.level_v_lo is None)
        self.assertTrue(sel.trust_level.level_v_hi is None)

        conv, ltg, sel = self.scheduler.plan_next_iteration([], foo_report, [])        
        self.assertEqual(conv, True)
        self.assertTrue(ltg is None)
        self.assertTrue(sel is None)
        # self.assertTrue(isinstance(sel, TrustLevelConfSelector))        
        # self.assertEqual(sel.trust_level.level_f_lo, 0.1)
        # self.assertEqual(sel.trust_level.level_f_hi, 0.3)
        # self.assertTrue(sel.trust_level.level_v_lo is None)
        # self.assertTrue(sel.trust_level.level_v_hi is None)

    def test_step1(self):
        self.trust_level = TrustLevel(0.1, 0.3)
        self.scheduler = ConstTrustLevelStageScheduler(
            MockedStage(),
            self.trust_level,
        )    

        foo_report = MockedExplorationReport()
        foo_report.accurate = 0.5
        foo_report.failed = 0.5          
        bar_report = MockedExplorationReport()
        bar_report.accurate = 1.
        bar_report.failed = 0.         

        conv, ltg, sel = self.scheduler.plan_next_iteration()
        self.assertEqual(conv, False)
        self.assertTrue(isinstance(ltg, MockedLmpTaskGroup))
        self.assertTrue(isinstance(sel, TrustLevelConfSelector))        
        self.assertEqual(sel.trust_level.level_f_lo, 0.1)
        self.assertEqual(sel.trust_level.level_f_hi, 0.3)
        self.assertTrue(sel.trust_level.level_v_lo is None)
        self.assertTrue(sel.trust_level.level_v_hi is None)

        conv, ltg, sel = self.scheduler.plan_next_iteration([], foo_report, [])
        self.assertEqual(conv, False)
        self.assertTrue(isinstance(ltg, MockedLmpTaskGroup))
        self.assertTrue(isinstance(sel, TrustLevelConfSelector))        
        self.assertEqual(sel.trust_level.level_f_lo, 0.1)
        self.assertEqual(sel.trust_level.level_f_hi, 0.3)
        self.assertTrue(sel.trust_level.level_v_lo is None)
        self.assertTrue(sel.trust_level.level_v_hi is None)

        conv, ltg, sel = self.scheduler.plan_next_iteration([], bar_report, [])
        self.assertEqual(conv, True)
        self.assertTrue(ltg is None)
        self.assertTrue(sel is None)
        # self.assertTrue(isinstance(sel, TrustLevelConfSelector))        
        # self.assertEqual(sel.trust_level.level_f_lo, 0.1)
        # self.assertEqual(sel.trust_level.level_f_hi, 0.3)
        # self.assertTrue(sel.trust_level.level_v_lo is None)
        # self.assertTrue(sel.trust_level.level_v_hi is None)

        
    def test_max_numb_iter(self):
        self.trust_level = TrustLevel(0.1, 0.3)
        self.scheduler = ConstTrustLevelStageScheduler(
            MockedStage(),
            self.trust_level,
            max_numb_iter = 2
        )    

        foo_report = MockedExplorationReport()
        foo_report.accurate = 0.5
        foo_report.failed = 0.5          
        bar_report = MockedExplorationReport()
        bar_report.accurate = 1.
        bar_report.failed = 0.         

        conv, ltg, sel = self.scheduler.plan_next_iteration()
        self.assertEqual(conv, False)
        self.assertTrue(isinstance(ltg, MockedLmpTaskGroup))
        self.assertTrue(isinstance(sel, TrustLevelConfSelector))        
        self.assertEqual(sel.trust_level.level_f_lo, 0.1)
        self.assertEqual(sel.trust_level.level_f_hi, 0.3)
        self.assertTrue(sel.trust_level.level_v_lo is None)
        self.assertTrue(sel.trust_level.level_v_hi is None)

        conv, ltg, sel = self.scheduler.plan_next_iteration([], foo_report, [])        
        self.assertEqual(conv, False)
        self.assertTrue(isinstance(ltg, MockedLmpTaskGroup))
        self.assertTrue(isinstance(sel, TrustLevelConfSelector))        
        self.assertEqual(sel.trust_level.level_f_lo, 0.1)
        self.assertEqual(sel.trust_level.level_f_hi, 0.3)
        self.assertTrue(sel.trust_level.level_v_lo is None)
        self.assertTrue(sel.trust_level.level_v_hi is None)

        with self.assertRaisesRegex(FatalError, 'reached maximal number of iterations'):
            conv, ltg, sel = self.scheduler.plan_next_iteration([], foo_report, [])


class TestExplorationScheduler(unittest.TestCase):
    def test_success(self):
        scheduler = ExplorationScheduler()        
        trust_level = TrustLevel(0.1, 0.3)
        stage_scheduler = ConstTrustLevelStageScheduler(
            MockedStage(),
            trust_level,
            max_numb_iter = 2,
        )
        scheduler.add_stage_scheduler(stage_scheduler)
        trust_level = TrustLevel(0.2, 0.4)
        stage_scheduler = ConstTrustLevelStageScheduler(
            MockedStage1(),
            trust_level,
            max_numb_iter = 2,
        )
        scheduler.add_stage_scheduler(stage_scheduler)

        foo_report = MockedExplorationReport()
        foo_report.accurate = 0.5
        foo_report.failed = 0.5          
        bar_report = MockedExplorationReport()
        bar_report.accurate = 1.0
        bar_report.failed = 0.0        
        
        conv, ltg, sel = scheduler.plan_next_iteration()
        self.assertEqual(conv, False)
        self.assertTrue(isinstance(ltg, MockedLmpTaskGroup))
        self.assertTrue(isinstance(sel, TrustLevelConfSelector))
        self.assertEqual(sel.trust_level.level_f_lo, 0.1)
        self.assertEqual(sel.trust_level.level_f_hi, 0.3)
        self.assertTrue(sel.trust_level.level_v_lo is None)
        self.assertTrue(sel.trust_level.level_v_hi is None)
        self.assertEqual(scheduler.get_stage(), 0)
        self.assertEqual(scheduler.get_iteration(), 0)
        conv, ltg, sel = scheduler.plan_next_iteration(bar_report, [])        
        self.assertEqual(conv, False)
        self.assertTrue(isinstance(ltg, MockedLmpTaskGroup1))
        self.assertTrue(isinstance(sel, TrustLevelConfSelector))
        self.assertEqual(sel.trust_level.level_f_lo, 0.2)
        self.assertEqual(sel.trust_level.level_f_hi, 0.4)
        self.assertTrue(sel.trust_level.level_v_lo is None)
        self.assertTrue(sel.trust_level.level_v_hi is None)
        self.assertEqual(scheduler.get_stage(), 1)
        self.assertEqual(scheduler.get_iteration(), 1)
        conv, ltg, sel = scheduler.plan_next_iteration(foo_report, [])
        self.assertEqual(conv, False)
        self.assertTrue(isinstance(ltg, MockedLmpTaskGroup1))
        self.assertTrue(isinstance(sel, TrustLevelConfSelector))
        self.assertEqual(sel.trust_level.level_f_lo, 0.2)
        self.assertEqual(sel.trust_level.level_f_hi, 0.4)
        self.assertTrue(sel.trust_level.level_v_lo is None)
        self.assertTrue(sel.trust_level.level_v_hi is None)
        self.assertEqual(scheduler.get_stage(), 1)
        self.assertEqual(scheduler.get_iteration(), 2)
        conv, ltg, sel = scheduler.plan_next_iteration(bar_report, [])
        self.assertEqual(conv, True)
        self.assertTrue(ltg is None)
        self.assertTrue(sel is None)
        self.assertEqual(scheduler.get_stage(), 2)
        self.assertEqual(scheduler.get_iteration(), 2)


    def test_failed_stage0(self):
        scheduler = ExplorationScheduler()        
        trust_level = TrustLevel(0.1, 0.3)
        stage_scheduler = ConstTrustLevelStageScheduler(
            MockedStage(),
            trust_level,
            max_numb_iter = 2,
        )
        scheduler.add_stage_scheduler(stage_scheduler)
        trust_level = TrustLevel(0.2, 0.4)
        stage_scheduler = ConstTrustLevelStageScheduler(
            MockedStage1(),
            trust_level,
            max_numb_iter = 2,
        )
        scheduler.add_stage_scheduler(stage_scheduler)

        foo_report = MockedExplorationReport()
        foo_report.accurate = 0.5
        foo_report.failed = 0.5          
        bar_report = MockedExplorationReport()
        bar_report.accurate = 1.0
        bar_report.failed = 0.0        
        
        conv, ltg, sel = scheduler.plan_next_iteration()
        self.assertEqual(conv, False)
        self.assertTrue(isinstance(ltg, MockedLmpTaskGroup))
        self.assertTrue(isinstance(sel, TrustLevelConfSelector))
        self.assertEqual(sel.trust_level.level_f_lo, 0.1)
        self.assertEqual(sel.trust_level.level_f_hi, 0.3)
        self.assertTrue(sel.trust_level.level_v_lo is None)
        self.assertTrue(sel.trust_level.level_v_hi is None)
        self.assertEqual(scheduler.get_stage(), 0)
        self.assertEqual(scheduler.get_iteration(), 0)
        conv, ltg, sel = scheduler.plan_next_iteration(foo_report, [])        
        self.assertEqual(conv, False)
        self.assertTrue(isinstance(ltg, MockedLmpTaskGroup))
        self.assertTrue(isinstance(sel, TrustLevelConfSelector))
        self.assertEqual(sel.trust_level.level_f_lo, 0.1)
        self.assertEqual(sel.trust_level.level_f_hi, 0.3)
        self.assertTrue(sel.trust_level.level_v_lo is None)
        self.assertTrue(sel.trust_level.level_v_hi is None)
        self.assertEqual(scheduler.get_stage(), 0)
        self.assertEqual(scheduler.get_iteration(), 1)
        with self.assertRaisesRegex(FatalError, 'stage 0: reached maximal number of iterations'):
            conv, ltg, sel = scheduler.plan_next_iteration(foo_report, [])


    def test_failed_stage1(self):
        scheduler = ExplorationScheduler()        
        trust_level = TrustLevel(0.1, 0.3)
        stage_scheduler = ConstTrustLevelStageScheduler(
            MockedStage(),
            trust_level,
            max_numb_iter = 2,
        )
        scheduler.add_stage_scheduler(stage_scheduler)
        trust_level = TrustLevel(0.2, 0.4)
        stage_scheduler = ConstTrustLevelStageScheduler(
            MockedStage1(),
            trust_level,
            max_numb_iter = 2,
        )
        scheduler.add_stage_scheduler(stage_scheduler)

        foo_report = MockedExplorationReport()
        foo_report.accurate = 0.5
        foo_report.failed = 0.5          
        bar_report = MockedExplorationReport()
        bar_report.accurate = 1.0
        bar_report.failed = 0.0        
        
        conv, ltg, sel = scheduler.plan_next_iteration()
        self.assertEqual(conv, False)
        self.assertTrue(isinstance(ltg, MockedLmpTaskGroup))
        self.assertTrue(isinstance(sel, TrustLevelConfSelector))
        self.assertEqual(sel.trust_level.level_f_lo, 0.1)
        self.assertEqual(sel.trust_level.level_f_hi, 0.3)
        self.assertTrue(sel.trust_level.level_v_lo is None)
        self.assertTrue(sel.trust_level.level_v_hi is None)
        self.assertEqual(scheduler.get_stage(), 0)
        self.assertEqual(scheduler.get_iteration(), 0)
        conv, ltg, sel = scheduler.plan_next_iteration(bar_report, [])        
        self.assertEqual(conv, False)
        self.assertTrue(isinstance(ltg, MockedLmpTaskGroup1))
        self.assertTrue(isinstance(sel, TrustLevelConfSelector))
        self.assertEqual(sel.trust_level.level_f_lo, 0.2)
        self.assertEqual(sel.trust_level.level_f_hi, 0.4)
        self.assertTrue(sel.trust_level.level_v_lo is None)
        self.assertTrue(sel.trust_level.level_v_hi is None)
        self.assertEqual(scheduler.get_stage(), 1)
        self.assertEqual(scheduler.get_iteration(), 1)
        conv, ltg, sel = scheduler.plan_next_iteration(foo_report, [])        
        self.assertEqual(conv, False)
        self.assertTrue(isinstance(ltg, MockedLmpTaskGroup1))
        self.assertTrue(isinstance(sel, TrustLevelConfSelector))
        self.assertEqual(sel.trust_level.level_f_lo, 0.2)
        self.assertEqual(sel.trust_level.level_f_hi, 0.4)
        self.assertTrue(sel.trust_level.level_v_lo is None)
        self.assertTrue(sel.trust_level.level_v_hi is None)
        self.assertEqual(scheduler.get_stage(), 1)
        self.assertEqual(scheduler.get_iteration(), 2)
        with self.assertRaisesRegex(FatalError, 'stage 1: reached maximal number of iterations'):
            conv, ltg, sel = scheduler.plan_next_iteration(foo_report, [])
        
    