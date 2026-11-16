"""Generate a <=10-page report from saved text and measured experiment results."""
from pathlib import Path
import json,html,re
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,Image,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'report';styles=getSampleStyleSheet()
styles['BodyText'].fontSize=10;styles['BodyText'].leading=14
story=[]
text=re.sub(r'(?m)^(#{1,2} .+)$', r'\1\n', (out/'report.md').read_text())
for page,chunk in enumerate(text.split('\n---\n')):
 if page:story.append(PageBreak())
 for para in chunk.strip().split('\n\n'):
  if para.startswith('# '):style='Title';para=para[2:]
  elif para.startswith('## '):style='Heading1';para=para[3:]
  else:style='BodyText'
  story.append(Paragraph(html.escape(para).replace('\n','<br/>'),styles[style]));story.append(Spacer(1,7))
 if page==3:
  story.append(Image(str(ROOT/'results/attention_response/comparison.png'),width=450,height=200))
 if page==4:
  pass
# Whole-body measured evidence is a dedicated final results page.
story.append(PageBreak());story.append(Paragraph('Whole-body measured results',styles['Heading1']))
r=json.loads((ROOT/'results/full_body_balance/summary.json').read_text())
table=[['Case','Pass / trials','Max tilt (deg)','Min base z (mm)']]
for case,trials in r['trials'].items():table.append([case,f"{sum(x['success'] for x in trials)}/{len(trials)}",f"{max(x['peak_tilt_deg'] for x in trials):.2f}",f"{1000*min(x['min_height_m'] for x in trials):.1f}"])
t=Table(table);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),.5,colors.grey),('BOTTOMPADDING',(0,0),(-1,-1),8)]));story.append(t)
for case,trials in r['trials'].items():
 vals=[x['gaze_rms_after_3s_deg'] for x in trials if x['gaze_rms_after_3s_deg'] is not None]
 text=f"{case}: non-foot contact count {sum(x['nonfoot_contact_samples'] for x in trials)}; joint-limit violation steps {sum(x['joint_violation_steps'] for x in trials)}; peak actuator force {max(x['peak_actuator_force_nm'] for x in trials):.3f} Nm. "
 if vals:text+=f"Mean gaze RMS after 3 s: {sum(vals)/len(vals):.3f} degrees."
 else:text+='No post-3 s gaze result: all trials terminated earlier.'
 story.append(Paragraph(text,styles['BodyText']))
story.append(Spacer(1,15));story.append(Image(str(ROOT/'results/full_body_balance/comparison.png'),width=450,height=281))
def footer(canvas,doc):canvas.setFont('Helvetica',9);canvas.drawString(42,25,f'ELEC5621 | Microduck gaze and balance | {doc.page}')
file=out/'ELEC5621_Report.pdf';SimpleDocTemplate(str(file),rightMargin=42,leftMargin=42,topMargin=36,bottomMargin=40).build(story,onFirstPage=footer,onLaterPages=footer)
n=len(PdfReader(file).pages);assert n<=10,n
print(f'{file}: {n} pages')
