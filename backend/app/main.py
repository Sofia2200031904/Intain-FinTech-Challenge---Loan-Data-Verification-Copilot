import os, io, json, hashlib, uuid, re
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt, pandas as pd
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import create_engine, String, Integer, Float, DateTime, Text, ForeignKey, select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session, sessionmaker

DATABASE_URL=os.getenv('DATABASE_URL','sqlite:///./loan_copilot.db')
connect_args={'check_same_thread':False} if DATABASE_URL.startswith('sqlite') else {}
engine=create_engine(DATABASE_URL, connect_args=connect_args); SessionLocal=sessionmaker(bind=engine)
class Base(DeclarativeBase): pass
class User(Base):
 __tablename__='users'
 id:Mapped[int]=mapped_column(primary_key=True); email:Mapped[str]=mapped_column(String(160),unique=True); password_hash:Mapped[str]=mapped_column(String(255)); role:Mapped[str]=mapped_column(String(30),default='reviewer')
class Dataset(Base):
 __tablename__='datasets'
 id:Mapped[str]=mapped_column(String(36),primary_key=True); name:Mapped[str]=mapped_column(String(255)); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow); normalized:Mapped[bool]=mapped_column(default=False); validated:Mapped[bool]=mapped_column(default=False)
class Loan(Base):
 __tablename__='loans'
 id:Mapped[int]=mapped_column(primary_key=True); dataset_id:Mapped[str]=mapped_column(ForeignKey('datasets.id')); source_row:Mapped[int]=mapped_column(); data:Mapped[str]=mapped_column(Text); normalized_data:Mapped[str]=mapped_column(Text); record_hash:Mapped[str]=mapped_column(String(64)); verified:Mapped[bool]=mapped_column(default=False); updated_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class ExceptionItem(Base):
 __tablename__='exceptions'
 id:Mapped[str]=mapped_column(String(36),primary_key=True); dataset_id:Mapped[str]=mapped_column(ForeignKey('datasets.id')); loan_id:Mapped[int]=mapped_column(ForeignKey('loans.id')); field:Mapped[str]=mapped_column(String(80)); rule:Mapped[str]=mapped_column(String(100)); message:Mapped[str]=mapped_column(Text); severity:Mapped[str]=mapped_column(String(15)); status:Mapped[str]=mapped_column(String(20),default='open'); ai_explanation:Mapped[str|None]=mapped_column(Text,nullable=True); ai_suggestion:Mapped[str|None]=mapped_column(Text,nullable=True); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
class Audit(Base):
 __tablename__='audits'
 id:Mapped[int]=mapped_column(primary_key=True); dataset_id:Mapped[str]=mapped_column(String(36)); loan_id:Mapped[int|None]=mapped_column(nullable=True); event:Mapped[str]=mapped_column(String(100)); actor:Mapped[str]=mapped_column(String(160)); detail:Mapped[str]=mapped_column(Text); created_at:Mapped[datetime]=mapped_column(DateTime,default=datetime.utcnow)
Base.metadata.create_all(engine)
app=FastAPI(title='Loan Data Verification Copilot',version='1.0.0'); app.add_middleware(CORSMiddleware,allow_origins=os.getenv('CORS_ORIGINS','http://localhost:5173,http://127.0.0.1:5173').split(','),allow_origin_regex=r'https?://(localhost|127\.0\.0\.1):\d+$',allow_methods=['*'],allow_headers=['*'])
pwd=CryptContext(schemes=['bcrypt'],deprecated='auto'); security=HTTPBearer()
def db():
 s=SessionLocal()
 try: yield s
 finally: s.close()
def current(creds:HTTPAuthorizationCredentials=Depends(security),s:Session=Depends(db)):
 try: email=jwt.decode(creds.credentials,os.getenv('JWT_SECRET','dev-secret'),algorithms=['HS256'])['sub']
 except Exception: raise HTTPException(401,'Invalid session')
 u=s.scalar(select(User).where(User.email==email))
 if not u: raise HTTPException(401,'User not found')
 return u
