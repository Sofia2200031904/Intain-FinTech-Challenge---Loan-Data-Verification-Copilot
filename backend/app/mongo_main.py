"""MongoDB persistence entrypoint. Run: uvicorn app.mongo_main:app --reload --port 8000"""
import os,io,json,uuid,hashlib
from datetime import datetime,timedelta,timezone
from typing import Any
import jwt,pandas as pd
from fastapi import FastAPI,Depends,HTTPException,UploadFile,File,status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer,HTTPAuthorizationCredentials
from passlib.context import CryptContext
from pydantic import BaseModel,Field
from pymongo import MongoClient,DESCENDING

client=MongoClient(os.getenv('MONGODB_URI','mongodb://localhost:27017/loan_copilot'),serverSelectionTimeoutMS=5000)
db=client.get_default_database()
if db is None: db=client.loan_copilot
app=FastAPI(title='Loan Data Verification Copilot',version='1.1.0-mongodb')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])
pwd=CryptContext(schemes=['bcrypt'],deprecated='auto');bearer=HTTPBearer()
def now():return datetime.now(timezone.utc)
def clean(x):x=dict(x);x.pop('_id',None);return x
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),default=str).encode()).hexdigest()
def note(dataset,event,actor,detail,loan_id=None):
 user=db.users.find_one({'email':actor})
 db.audits.insert_one({'id':str(uuid.uuid4()),'dataset_id':dataset,'loan_id':loan_id,'event':event,'actor':actor,'role':user.get('role') if user else 'system','detail':detail,'created_at':now()})
def me(c:HTTPAuthorizationCredentials=Depends(bearer)):
 try:e=jwt.decode(c.credentials,os.getenv('JWT_SECRET','dev-secret'),algorithms=['HS256'])['sub']
 except Exception:raise HTTPException(401,'Invalid session')
 u=db.users.find_one({'email':e,'enabled':True})
 if not u:raise HTTPException(401,'User unavailable')
 return clean(u)
def allow(*roles):
 def guard(u=Depends(me)):
  if u['role'] not in roles:raise HTTPException(status.HTTP_403_FORBIDDEN,'Your role is not permitted to perform this action')
  return u
 return guard
def dataset_access(did,u):
 if u['role']=='reviewer' and not db.datasets.find_one({'id':did,'assigned_reviewers':u['email']}):raise HTTPException(403,'This dataset is not assigned to you')
def norm(row):
 d={str(k).strip().lower().replace(' ','_'):(None if pd.isna(v) else str(v).strip()) for k,v in row.items()}
 if d.get('status'):d['status']=d['status'].title()
 for f in ['loan_amount','interest_rate','income','credit_score','loan_term']:
  try:
   if d.get(f) not in (None,''):d[f]=float(str(d[f]).replace('%','').replace(',',''))
  except:pass
 if d.get('origination_date'):
  try:d['origination_date']=pd.to_datetime(d['origination_date'],dayfirst=True).strftime('%Y-%m-%d')
  except:pass
 return d
def rule_setting(key,default):
 rule=db.validation_rules.find_one({'key':key,'enabled':{'$ne':False}})
 return rule.get('value',default) if rule else default
