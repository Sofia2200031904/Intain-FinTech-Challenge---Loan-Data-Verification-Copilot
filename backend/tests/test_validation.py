import sys
sys.path.insert(0,'backend')
from app.main import normalize, rules, hash_record
def test_normalizes_and_flags_bad_rate():
 d=normalize({'loan_id':'A1','status':'active','loan_amount':'1000','interest_rate':'85%','origination_date':'15/02/2024'})
 assert d['status']=='Active' and d['origination_date']=='2024-02-15'
 assert any(x[1]=='rate_range' for x in rules(d,set()))
def test_hash_is_repeatable():
 assert hash_record({'b':2,'a':1})==hash_record({'a':1,'b':2})
