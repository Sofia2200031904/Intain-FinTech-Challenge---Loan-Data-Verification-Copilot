"""Create a narration-ready MP4 storyboard for the Loan Verification Copilot."""
from pathlib import Path
import sys
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.demo_video_deps'))
import imageio_ffmpeg

W,H,FPS=1280,720,24
OUT=ROOT/'demo_video'/'loan_verification_copilot_demo.mp4'
BG='#f5f7fb';NAV='#102a56';BLUE='#155eef';TEXT='#13233f';MUTED='#667085';WHITE='#ffffff';LINE='#dfe7f1'

def font(size,bold=False):
 paths=[Path('C:/Windows/Fonts/arialbd.ttf' if bold else 'C:/Windows/Fonts/arial.ttf'),Path('C:/Windows/Fonts/segoeui.ttf')]
 for p in paths:
  if p.exists():return ImageFont.truetype(str(p),size)
 return ImageFont.load_default()
F={s:font(s) for s in [15,17,18,20,22,28,36,52]};FB={s:font(s,True) for s in [15,17,18,20,22,28,36,52]}

def rounded(d,box,fill,outline=None,r=14,w=1):d.rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=w)
def text(d,xy,s,size=18,fill=TEXT,bold=False,anchor=None):d.text(xy,s,font=(FB if bold else F)[size],fill=fill,anchor=anchor)
def base(title,subtitle,step):
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 d.rectangle((0,0,W,66),fill=NAV);text(d,(28,33),'INTAIN',22,WHITE,True,'lm');text(d,(180,33),'Loan Data Verification Copilot',18,'#dbeafe',False,'lm')
 rounded(d,(1090,18,1250,48),'#1f4a86',r=18);text(d,(1170,33),step,15,WHITE,True,'mm')
 text(d,(52,112),title,36,TEXT,True);text(d,(52,158),subtitle,18,MUTED)
 return im,d
def panel(d,box,title):rounded(d,box,WHITE,LINE);text(d,(box[0]+22,box[1]+24),title,22,TEXT,True)
def badge(d,x,y,s,color):rounded(d,(x,y,x+105,y+30),color,r=15);text(d,(x+52,y+15),s,15,WHITE,True,'mm')
def footer(d,note):text(d,(52,690),note,15,MUTED)

def scene_title():
 im=Image.new('RGB',(W,H),'#5a69d9');d=ImageDraw.Draw(im)
 d.ellipse((-170,430,320,920),fill=WHITE);d.ellipse((1020,-260,1500,220),fill=WHITE)
 rounded(d,(175,105,1105,615),WHITE,r=22);text(d,(640,180),'VERIFIED DATA',28,BLUE,True,'mm');text(d,(640,250),'Loan Data Verification Copilot',52,TEXT,True,'mm')
 text(d,(640,312),'Turn messy loan tapes into verified, explainable and auditable records.',22,MUTED,False,'mm')
 rounded(d,(335,370,945,430),BLUE,r=12);text(d,(640,400),'INGEST → PROFILE → VALIDATE → REVIEW → VERIFY',18,WHITE,True,'mm')
 text(d,(640,500),'AI explains  •  deterministic rules decide  •  humans approve',18,'#344054',False,'mm')
 text(d,(640,570),'Intain FinTech Challenge 2026 · Full Stack Track',15,MUTED,True,'mm');return im
def scene_upload():
 im,d=base('1. Ingest messy loan data','Admin uploads CSV, XLSX or XLS — up to 50,000 records.','ADMIN')
 panel(d,(50,200,355,650),'Dataset controls');rounded(d,(75,260,330,315),BLUE,r=8);text(d,(202,287),'↑  Upload CSV / Excel',18,WHITE,True,'mm');rounded(d,(75,330,330,385),WHITE,LINE,r=8);text(d,(202,357),'Load Demo Dataset',18,TEXT,True,'mm')
 panel(d,(390,200,1230,650),'Upload result');text(d,(425,265),'messy_loan_tape.xlsx',28,TEXT,True);badge(d,1040,245,'UPLOADED','#15803d');text(d,(425,325),'5 loan records detected',22,TEXT);text(d,(425,370),'9 source fields preserved',22,TEXT);text(d,(425,415),'Original spreadsheet row numbers retained',22,TEXT);text(d,(425,485),'Supported safeguards',18,MUTED,True)
 for i,s in enumerate(['File type validation','10 MB size limit','Empty/corrupt file detection']):text(d,(450,525+i*34),'OK  '+s,18,'#15803d',True)
 footer(d,'Every record keeps its raw source evidence before normalization.');return im