def findings(d,seen):
 r=[];add=lambda f,k,m,s:r.append((f,k,m,s))
 for f in ['loan_id','borrower_name','loan_amount','interest_rate','origination_date','status']:
  if d.get(f) in (None,''):add(f,'required',f'{f.replace("_"," ").title()} is required','high')
 try:
  if float(d.get('loan_amount',0))<=0:add('loan_amount','positive_amount','Loan amount must be greater than zero','critical')
 except:add('loan_amount','numeric','Loan amount must be numeric','high')
 try:
  if not 0<float(d.get('interest_rate',0))<=float(rule_setting('interest_rate_max',35)):add('interest_rate','rate_range',f"Interest rate must be between 0 and {rule_setting('interest_rate_max',35)}%",'critical')
 except:add('interest_rate','numeric','Interest rate must be numeric','high')
 try:
  if d.get('income') not in (None,'') and float(d['income'])<=0:add('income','income_positive','Income must be positive when it is provided','high')
 except:add('income','income_numeric','Income must be numeric when it is provided','medium')
 try:
  if d.get('credit_score') not in (None,'') and not float(rule_setting('credit_score_min',300))<=float(d['credit_score'])<=float(rule_setting('credit_score_max',850)):add('credit_score','credit_score_range',f"Credit score must be between {rule_setting('credit_score_min',300)} and {rule_setting('credit_score_max',850)}",'high')
 except:add('credit_score','credit_score_numeric','Credit score must be numeric when it is provided','medium')
 if d.get('status') and d['status'] not in ['Active','Closed','Delinquent','Paid Off','Pending']:add('status','status_vocabulary','Status is outside the approved vocabulary','medium')
 try:
  if float(d.get('loan_amount',0))>0 and float(d.get('loan_term',0))<=0:add('loan_term','loan_term_positive','A positive loan amount requires a positive loan term','high')
 except:add('loan_term','loan_term_numeric','Loan term must be numeric when a loan amount is present','medium')
 try:
  if d.get('loan_term') not in (None,'') and not 1<=float(d['loan_term'])<=float(rule_setting('loan_term_max',480)):add('loan_term','loan_term_supported_range',f"Loan term must be between 1 and {rule_setting('loan_term_max',480)} months",'high')
 except:pass
 try:
  income=float(d.get('income',0)); amount=float(d.get('loan_amount',0))
  if income>0 and amount>income*float(rule_setting('income_multiple_max',20)):add('loan_amount,income','income_amount_consistency',f"Loan amount is greater than {rule_setting('income_multiple_max',20)}× reported annual income",'high')
 except:pass
 if d.get('status') in ['Closed','Paid Off']:
  try:
   if float(d.get('outstanding_balance',0))>0:add('status,outstanding_balance','closed_balance_consistency','Closed or paid-off loans cannot have an outstanding balance','critical')
  except:add('outstanding_balance','closed_balance_numeric','Outstanding balance must be numeric for closed loans','high')
 if d.get('loan_id') in seen:add('loan_id','duplicate_loan_id','Duplicate loan identifier in this dataset','critical')
 return r
class Login(BaseModel):email:str;password:str
class Review(BaseModel):
 action:str
 changes:dict[str,Any]={}
 reason:str=''
 notes:str=''
 # Kept for requests made by the existing frontend before this enhancement.
 note:str=''
class UserInput(BaseModel):email:str;name:str='';role:str=Field(pattern='^(admin|reviewer|viewer)$');password:str='Demo@123';enabled:bool=True
class RuleUpdate(BaseModel):enabled:bool|None=None;value:float|None=None
@app.on_event('startup')
def boot():
 client.admin.command('ping');db.users.create_index('email',unique=True)
 db.users.update_one({'email':'reviewer@intain.demo'},{'$set':{'password_hash':pwd.hash('Demo@123'),'role':'reviewer','enabled':True},'$setOnInsert':{'id':str(uuid.uuid4()),'email':'reviewer@intain.demo','created_at':now()}},upsert=True)
 db.users.update_one({'email':'admin@intain.demo'},{'$set':{'password_hash':pwd.hash('Admin@123'),'role':'admin','enabled':True,'name':'Demo Admin'},'$setOnInsert':{'id':str(uuid.uuid4()),'email':'admin@intain.demo','created_at':now()}},upsert=True)
 db.users.update_one({'email':'viewer@intain.demo'},{'$set':{'password_hash':pwd.hash('Viewer@123'),'role':'viewer','enabled':True,'name':'Demo Viewer'},'$setOnInsert':{'id':str(uuid.uuid4()),'email':'viewer@intain.demo','created_at':now()}},upsert=True)
 for key,value,label in [('interest_rate_max',35,'Maximum interest rate (%)'),('credit_score_min',300,'Minimum credit score'),('credit_score_max',850,'Maximum credit score'),('loan_term_max',480,'Maximum loan term (months)'),('income_multiple_max',20,'Maximum loan-to-income multiple')]:
  db.validation_rules.update_one({'key':key},{'$setOnInsert':{'key':key,'value':value,'label':label,'enabled':True,'updated_at':now()}},upsert=True)
 # Legacy local demo datasets remain available to the demonstration reviewer.
 db.datasets.update_many({'assigned_reviewers':{'$exists':False}},{'$set':{'assigned_reviewers':['reviewer@intain.demo']}})
