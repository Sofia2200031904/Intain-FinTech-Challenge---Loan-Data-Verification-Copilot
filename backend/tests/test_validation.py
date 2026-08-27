import sys
import pytest
from fastapi import HTTPException
sys.path.insert(0,"backend")
from app import mongo_main

def test_normalizes_dates_numbers_and_statuses():
 record=mongo_main.norm({"Loan ID":" A1 ","Status":"active","Loan Amount":"1,000","Interest Rate":"8.5%","Origination Date":"15/02/2024"})
 assert record["loan_id"]=="A1"
 assert record["status"]=="Active"
 assert record["loan_amount"]==1000
 assert record["interest_rate"]==8.5
 assert record["origination_date"]=="2024-02-15"

def test_hash_is_repeatable_and_changes_with_content():
 assert mongo_main.digest({"b":2,"a":1})==mongo_main.digest({"a":1,"b":2})
 assert mongo_main.digest({"a":1})!=mongo_main.digest({"a":2})

def test_deterministic_rules_flag_bad_values(monkeypatch):
 monkeypatch.setattr(mongo_main,"rule_setting",lambda _key,default:default)
 record=mongo_main.norm({"loan_id":"A1","borrower_name":"Test","loan_amount":"-100","interest_rate":"85%","loan_term":"360","origination_date":"2024-01-01","status":"mystery"})
 rules={finding[1] for finding in mongo_main.findings(record,set())}
 assert {"positive_amount","rate_range","status_vocabulary"}<=rules

def test_duplicate_loan_identifier_is_critical(monkeypatch):
 monkeypatch.setattr(mongo_main,"rule_setting",lambda _key,default:default)
 record=mongo_main.norm({"loan_id":"A1","borrower_name":"Test","loan_amount":1000,"interest_rate":8,"loan_term":12,"origination_date":"2024-01-01","status":"Active"})
 assert any(x[1]=="duplicate_loan_id" and x[3]=="critical" for x in mongo_main.findings(record,{"A1"}))

def valid_record():
 return mongo_main.norm({"loan_id":"A1","borrower_name":"Test","loan_amount":25000,"interest_rate":8,"loan_term":12,"origination_date":"2024-01-01","status":"Active","income":50000})

def test_no_op_correction_is_rejected_before_persistence(monkeypatch):
 monkeypatch.setattr(mongo_main,"rule_setting",lambda _key,default:default)
 before=valid_record();exception={"field":"loan_amount","rule":"positive_amount"}
 with pytest.raises(HTTPException) as error:mongo_main.correction_preview(exception,before,{"loan_amount":25000},set())
 assert error.value.status_code==422 and "different" in error.value.detail

def test_still_invalid_correction_is_rejected(monkeypatch):
 monkeypatch.setattr(mongo_main,"rule_setting",lambda _key,default:default)
 before={**valid_record(),"loan_amount":-25000};exception={"field":"loan_amount","rule":"positive_amount"}
 with pytest.raises(HTTPException) as error:mongo_main.correction_preview(exception,before,{"loan_amount":-100},set())
 assert error.value.status_code==422 and "greater than zero" in error.value.detail

def test_valid_correction_passes_and_has_accurate_evidence(monkeypatch):
 monkeypatch.setattr(mongo_main,"rule_setting",lambda _key,default:default)
 before={**valid_record(),"loan_amount":-25000};exception={"field":"loan_amount","rule":"positive_amount"}
 after,changed,current=mongo_main.correction_preview(exception,before,{"loan_amount":25000},set())
 assert after["loan_amount"]==25000 and changed==[{"field":"loan_amount","original":-25000,"corrected":25000}]
 assert not any(rule=="positive_amount" for _,rule,_,_ in current)
 assert mongo_main.audit_change_values(changed)==("loan_amount",-25000,25000)

def test_compound_rule_requires_a_real_affected_field(monkeypatch):
 monkeypatch.setattr(mongo_main,"rule_setting",lambda _key,default:default)
 before={**valid_record(),"loan_amount":2_000_000};exception={"field":"loan_amount,income","rule":"income_amount_consistency"}
 with pytest.raises(HTTPException):mongo_main.correction_preview(exception,before,{"status":"Active"},set())
 after,changed,_=mongo_main.correction_preview(exception,before,{"loan_amount":25000},set())
 assert after["loan_amount"]==25000 and changed[0]["field"]=="loan_amount"

def test_dataset_export_and_preview_views_are_declared():
 routes={route.path for route in mongo_main.app.routes}
 assert '/datasets/{did}/records' in routes
 assert '/datasets/{did}/export/{kind}' in routes