def scene_profile():
 im,d=base('2. Profile and normalize','Understand the incoming tape before making any decisions.','ADMIN');panel(d,(50,205,1230,650),'Ingest & profile')
 cols=[('loan_id','string','0','4'),('borrower_name','string','0','4'),('loan_amount','number','0','4'),('interest_rate','number','1','4'),('origination_date','date','0','5'),('status','string','0','3'),('credit_score','number','0','5')]
 text(d,(90,265),'FIELD',15,MUTED,True);text(d,(510,265),'TYPE',15,MUTED,True);text(d,(760,265),'MISSING',15,MUTED,True);text(d,(990,265),'UNIQUE',15,MUTED,True)
 for i,(a,t,b,c) in enumerate(cols):y=305+i*44;d.line((85,y+27,1185,y+27),fill=LINE);text(d,(90,y),a,18);text(d,(510,y),t,18,BLUE);text(d,(790,y),b,18,('#b42318' if b!='0' else TEXT));text(d,(1015,y),c,18)
 footer(d,'Normalization standardizes field names, numbers, percentages, statuses and dates.');return im
def scene_validate():
 im,d=base('3. Deterministic validation','Transparent rules detect and prioritize data-quality exceptions.','ADMIN')
 cards=[('DATA QUALITY','55%','#b45309'),('RECORDS','5',BLUE),('OPEN EXCEPTIONS','7','#b42318'),('VERIFIED','1 / 5','#15803d')]
 for i,(a,b,c) in enumerate(cards):x=50+i*295;rounded(d,(x,205,x+270,315),WHITE,LINE);text(d,(x+20,230),a,15,MUTED,True);text(d,(x+20,270),b,36,c,True)
 panel(d,(50,345,1230,655),'Prioritized reviewer queue')
 rows=[('LN002','Interest rate must be between 0 and 35%','CRITICAL','#b42318'),('LN003','Loan amount must be greater than zero','CRITICAL','#b42318'),('LN003','Duplicate loan identifier in this dataset','CRITICAL','#b42318'),('LN004','Interest rate is required','HIGH','#c2410c'),('LN004','Status is outside approved vocabulary','MEDIUM','#a16207')]
 for i,(loan,msg,sev,c) in enumerate(rows):y=395+i*48;rounded(d,(75,y-8,1205,y+33),'#fbfcfe',LINE,r=6);text(d,(95,y),loan,18,TEXT,True);text(d,(220,y),msg,18);text(d,(1115,y+9),sev,15,c,True,'mm')
 footer(d,'AI is not used to decide validity. Each finding records rule, field, value and severity.');return im
def scene_review():
 im,d=base('4. Assigned human review','Only the assigned reviewer can claim and decide an exception.','REVIEWER');panel(d,(50,205,700,655),'Exception evidence');badge(d,555,228,'CRITICAL','#b42318');text(d,(82,275),'LN002 · Interest rate',28,TEXT,True);text(d,(82,330),'Rule: rate_range',18);text(d,(82,367),'Actual value: 85',18);text(d,(82,404),'Expected: greater than 0 and at most 35%',18);rounded(d,(82,470,350,525),BLUE,r=8);text(d,(216,497),'Generate AI assistance',18,WHITE,True,'mm')
 panel(d,(735,205,1230,655),'Access controls');items=['Dataset assignment checked','Claim is atomic','Claim ownership enforced','Viewer remains read-only','Backend returns 403 / 409'];
 for i,s in enumerate(items):text(d,(775,285+i*58),'OK  '+s,20,'#15803d',i<3)
 footer(d,'A second reviewer cannot take over an exception that is already under review.');return im
def scene_claim():
 im,d=base('4. Claim the exception','The reviewer performs an explicit, atomic claim before making a decision.','REVIEWER')
 panel(d,(110,205,1170,640),'Reviewer queue · LN002')
 badge(d,985,230,'CRITICAL','#b42318');text(d,(150,285),'Interest rate must be between 0 and 35%',28,TEXT,True);text(d,(150,335),'Status',18,MUTED,True);badge(d,260,325,'OPEN','#b45309');text(d,(150,405),'Assigned reviewer',18,MUTED,True);text(d,(350,405),'reviewer@intain.demo',20,TEXT,True)
 rounded(d,(790,500,1110,565),BLUE,r=9);text(d,(950,532),'Claim Exception',22,WHITE,True,'mm');text(d,(150,535),'Action:',18,MUTED,True);text(d,(245,535),'OPEN  →  UNDER REVIEW',22,BLUE,True)
 footer(d,'The backend performs the status transition only when the exception is still open.');return im