@app.post('/auth/login')
def login(x:Login):
 u=db.users.find_one({'email':x.email,'enabled':True})
 if not u or not pwd.verify(x.password,u['password_hash']):raise HTTPException(401,'Incorrect email or password')
 return {'access_token':jwt.encode({'sub':u['email'],'exp':now()+timedelta(hours=8)},os.getenv('JWT_SECRET','dev-secret'),algorithm='HS256'),'user':{'email':u['email'],'role':u['role']}}
def make(name,frame,actor):
 did=str(uuid.uuid4());db.datasets.insert_one({'id':did,'name':name,'created_at':now(),'normalized':False,'validated':False,'uploaded_by':actor,'assigned_reviewers':['reviewer@intain.demo']})
 for i,row in frame.iterrows():
  raw={k:(None if pd.isna(v) else v) for k,v in row.to_dict().items()};n=norm(raw);db.loans.insert_one({'id':str(uuid.uuid4()),'dataset_id':did,'source_row':i+2,'raw':raw,'normalized':n,'record_hash':digest(n),'verified':False,'status':'Unreviewed','corrections':[]})
 note(did,'dataset_uploaded',actor,{'rows':len(frame)});return {'id':did,'name':name,'rows':len(frame),'columns':list(frame.columns)}
@app.post('/datasets/demo')
def demo(u=Depends(allow('admin'))):
 existing=db.datasets.find_one({'name':'intain_demo_messy_loans.csv'},{'id':1,'name':1,'rows':1})
 if existing:
  return {'id':existing['id'],'name':existing['name'],'rows':db.loans.count_documents({'dataset_id':existing['id']}),'columns':['loan_id','borrower_name','loan_amount','interest_rate','loan_term','origination_date','status','income','credit_score'],'reused':True}
 rows=[['LN001','John Smith',250000,8.5,360,'2024-01-15','Active',85000,742],['LN002','Jane Doe',150000,85,360,'15/02/2024','active',None,710],['LN003','Robert Lee',-25000,7.2,180,'2024-03-01','Active',92000,810],['LN003','Robert Lee',25000,7.2,180,'2024-03-01','Active',92000,810],['LN004','Alice Brown',500000,None,240,'2024/04/10','Unknown',120000,690]]
 return make('intain_demo_messy_loans.csv',pd.DataFrame(rows,columns=['loan_id','borrower_name','loan_amount','interest_rate','loan_term','origination_date','status','income','credit_score']),u['email'])
@app.post('/datasets/deduplicate-demo')
def deduplicate_demo(u=Depends(allow('admin'))):
 copies=list(db.datasets.find({'name':'intain_demo_messy_loans.csv'}).sort('created_at',DESCENDING))
 if not copies:return {'kept':None,'removed':0}
 keep=copies[0]['id'];remove=[x['id'] for x in copies[1:]]
 if remove:
  db.loans.delete_many({'dataset_id':{'$in':remove}});db.exceptions.delete_many({'dataset_id':{'$in':remove}});db.audits.delete_many({'dataset_id':{'$in':remove}});db.datasets.delete_many({'id':{'$in':remove}})
 note(keep,'duplicate_demo_datasets_removed',u['email'],{'removed_dataset_count':len(remove)})
 return {'kept':keep,'removed':len(remove)}