def audit(s,dataset,event,actor,detail,loan_id=None): s.add(Audit(dataset_id=dataset,event=event,actor=actor,detail=json.dumps(detail,default=str),loan_id=loan_id))
def canonical(data): return json.dumps(data,sort_keys=True,separators=(',',':'),default=str)
def hash_record(data): return hashlib.sha256(canonical(data).encode()).hexdigest()
def normalize(data):
 d={str(k).strip().lower().replace(' ','_'): (None if pd.isna(v) else str(v).strip()) for k,v in data.items()}
 if d.get('status'): d['status']=d['status'].title()
 for f in ['loan_amount','interest_rate','income','credit_score','loan_term']:
  if d.get(f):
   try: d[f]=float(str(d[f]).replace(',','').replace('%',''))
   except: pass
 if d.get('origination_date'):
  try: d['origination_date']=pd.to_datetime(d['origination_date'],dayfirst=True).strftime('%Y-%m-%d')
  except: pass
 return d
def rules(d, seen):
 out=[]
 def add(field,rule,msg,severity): out.append((field,rule,msg,severity))
 for f in ['loan_id','borrower_name','loan_amount','interest_rate','origination_date','status']:
  if d.get(f) in [None,'']: add(f,'required',f'{f.replace("_"," ").title()} is required','high')
 try:
  if float(d.get('loan_amount',0))<=0:add('loan_amount','positive_amount','Loan amount must be greater than zero','critical')
 except:add('loan_amount','numeric','Loan amount must be numeric','high')
 try:
  rate=float(d.get('interest_rate',0));
  if rate<=0 or rate>35:add('interest_rate','rate_range','Interest rate must be between 0 and 35%','critical')
 except:add('interest_rate','numeric','Interest rate must be numeric','high')
 try:
  score=float(d.get('credit_score',0));
  if score and not 300<=score<=850:add('credit_score','credit_range','Credit score must be between 300 and 850','high')
 except:add('credit_score','numeric','Credit score must be numeric','medium')
 if d.get('status') and d['status'] not in ['Active','Closed','Delinquent','Paid Off','Pending']:add('status','status_vocabulary','Status is outside the approved vocabulary','medium')
 if d.get('loan_id') in seen:add('loan_id','duplicate_loan_id','Duplicate loan identifier in this dataset','critical')
 return out
class Login(BaseModel): email:str; password:str
class Review(BaseModel): action:str; changes:dict[str,Any]={}; note:str=''
@app.on_event('startup')
def seed():
 s=SessionLocal()
 if not s.scalar(select(User).where(User.email=='reviewer@intain.demo')):
  s.add(User(email='reviewer@intain.demo',password_hash=pwd.hash('Demo@123'),role='reviewer')); s.commit()
 s.close()
@app.post('/auth/login')
def login(x:Login,s:Session=Depends(db)):
 u=s.scalar(select(User).where(User.email==x.email))
 if not u or not pwd.verify(x.password,u.password_hash): raise HTTPException(401,'Incorrect email or password')
 return {'access_token':jwt.encode({'sub':u.email,'exp':datetime.now(timezone.utc)+timedelta(hours=8)},os.getenv('JWT_SECRET','dev-secret'),algorithm='HS256'),'user':{'email':u.email,'role':u.role}}
@app.post('/datasets/upload')
async def upload(file:UploadFile=File(...),u:User=Depends(current),s:Session=Depends(db)):
 raw=await file.read()
 try: frame=pd.read_excel(io.BytesIO(raw)) if file.filename.lower().endswith(('xlsx','xls')) else pd.read_csv(io.BytesIO(raw))
 except Exception as e: raise HTTPException(400,f'Could not read dataset: {e}')
 if frame.empty: raise HTTPException(400,'Dataset has no rows')
 ds=Dataset(id=str(uuid.uuid4()),name=file.filename); s.add(ds); s.flush()
 for i,row in frame.iterrows():
  data={k:(None if pd.isna(v) else v) for k,v in row.to_dict().items()}; n=normalize(data); s.add(Loan(dataset_id=ds.id,source_row=i+2,data=canonical(data),normalized_data=canonical(n),record_hash=hash_record(n)))
 audit(s,ds.id,'dataset_uploaded',u.email,{'rows':len(frame),'columns':list(frame.columns)}); s.commit(); return {'id':ds.id,'rows':len(frame),'columns':list(frame.columns)}