def scene_claimed():
 im,d=base('5. Claim confirmed','The claimed exception now displays its reviewer identity and review status.','REVIEWER')
 panel(d,(110,205,1170,640),'Exception evidence · LN002');badge(d,945,235,'UNDER REVIEW',BLUE);text(d,(150,290),'Interest rate',28,TEXT,True)
 rows=[('Rule','rate_range'),('Actual value','85'),('Reviewer','reviewer@intain.demo'),('Claimed at','10:31:02'),('Record status','In Review')]
 for i,(a,b) in enumerate(rows):y=350+i*48;text(d,(150,y),a,18,MUTED,True);text(d,(410,y),b,20,TEXT,b in ['reviewer@intain.demo','In Review'])
 rounded(d,(810,525,1110,580),'#eef6ff',r=8);text(d,(960,552),'CLAIM OWNED',18,BLUE,True,'mm');footer(d,'A competing reviewer receives 409 Conflict and cannot decide this exception.');return im
def scene_ai():
 im,d=base('6. AI-assisted explanation','Reviewer guidance is advisory and cannot change loan values.','REVIEWER');panel(d,(80,215,1200,640),'AI ASSISTED — HUMAN REVIEW REQUIRED')
 text(d,(120,280),'Explanation',22,BLUE,True);text(d,(120,325),"The deterministic 'rate_range' rule flagged an interest rate of 85%.",22);text(d,(120,365),'This may affect servicing, pricing and downstream reporting.',22)
 text(d,(120,440),'Suggested review',22,BLUE,True);text(d,(120,485),'Check the source document for the contracted interest rate.',22);text(d,(120,525),'Correct it only when evidence supports the change; otherwise reject with a reason.',22)
 rounded(d,(930,560,1155,610),'#eef6ff',r=8);text(d,(1042,585),'NO AUTO-CHANGE',15,BLUE,True,'mm');footer(d,'The LLM explains; deterministic revalidation controls the final status.');return im
def scene_correct():
 im,d=base('7. Correct and revalidate','Every reviewer decision requires a reason and produces traceable evidence.','REVIEWER');panel(d,(210,195,1070,655),'Correction & revalidation')
 fields=[('Loan ID','LN002'),('Field','interest_rate'),('Current value','85'),('Corrected value','8.5'),('Reason','Confirmed from signed source document')]
 for i,(a,b) in enumerate(fields):y=255+i*62;text(d,(260,y),a,18,MUTED,True);rounded(d,(500,y-10,1015,y+35),'#fbfcfe',LINE,r=6);text(d,(520,y+10),b,18,TEXT,False,'lm')
 rounded(d,(700,575,1015,625),BLUE,r=8);text(d,(857,600),'Save & Revalidate',18,WHITE,True,'mm');footer(d,'The corrected record is normalized and all applicable deterministic rules run again.');return im
def scene_result():
 im,d=base('8. Revalidation result','The correction passes its deterministic rule and completes the record lifecycle.','REVIEWER')
 panel(d,(120,205,1160,635),'Correction result · LN002');text(d,(175,280),'interest_rate',18,MUTED,True);text(d,(430,280),'85',28,'#b42318',True);text(d,(520,280),'→',28,MUTED,True);text(d,(590,280),'8.5',28,'#15803d',True)
 results=[('VALIDATION','PASSED','#15803d'),('EXCEPTION','RESOLVED',BLUE),('RECORD','VERIFIED','#15803d')]
 for i,(a,b,c) in enumerate(results):y=365+i*72;text(d,(175,y),a,18,MUTED,True);rounded(d,(430,y-14,750,y+35),c,r=22);text(d,(590,y+10),b,18,WHITE,True,'mm')
 rounded(d,(820,365,1085,515),'#ecfdf3','#86efac',r=14);text(d,(952,405),'0',52,'#15803d',True,'mm');text(d,(952,470),'open exceptions',18,'#15803d',True,'mm');footer(d,'A record is Verified only when no open or under-review exceptions remain.');return im
def scene_audit():
 im,d=base('9. Hash, history and audit trail','The system preserves who changed what, why, when and with what result.','VIEWER');panel(d,(50,205,1230,650),'Record history · LN002')
 text(d,(85,250),'Previous hash',15,MUTED,True);rounded(d,(85,280,520,330),'#fff1f2',r=7);text(d,(105,305),'a83f21c0...91c',20,'#9f1239',True,'lm');text(d,(590,305),'Correction + revalidation',18,MUTED,True,'mm');text(d,(590,337),'↓',28,BLUE,True,'mm');text(d,(730,250),'New hash',15,MUTED,True);rounded(d,(730,280,1190,330),'#ecfdf3',r=7);text(d,(750,305),'72bd9e41...4ef',20,'#166534',True,'lm')
 headers=['TIMESTAMP','ACTOR','ACTION','RESULT'];xs=[85,330,570,1030]
 for x,h in zip(xs,headers):text(d,(x,395),h,15,MUTED,True)
 rows=[('10:31:02','reviewer@intain.demo','exception_under_review','recorded'),('10:32:18','reviewer@intain.demo','loan_record_corrected','passed'),('10:32:18','reviewer@intain.demo','record_revalidated','passed')]
 for i,row in enumerate(rows):y=440+i*55;d.line((80,y+32,1190,y+32),fill=LINE);[text(d,(x,y),v,17,('#15803d' if j==3 and v=='passed' else TEXT),j==3) for j,(x,v) in enumerate(zip(xs,row))]
 footer(d,'Raw → normalized → verified provenance remains available to permitted users.');return im
