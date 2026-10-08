"""Checks for errors that would change the reported findings."""
import unittest
import pandas as pd
import numpy as np
from analysis import parse_rating, profile_values, code_themes, ORIGINAL, SENSITIVITY, interval
from collect import final_answer

class AnalysisChecks(unittest.TestCase):
    def test_exact_rating_match(self):
        self.assertEqual(parse_rating('"Very important"'),(5.0,'valid'))
        self.assertEqual(parse_rating('Important'),(4.0,'valid'))
        self.assertEqual(parse_rating('I considered Important but choose Very important')[1],'invalid')
    def test_refusal_is_not_parse_failure(self):
        self.assertEqual(parse_rating('I don\'t have enough information')[1],'refusal')
        self.assertEqual(parse_rating('Prefer not to answer')[1],'refusal')
        self.assertEqual(parse_rating(None)[1],'missing')
        self.assertEqual(parse_rating('5')[1],'invalid')
    def test_repeated_runs_do_not_triple_sample_size(self):
        d=pd.DataFrame({'profile_id':['a','a','a','b','b','b'],'x':[1,2,3,3,4,5]})
        z=interval(profile_values(d,['x']).x)
        self.assertEqual(z['n'],2);self.assertEqual(z['mean'],3.0)
        self.assertAlmostEqual(z['se'],1.0)
    def test_keywords_are_presence_not_word_counts(self):
        c=code_themes(['nuclear nuclear cost','nothing relevant'],ORIGINAL)
        self.assertEqual(int(c.nuclear.sum()),1)
        self.assertEqual(int(c.sum().sum()),2)
    def test_narrow_energy_terms_remove_ambiguous_match(self):
        s=['financial security','energy security']
        self.assertEqual(int(code_themes(s,ORIGINAL).energy_independence.sum()),2)
        self.assertEqual(int(code_themes(s,SENSITIVITY).energy_independence.sum()),1)
    def test_zero_difference_is_not_an_equivalence_decision(self):
        z=interval([-1,1]);self.assertLess(z['lo'],0);self.assertGreater(z['hi'],0)
        self.assertNotIn('equivalent',z)
    def test_reasoning_is_never_saved_as_an_answer(self):
        r={'choices':[{'finish_reason':'stop','message':{'content':None,'reasoning':'Very important'}}]}
        self.assertEqual(final_answer(r,'rating'),(None,'missing_final_answer'))
    def test_truncated_answer_is_rejected(self):
        r={'choices':[{'finish_reason':'length','message':{'content':'Important'}}]}
        self.assertEqual(final_answer(r,'rating'),(None,'incomplete'))
    def test_complete_final_answer_is_accepted(self):
        r={'choices':[{'finish_reason':'stop','message':{'content':'Very important','reasoning':'Important'}}]}
        self.assertEqual(final_answer(r,'rating'),('Very important','valid'))


class ProfileSampleChecks(unittest.TestCase):
    def test_workbook_profiles_define_sample_and_mismatched_run_fails(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        from analysis import load_data
        with TemporaryDirectory() as td:
            root=Path(td);(root/'1 Survey Results').mkdir()
            human=pd.DataFrame({'Respondent ID':['example-a','example-b'], **{f'Q{i}':['Important','Very important'] for i in range(1,17)}})
            profiles=pd.DataFrame({'Respondent ID':['example-b','example-a']})
            with pd.ExcelWriter(root/'1 Survey Results/survey_results.xlsx') as writer:
                human.to_excel(writer,sheet_name='Responses',index=False)
                profiles.to_excel(writer,sheet_name='demo_cov',index=False)
                pd.DataFrame({'arbitrary_old_flag':[False,False]}).to_excel(writer,sheet_name='All Data',index=False)
            run=root/'5 Final Results/example/run';run.mkdir(parents=True)
            human.to_excel(run/'final_results.xlsx',index=False)
            with patch('analysis.CONFIGS',{'example':(1,'Example')}):
                data,_,_=load_data(root)
                self.assertEqual(len(data[0]),2)
                human.loc[1,'Respondent ID']='example-c'
                human.to_excel(run/'final_results.xlsx',index=False)
                with self.assertRaisesRegex(ValueError,'does not match'):
                    load_data(root)

if __name__=='__main__':unittest.main()