@app.post('/datasets/demo')
def demo(u:User=Depends(current),s:Session=Depends(db)):
 rows=[['LN001','John Smith',250000,8.5,360,'2024-01-15','Active',85000,742],['LN002','Jane Doe',150000,85,360,'15/02/2024','active',None,710],['LN003','Robert Lee',-25000,7.2,180,'2024-03-01','Active',92000,810],['LN003','Robert Lee',25000,7.2,180,'2024-03-01','Active',92000,810],['LN004','Alice Brown',500000,None,240,'2024/04/10','Unknown',120000,690]]
 df=pd.DataFrame(rows,columns=['loan_id','borrower_name','loan_amount','interest_rate','loan_term','origination_date','status','income','credit_score']); b=io.BytesIO(); df.to_csv(b,index=False); b.seek(0)
 ds=Dataset(id=str(uuid.uuid4()),name='intain_demo_messy_loans.csv');s.add(ds);s.flush()
 for i,row in df.iterrows():
  data=row.to_dict();n=normalize(data);s.add(Loan(dataset_id=ds.id,source_row=i+2,data=canonical(data),normalized_data=canonical(n),record_hash=hash_record(n)))
 audit(s,ds.id,'demo_dataset_loaded',u.email,{'rows':len(df)});s.commit();return {'id':ds.id,'rows':len(df),'columns':list(df.columns)}
@app.get('/datasets')
def datasets(u:User=Depends(current),s:Session=Depends(db)): return [{'id':x.id,'name':x.name,'created_at':x.created_at,'normalized':x.normalized,'validated':x.validated} for x in s.scalars(select(Dataset).order_by(Dataset.created_at.desc()))]
@app.get('/datasets/{id}/profile')
def profile(id:str,u:User=Depends(current),s:Session=Depends(db)):
 loans=s.scalars(select(Loan).where(Loan.dataset_id==id)).all(); rows=[json.loads(x.normalized_data) for x in loans]
 if not rows:raise HTTPException(404,'Dataset not found')
 df=pd.DataFrame(rows); return {'rows':len(df),'columns':[{'name':c,'missing':int(df[c].isna().sum()+(df[c]=='').sum() if df[c].dtype=='object' else df[c].isna().sum()),'unique':int(df[c].nunique())} for c in df.columns],'schema':{c:str(df[c].dtype) for c in df.columns}}
@app.post('/datasets/{id}/normalize')
def run_normalize(id:str,u:User=Depends(current),s:Session=Depends(db)):
 for l in s.scalars(select(Loan).where(Loan.dataset_id==id)): l.normalized_data=canonical(normalize(json.loads(l.data)));l.record_hash=hash_record(json.loads(l.normalized_data))
 ds=s.get(Dataset,id); ds.normalized=True;audit(s,id,'dataset_normalized',u.email,{});s.commit();return {'ok':True}
@app.post('/datasets/{id}/validate')
def validate(id:str,u:User=Depends(current),s:Session=Depends(db)):
 s.query(ExceptionItem).filter(ExceptionItem.dataset_id==id).delete(); seen=set(); count=0
 for l in s.scalars(select(Loan).where(Loan.dataset_id==id)):
  d=json.loads(l.normalized_data)
  for field,rule,msg,sev in rules(d,seen):s.add(ExceptionItem(id=str(uuid.uuid4()),dataset_id=id,loan_id=l.id,field=field,rule=rule,message=msg,severity=sev));count+=1
  seen.add(d.get('loan_id'))
 ds=s.get(Dataset,id);ds.validated=True;audit(s,id,'validation_completed',u.email,{'exceptions':count});s.commit();return {'exceptions':count}
@app.get('/datasets/{id}/overview')
def overview(id:str,u:User=Depends(current),s:Session=Depends(db)):
 loans=s.scalars(select(Loan).where(Loan.dataset_id==id)).all(); issues=s.scalars(select(ExceptionItem).where(ExceptionItem.dataset_id==id)).all(); open_=[x for x in issues if x.status=='open']; total=len(loans); score=round(max(0,100-(sum({'critical':12,'high':6,'medium':3,'low':1}[x.severity] for x in open_)/max(total,1))),1)
 return {'records':total,'verified':sum(x.verified for x in loans),'quality_score':score,'exceptions':{z:sum(x.severity==z and x.status=='open' for x in issues) for z in ['critical','high','medium','low']},'resolved':sum(x.status=='resolved' for x in issues)}