@app.post('/datasets/upload')
async def upload(file:UploadFile=File(...),u=Depends(allow('admin'))):
 if not file.filename or not file.filename.lower().endswith(('.csv','.xlsx','.xls')):raise HTTPException(400,'Only CSV and Excel files are accepted')
 raw=await file.read()
 if not raw:raise HTTPException(400,'The uploaded file is empty')
 if len(raw)>10_000_000:raise HTTPException(400,'File exceeds the 10 MB upload limit')
 try:frame=pd.read_excel(io.BytesIO(raw)) if file.filename.lower().endswith(('.xlsx','.xls')) else pd.read_csv(io.BytesIO(raw))
 except Exception:raise HTTPException(400,'The file could not be read as a valid CSV or Excel dataset')
 if frame.empty:raise HTTPException(400,'The uploaded dataset has no records')
 if len(frame)>50_000:raise HTTPException(400,'Dataset exceeds the 50,000-record limit')
 return make(file.filename,frame,u['email'])
@app.get('/datasets')
def datasets(u=Depends(me)):
 query={'assigned_reviewers':u['email']} if u['role']=='reviewer' else {}
 return [clean(x) for x in db.datasets.find(query).sort('created_at',DESCENDING)]
@app.patch('/datasets/{did}/assign-reviewers')
def assign_reviewers(did:str,reviewers:list[str],u=Depends(allow('admin'))):
 valid={x['email'] for x in db.users.find({'role':'reviewer','enabled':True})}
 if not set(reviewers).issubset(valid):raise HTTPException(400,'Assignments must be enabled Reviewer accounts')
 result=db.datasets.update_one({'id':did},{'$set':{'assigned_reviewers':reviewers,'assigned_at':now(),'assigned_by':u['email']}})
 if not result.matched_count:raise HTTPException(404,'Dataset not found')
 note(did,'dataset_reviewer_assignment_updated',u['email'],{'reviewers':reviewers});return {'ok':True,'reviewers':reviewers}
@app.get('/datasets/{did}/profile')
def profile(did:str,u=Depends(me)):
 dataset_access(did,u)
 rows=[x['normalized'] for x in db.loans.find({'dataset_id':did})]
 if not rows:raise HTTPException(404,'Dataset not found')
 f=pd.DataFrame(rows);return {'rows':len(f),'columns':[{'name':c,'missing':int(f[c].isna().sum()+(f[c]=='').sum() if f[c].dtype=='object' else f[c].isna().sum()),'unique':int(f[c].nunique())} for c in f.columns],'schema':{c:str(f[c].dtype) for c in f.columns}}
@app.post('/datasets/{did}/normalize')
def normalize(did:str,u=Depends(allow('admin'))):
 for l in db.loans.find({'dataset_id':did}):
  n=norm(l['raw']);db.loans.update_one({'_id':l['_id']},{'$set':{'normalized':n,'record_hash':digest(n)}})
 db.datasets.update_one({'id':did},{'$set':{'normalized':True}});note(did,'dataset_normalized',u['email'],{});return {'ok':True}
@app.post('/datasets/{did}/validate')
def validate(did:str,u=Depends(allow('admin'))):
 # Preserve the lifecycle of prior findings; only the latest findings are active.
 db.exceptions.update_many({'dataset_id':did,'status':{'$in':['open','under_review']}},{'$set':{'status':'superseded','superseded_at':now()}});seen=set();n=0
 for l in db.loans.find({'dataset_id':did}):
  results=findings(l['normalized'],seen)
  for field,rule,msg,severity in results:db.exceptions.insert_one({'id':str(uuid.uuid4()),'dataset_id':did,'loan_id':l['id'],'field':field,'rule':rule,'message':msg,'severity':severity,'status':'open','actual':l['normalized'].get(field),'created_at':now()});n+=1
  db.loans.update_one({'_id':l['_id']},{'$set':{'verified':not results,'status':'Verified' if not results else 'Needs Review'}})
  seen.add(l['normalized'].get('loan_id'))
 db.datasets.update_one({'id':did},{'$set':{'validated':True}});note(did,'validation_completed',u['email'],{'exceptions':n});return {'exceptions':n}