def scene_roles():
 im,d=base('10. Role-based workflow','Each persona sees only the controls needed for their responsibility.','RBAC')
 data=[('ADMIN','#155eef',['Upload and validate','Manage users and rules','Assign reviewers']),('REVIEWER','#7c3aed',['Assigned datasets only','Claim and decide','Correct and revalidate']),('VIEWER','#15803d',['Read-only visibility','Inspect history','Download reports'])]
 for i,(name,c,items) in enumerate(data):x=55+i*410;rounded(d,(x,220,x+370,625),WHITE,LINE);rounded(d,(x,x*0+220,x+370,285),c,r=14);text(d,(x+185,252),name,22,WHITE,True,'mm');
  # intentionally drawn below outside compact header
 for i,(name,c,items) in enumerate(data):
  x=55+i*410
  for j,s in enumerate(items):text(d,(x+38,345+j*62),'OK  '+s,20,TEXT,j==0)
 footer(d,'Frontend visibility supports usability; FastAPI authorization remains the security boundary.');return im
def scene_export():
 im,d=base('11. Export verified evidence','Download operational outputs directly from the completed dataset.','ADMIN')
 panel(d,(70,205,1210,640),'Dataset reports · messy_loan_tape.xlsx')
 exports=[('Export Verified Records','verified.csv','1 verified record','#15803d'),('Export Exceptions','exceptions.csv','7 findings with lifecycle status',BLUE),('Export Audit','audit.csv','complete actor and timestamp history','#7c3aed')]
 for i,(label,file,detail,c) in enumerate(exports):y=270+i*105;rounded(d,(110,y,1170,y+80),'#fbfcfe',LINE,r=9);text(d,(145,y+25),label,20,TEXT,True);text(d,(145,y+54),detail,15,MUTED);rounded(d,(850,y+17,1130,y+63),c,r=7);text(d,(990,y+40),'Download '+file,15,WHITE,True,'mm')
 rounded(d,(800,580,1170,620),'#ecfdf3',r=7);text(d,(985,600),'verified.csv downloaded',15,'#15803d',True,'mm');footer(d,'Exports preserve verified hashes, exception status, and audit evidence for downstream use.');return im
def scene_finish():
 im=Image.new('RGB',(W,H),NAV);d=ImageDraw.Draw(im);text(d,(640,145),'VERIFIED DATA',28,'#60a5fa',True,'mm');text(d,(640,225),'From messy data to trusted records',52,WHITE,True,'mm');text(d,(640,300),'Upload → Profile → Validate → Review → Verify → Audit → Export',22,'#dbeafe',False,'mm')
 for i,(a,b) in enumerate([('Deterministic controls','Rules decide'),('Human accountability','Reviewers approve'),('Complete traceability','Hashes and audit events')]):x=125+i*350;rounded(d,(x,375,x+325,505),'#1f4a86',r=15);text(d,(x+162,415),a,18,WHITE,True,'mm');text(d,(x+162,460),b,18,'#bfdbfe',False,'mm')
 text(d,(640,600),'Loan Data Verification Copilot · Full Stack Track',18,'#93c5fd',True,'mm');return im

SCENES=[scene_title,scene_upload,scene_profile,scene_validate,scene_claim,scene_claimed,scene_ai,scene_correct,scene_result,scene_audit,scene_roles,scene_export,scene_finish]
DURATIONS=[5,7,8,7,7,7,7,7,8,8,6,7,6]
def frames():
 for make,seconds in zip(SCENES,DURATIONS):
  frame=make()
  for n in range(seconds*FPS):
   shown=frame.copy();d=ImageDraw.Draw(shown);progress=n/(seconds*FPS-1);d.rectangle((0,H-7,int(W*progress),H),fill='#60a5fa')
   yield shown.tobytes()

OUT.parent.mkdir(exist_ok=True)
writer=imageio_ffmpeg.write_frames(str(OUT),(W,H),fps=FPS,codec='libx264',quality=7,pix_fmt_in='rgb24',output_params=['-pix_fmt','yuv420p','-movflags','+faststart'])
writer.send(None)
for frame in frames():writer.send(frame)
writer.close()
print(OUT)