@app.get('/datasets/{id}/exceptions')
def exceptions(id:str,severity:str|None=None,status:str='open',q:str|None=None,u:User=Depends(current),s:Session=Depends(db)):
 xs=s.scalars(select(ExceptionItem).where(ExceptionItem.dataset_id==id)).all(); out=[]
 for x in xs:
  l=s.get(Loan,x.loan_id);d=json.loads(l.normalized_data)
  if (severity and x.severity!=severity) or (status!='all' and x.status!=status) or (q and q.lower() not in canonical(d).lower()):continue
  out.append({'id':x.id,'loan_id':x.loan_id,'record':d,'field':x.field,'rule':x.rule,'message':x.message,'severity':x.severity,'status':x.status,'ai_explanation':x.ai_explanation,'ai_suggestion':x.ai_suggestion})
 return out
@app.post('/exceptions/{id}/ai')
def ai(id:str,u:User=Depends(current),s:Session=Depends(db)):
 x=s.get(ExceptionItem,id)
 if not x:raise HTTPException(404,'Exception not found')
 d=json.loads(s.get(Loan,x.loan_id).normalized_data)
 prompt=f'''You assist a loan-data reviewer. A deterministic validation rule already found this issue; do not validate, infer missing financial values, or direct automatic changes. Return two short labeled paragraphs: Explanation and Suggested review. Issue: {x.message}. Rule: {x.rule}. Field: {x.field}. Severity: {x.severity}. Relevant record: {json.dumps({x.field:d.get(x.field),'loan_id':d.get('loan_id'),'status':d.get('status')})}.'''
 if os.getenv('OPENAI_API_KEY'):
  try:
   from openai import OpenAI
   response=OpenAI().responses.create(model=os.getenv('OPENAI_MODEL','gpt-5'),input=prompt)
   output=response.output_text
   parts=output.split('Suggested review:',1); x.ai_explanation=parts[0].replace('Explanation:','').strip(); x.ai_suggestion=(parts[1].strip() if len(parts)>1 else output)
  except Exception as e: raise HTTPException(502,f'AI assistance unavailable: {e}')
 else:
  x.ai_explanation=f"The deterministic rule '{x.rule}' flagged {x.field}: {x.message}. This can affect downstream servicing, pricing, and investor reporting."; x.ai_suggestion=f"Review the source document for {x.field}. Correct only if evidence supports it; otherwise reject with a reviewer note. No data has been changed."
 audit(s,x.dataset_id,'ai_assistance_generated',u.email,{'exception':id,'provider':'openai' if os.getenv('OPENAI_API_KEY') else 'local-demo'},x.loan_id);s.commit();return {'explanation':x.ai_explanation,'suggestion':x.ai_suggestion}
@app.post('/exceptions/{id}/review')
def review(id:str,x:Review,u:User=Depends(current),s:Session=Depends(db)):
 ex=s.get(ExceptionItem,id)
 if not ex:raise HTTPException(404,'Exception not found')
 loan=s.get(Loan,ex.loan_id); before=json.loads(loan.normalized_data)
 if x.action=='approve':
  after={**before,**x.changes};loan.normalized_data=canonical(normalize(after));loan.record_hash=hash_record(json.loads(loan.normalized_data));ex.status='resolved'
 elif x.action=='reject': ex.status='rejected'
 else:raise HTTPException(400,'Action must be approve or reject')
 remaining=s.scalar(select(func.count()).select_from(ExceptionItem).where(ExceptionItem.loan_id==loan.id,ExceptionItem.status=='open'))
 if not remaining:loan.verified=True
 audit(s,ex.dataset_id,'exception_'+x.action,u.email,{'before':before,'after':json.loads(loan.normalized_data),'note':x.note,'hash':loan.record_hash},loan.id);s.commit();return {'ok':True,'hash':loan.record_hash}
@app.get('/datasets/{id}/export/{kind}')
def export(id:str,kind:str,u:User=Depends(current),s:Session=Depends(db)):
 if kind=='verified': rows=[{**json.loads(x.normalized_data),'record_hash':x.record_hash} for x in s.scalars(select(Loan).where(Loan.dataset_id==id,Loan.verified==True))]
 elif kind=='exceptions':rows=[{'id':x.id,'loan_id':x.loan_id,'field':x.field,'severity':x.severity,'status':x.status,'message':x.message} for x in s.scalars(select(ExceptionItem).where(ExceptionItem.dataset_id==id))]
 else: rows=[{'event':x.event,'actor':x.actor,'detail':x.detail,'created_at':x.created_at} for x in s.scalars(select(Audit).where(Audit.dataset_id==id))]
 return StreamingResponse(io.StringIO(pd.DataFrame(rows).to_csv(index=False)),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename={kind}_{id}.csv'})