@app.get('/datasets/{did}/overview')
def overview(did:str,u=Depends(me)):
 dataset_access(did,u)
 loans=list(db.loans.find({'dataset_id':did}));issues=list(db.exceptions.find({'dataset_id':did}));op=[x for x in issues if x['status'] in ['open','under_review']];score=round(max(0,100-sum({'critical':12,'high':6,'medium':3,'low':1}[x['severity']] for x in op)/max(len(loans),1)),1)
 return {'records':len(loans),'verified':sum(x['verified'] for x in loans),'quality_score':score,'exceptions':{s:sum(x['severity']==s and x['status'] in ['open','under_review'] for x in issues) for s in ['critical','high','medium','low']},'resolved':sum(x['status']=='resolved' for x in issues),'record_statuses':{s:sum(x.get('status','Unreviewed')==s for x in loans) for s in ['Unreviewed','Needs Review','In Review','Verified','Rejected']}}
@app.get('/datasets/{did}/exceptions')
def exceptions(did:str,status:str='open',u=Depends(me)):
 dataset_access(did,u)
 return [{**clean(x),'record':db.loans.find_one({'id':x['loan_id']})['normalized']} for x in db.exceptions.find({'dataset_id':did,'status':status})]
@app.get('/datasets/{did}/audit')
def audit_history(did:str,u=Depends(me)):
 dataset_access(did,u)
 return [clean(x) for x in db.audits.find({'dataset_id':did}).sort('created_at',DESCENDING)]
@app.get('/admin/users')
def list_users(u=Depends(allow('admin'))):
 return [clean({k:v for k,v in user.items() if k!='password_hash'}) for user in db.users.find().sort('email')]
@app.post('/admin/users')
def create_user(x:UserInput,u=Depends(allow('admin'))):
 if db.users.find_one({'email':x.email}):raise HTTPException(409,'A user with this email already exists')
 record={'id':str(uuid.uuid4()),'email':x.email,'name':x.name,'role':x.role,'enabled':x.enabled,'password_hash':pwd.hash(x.password),'created_at':now()}
 db.users.insert_one(record);note('system','user_created',u['email'],{'user':x.email,'role':x.role});return clean({k:v for k,v in record.items() if k!='password_hash'})
@app.patch('/admin/users/{email}')
def update_user(email:str,x:UserInput,u=Depends(allow('admin'))):
 update={'name':x.name,'role':x.role,'enabled':x.enabled}
 if x.password:update['password_hash']=pwd.hash(x.password)
 result=db.users.update_one({'email':email},{'$set':update})
 if not result.matched_count:raise HTTPException(404,'User not found')
 note('system','user_updated',u['email'],{'user':email,'role':x.role,'enabled':x.enabled});return {'ok':True}
@app.get('/admin/validation-rules')
def list_rules(u=Depends(allow('admin'))):return [clean(x) for x in db.validation_rules.find().sort('key')]
@app.patch('/admin/validation-rules/{key}')
def update_rule(key:str,x:RuleUpdate,u=Depends(allow('admin'))):
 update={k:v for k,v in {'enabled':x.enabled,'value':x.value}.items() if v is not None}
 if not update:raise HTTPException(400,'Provide enabled or value')
 update['updated_at']=now();result=db.validation_rules.update_one({'key':key},{'$set':update})
 if not result.matched_count:raise HTTPException(404,'Rule not found')
 note('system','validation_rule_updated',u['email'],{'rule':key,**update});return {'ok':True}
@app.get('/datasets/{did}/verification')
def verification_view(did:str,u=Depends(me)):
 dataset_access(did,u)
 rows=[]
 for x in db.loans.find({'dataset_id':did}).sort('source_row'):
  issues=list(db.exceptions.find({'dataset_id':did,'loan_id':x['id'],'status':{'$in':['open','under_review']}}))
  rows.append({'loan_id':x['normalized'].get('loan_id',x['id']),'record_key':x['id'],'status':x.get('status','Unreviewed'),'verified':x.get('verified',False),'open_exception_count':len(issues),'severities':sorted({issue['severity'] for issue in issues}),'record_hash':x['record_hash'],'source_row':x['source_row']})
 return rows
@app.post('/exceptions/{eid}/ai')
def ai(eid:str,u=Depends(allow('admin','reviewer'))):
 x=db.exceptions.find_one({'id':eid});
 if not x:raise HTTPException(404,'Exception not found')
 e=f"The deterministic rule '{x['rule']}' flagged {x['field']}: {x['message']}. This can affect servicing, pricing, and reporting.";s=f"Review source evidence for {x['field']}. Correct only if supported; no data has been changed.";db.exceptions.update_one({'_id':x['_id']},{'$set':{'ai_explanation':e,'ai_suggestion':s}});note(x['dataset_id'],'ai_assistance_generated',u['email'],{'exception':eid},x['loan_id']);return {'explanation':e,'suggestion':s}
@app.post('/exceptions/{eid}/start-review')
def start_review(eid:str,u=Depends(allow('reviewer'))):
 ex=db.exceptions.find_one({'id':eid})
 if not ex:raise HTTPException(404,'Exception not found')
 db.exceptions.update_one({'_id':ex['_id'],'status':'open'},{'$set':{'status':'under_review','under_review_at':now(),'under_review_by':u['email']}})
 db.loans.update_one({'id':ex['loan_id']},{'$set':{'status':'In Review'}})
 note(ex['dataset_id'],'exception_under_review',u['email'],{'exception':eid,'field':ex['field'],'previous_status':'open','new_status':'under_review'},ex['loan_id'])
 return {'ok':True,'record_status':'In Review'}
@app.post('/exceptions/{eid}/review')
def review(eid:str,x:Review,u=Depends(allow('reviewer'))):
 ex=db.exceptions.find_one({'id':eid});loan=db.loans.find_one({'id':ex['loan_id']}) if ex else None
 if not loan:raise HTTPException(404,'Exception not found')
 if x.action not in ['approve','reject']:raise HTTPException(400,'Action must be approve or reject')
 reviewer_reason=(x.reason or x.note).strip()
 if len(reviewer_reason)<3:raise HTTPException(422,'A correction reason of at least 3 characters is required')
 before=dict(loan['normalized']);previous_hash=loan['record_hash']
 if x.action=='reject':
  db.exceptions.update_one({'_id':ex['_id']},{'$set':{'status':'rejected','reviewed_at':now(),'reviewed_by':u['email'],'reason':reviewer_reason,'notes':x.notes}})
  db.loans.update_one({'_id':loan['_id']},{'$set':{'verified':False,'status':'Rejected'}})
  note(ex['dataset_id'],'exception_rejected',u['email'],{'loan_id':loan['id'],'field':ex['field'],'before':before.get(ex['field']),'after':before.get(ex['field']),'reason':reviewer_reason,'notes':x.notes,'previous_status':ex['status'],'new_status':'rejected','validation_result':'not_applicable','previous_hash':previous_hash,'new_hash':previous_hash},loan['id'])
  return {'ok':True,'previous_hash':previous_hash,'hash':previous_hash,'validation_result':'not_applicable','exception_resolved':False,'record_status':'Rejected'}
 after=norm({**before,**x.changes});new_hash=digest(after)
 changed=[{'field':k,'original':before.get(k),'corrected':after.get(k)} for k in x.changes if before.get(k)!=after.get(k)]
 db.loans.update_one({'_id':loan['_id']},{'$set':{'normalized':after,'record_hash':new_hash,'status':'In Review'},'$push':{'corrections':{'at':now(),'reviewer':u['email'],'role':u['role'],'reason':reviewer_reason,'notes':x.notes,'changes':changed,'previous_hash':previous_hash,'new_hash':new_hash}}})
 # Re-run all deterministic rules applicable to this record. AI is never used here.
 seen={item['normalized'].get('loan_id') for item in db.loans.find({'dataset_id':ex['dataset_id'],'id':{'$ne':loan['id']}})}
 current=findings(after,seen)
 still_failing=any(field==ex['field'] and rule==ex['rule'] for field,rule,_,_ in current)
 new_status='under_review' if still_failing else 'resolved'
 db.exceptions.update_one({'_id':ex['_id']},{'$set':{'status':new_status,'reviewed_at':now(),'reviewed_by':u['email'],'reason':reviewer_reason,'notes':x.notes,'validation_result':'failed' if still_failing else 'passed'}})
 for field,rule,msg,severity in current:
  if field==ex['field'] and rule==ex['rule']:continue
  if not db.exceptions.find_one({'dataset_id':ex['dataset_id'],'loan_id':loan['id'],'field':field,'rule':rule,'status':{'$in':['open','under_review']}}):
   db.exceptions.insert_one({'id':str(uuid.uuid4()),'dataset_id':ex['dataset_id'],'loan_id':loan['id'],'field':field,'rule':rule,'message':msg,'severity':severity,'status':'open','actual':after.get(field),'created_at':now()})
 remaining=list(db.exceptions.find({'dataset_id':ex['dataset_id'],'loan_id':loan['id'],'status':{'$in':['open','under_review']}}))
 verification='Verified' if not remaining else 'Needs Review'
 db.loans.update_one({'_id':loan['_id']},{'$set':{'verified':verification=='Verified','status':verification}})
 validation_result='passed' if not remaining else 'failed'
 note(ex['dataset_id'],'loan_record_corrected',u['email'],{'loan_id':loan['id'],'field':ex['field'],'before':before.get(ex['field']),'after':after.get(ex['field']),'reason':reviewer_reason,'notes':x.notes,'previous_status':ex['status'],'new_status':new_status,'validation_result':validation_result,'previous_hash':previous_hash,'new_hash':new_hash},loan['id'])
 note(ex['dataset_id'],'record_revalidated',u['email'],{'result':validation_result,'open_issues':len(remaining)},loan['id'])
 return {'ok':True,'previous_hash':previous_hash,'hash':new_hash,'validation_result':validation_result,'exception_resolved':new_status=='resolved','record_status':verification}
@app.get('/loans/{loan_id}/history')
def loan_history(loan_id:str,u=Depends(me)):
 loan=db.loans.find_one({'id':loan_id})
 if not loan:raise HTTPException(404,'Loan not found')
 dataset=db.datasets.find_one({'id':loan['dataset_id']})
 audit=[]
 for item in db.audits.find({'loan_id':loan_id}).sort('created_at',DESCENDING):
  entry=clean(item);detail=entry.get('detail',{})
  if detail.get('field'):
   entry['event']=f"{entry['event']} · {detail['field']}: {detail.get('before')} → {detail.get('after')} · validation: {detail.get('validation_result','recorded')}"
  entry['display']={'timestamp':entry['created_at'],'user':entry['actor'],'role':entry.get('role','system'),'action':entry['event'],'loan_id':loan_id,'field':detail.get('field'),'before':detail.get('before'),'after':detail.get('after'),'reviewer_notes':detail.get('reason'),'validation_result':detail.get('validation_result'),'previous_hash':detail.get('previous_hash'),'new_hash':detail.get('new_hash')}
  audit.append(entry)
 return {'loan_id':loan['normalized'].get('loan_id',loan_id),'record_key':loan_id,'status':loan.get('status','Unreviewed'),'raw':loan['raw'],'normalized':loan['normalized'],'record_hash':loan['record_hash'],'provenance':{'dataset':dataset['name'],'uploaded_by':dataset['uploaded_by'],'uploaded_at':dataset['created_at'],'source_row':loan['source_row']},'corrections':loan.get('corrections',[]),'audit':audit}
@app.get('/datasets/{did}/export/{kind}')
def export(did:str,kind:str,u=Depends(me)):
 dataset_access(did,u)
 if kind=='verified':rows=[{**x['normalized'],'record_hash':x['record_hash']} for x in db.loans.find({'dataset_id':did,'verified':True})]
 elif kind=='exceptions':rows=[clean(x) for x in db.exceptions.find({'dataset_id':did})]
 elif kind=='audit':rows=[clean(x) for x in db.audits.find({'dataset_id':did}).sort('created_at',DESCENDING)]
 else:raise HTTPException(404,'Unknown export type')
 return StreamingResponse(io.StringIO(pd.DataFrame(rows).to_csv(index=False)),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename={kind}_{did}.csv'})
