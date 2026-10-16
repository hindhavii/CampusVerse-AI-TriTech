"""🏰 CampusVerse AI | DSU Harohalli Smart Campus Digital Twin.

Hackathon PROTOTYPE. All digital sensor measurements, model geometry, user roles,
facility-floor assignments and crowd scenarios are illustrative/simulated.
Do NOT use this app for actual evacuation or emergency decision-making.
"""
from __future__ import annotations
import hmac
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from campusverse import data as db
from campusverse.energy_demo import load_energy_readings, classify_interval

st.set_page_config(page_title='🏰 CampusVerse AI | DSU Digital Twin',page_icon='🏰',layout='wide',initial_sidebar_state='collapsed')
db.initialize()
BASE=Path(__file__).resolve().parent
ASSETS=BASE/'assets'

st.markdown('''<style>
#MainMenu,footer {visibility:hidden}
.block-container {padding-top:1.05rem;max-width:1480px;padding-bottom:3rem}
h1 {font-weight:800;letter-spacing:-.045em}
[data-testid="stMetric"] {background:#f1f5fb;border:1px solid #e1e7ee;border-radius:15px;padding:12px}
[data-testid="stAppViewContainer"] {background:linear-gradient(180deg,#f6f9fc 0%,#ffffff 60%)}
[data-testid="stButton"] button {border-radius:12px;font-weight:650}
.pill {display:inline-block;background:#e9efff;border-radius:20px;padding:5px 12px;font-size:12px;color:#213e68;font-weight:750}
.hero {background:linear-gradient(115deg,#132c49,#254b69);color:#fff;padding:20px 24px;border-radius:19px;margin-bottom:14px}
.hero h1 {font-size:2.12rem;color:#fff;margin:0}.hero p {color:#d8e7f5;margin:5px 0 0}
[data-testid="stPlotlyChart"] {border-radius:18px;overflow:hidden}
.small-note {font-size:.83rem;color:#65748a}
</style>''',unsafe_allow_html=True)

for key,default in [('building',None),('mode',None),('chosen_facility','Classrooms'),('login_role','Administrator'),('picker_nonce',0)]:
    if key not in st.session_state: st.session_state[key]=default


def secrets_get(name):
    try:
        return st.secrets.get(name,'')
    except (FileNotFoundError,KeyError):
        return ''


def role():
    return st.session_state.get('authenticated_role','')


def can_control():
    return role() in ('Administrator','Maintenance Worker')


def can_crowd():
    return role() in ('Administrator','Security Staff')


def login(required):
    if (required=='control' and can_control()) or (required=='crowd' and can_crowd()):
        return True
    st.warning('🔐 This area requires authorized staff access. Campus Connect stays public.')
    roles=['Administrator','Maintenance Worker'] if required=='control' else ['Administrator','Security Staff']
    with st.form('login_'+required):
        who=st.selectbox('Staff role',roles)
        entered=st.text_input('Password',type='password')
        attempt=st.form_submit_button('🔓 Sign in',use_container_width=True)
    if attempt:
        key={'Administrator':'ADMIN_PASSWORD','Maintenance Worker':'WORKER_PASSWORD','Security Staff':'SECURITY_PASSWORD'}[who]
        saved=secrets_get(key)
        if not saved:
            st.error('Staff access is not configured. Run `py configure_demo.py` first, then restart the application.')
        elif hmac.compare_digest(entered,saved):
            st.session_state.authenticated_role=who
            st.success('Signed in as '+who)
            st.rerun()
        else:
            st.error('Incorrect password.')
    with st.expander('First-time setup'):
        st.code('py configure_demo.py',language='powershell')
        st.caption('Run once in the VS Code terminal while Streamlit is stopped. It creates local, uncommitted secrets and prints the demo credentials.')
    return False


def navigate(building=None,mode=None):
    st.session_state.building=building
    st.session_state.mode=mode
    if building is None:
        st.session_state.picker_nonce+=1  # New 3D component instance when returning home.
    st.rerun()


def title(subtitle):
    st.markdown('<div class="hero"><h1>🏰 CampusVerse AI</h1><p>DSU Smart Campus Digital Twin &nbsp;•&nbsp; '+subtitle+'</p></div>',unsafe_allow_html=True)


def disclaimer():
    st.caption('🧪 HACKATHON SIMULATION — occupancy, parking, electricity, waste levels, maps, locations and staff alerts are demonstration data, not live DSU readings. Spatial geometry and routes are not surveyed.')


def level_label(n):
    return 'Ground Floor' if n==0 else f'Floor {n}' if n is not None and n>=0 else 'Block facility — exact floor unverified'


def classification(r):
    p=100*r['occupied']/max(1,r['capacity'])
    return ('Full' if p>=100 else 'High' if p>=85 else 'Moderate' if p>=60 else 'Low', p)


def metric_cards(r,show_free=True):
    label,p=classification(r)
    a,b,c=st.columns(3)
    a.metric('Current '+('vehicles' if r.get('category')=='parking' else 'people'),str(r['occupied']))
    b.metric('Capacity (simulated)',str(r['capacity']))
    c.metric('Crowd / occupancy',f'{p:.0f}% • {label}')
    if show_free: st.caption(f'Estimated spaces/seats available: {max(0,r["capacity"]-r["occupied"])}')
    st.progress(min(1,p/100))


def show_reference(building):
    files={'SOE':('soe_front.jpg','Actual SOE exterior reference photograph from the virtual tour.'),
           'CDSIMER':('courtyard.jpg','Actual 360° courtyard view: SOE on the left and CDSIMER on the right.')}
    if building in files:
        f,description=files[building]
        if (ASSETS/f).exists():
            with st.expander('📸 View real campus visual reference'):
                st.image(str(ASSETS/f),caption=description,use_container_width=True)
    else:
        st.caption('This building’s exact visual placement has not yet been verified from a dedicated site plan.')


def home():
    # Only the original Plotly exterior viewer is replaced.
    # The selected place flows into the ORIGINAL building_hub and its three systems.
    from streamlit.components.v1 import declare_component
    pick_3d = declare_component('campus_picker',path=str(BASE/'campus_picker'))
    picked=pick_3d(key=f'castle_campus_{st.session_state.picker_nonce}',default=None)
    if picked in db.BUILDINGS:
        st.session_state.building=picked
        st.session_state.mode=None
        st.rerun()
    st.caption('🧪 DSU-inspired 3D concept • Simulated geometry • Rotate, zoom, or click an actual 3D building to open the original modules.')
    with st.expander('If your browser cannot use the 3D model, choose a campus location here'):
        for col,name in zip(st.columns(3),db.BUILDINGS[:3]):
            if col.button(name,key='fallback_'+name,use_container_width=True):navigate(name,None)
        for i,name in enumerate(db.BUILDINGS[3:]):
            if st.button('Open '+name,key='fallback_'+name,use_container_width=True):navigate(name,None)
    disclaimer()


def building_hub(building):
    title(building+' • Choose your experience')
    cols=st.columns([1,3,1])
    with cols[0]:
        if st.button('← 3D Campus',use_container_width=True):navigate(None,None)
    st.subheader(f'🏛️ {building}')
    st.caption('Your selection stays linked to this building through the next screens.')
    show_reference(building)
    x,y,z=st.columns(3)
    with x:
        st.info('🎓 **CAMPUS CONNECT**\n\nOccupancy, cafeteria, library, parking, classrooms and reporting issues. Public access.')
        if st.button('Open Campus Connect →',use_container_width=True,type='primary'):navigate(building,'connect')
    with y:
        st.info('🛠️ **CAMPUS CONTROL**\n\nWaste, electricity, maintenance tickets, staff tasks and deadlines. Restricted.')
        if st.button('Open Campus Control 🔐',use_container_width=True):navigate(building,'control')
    with z:
        st.info('🚨 **CROWD COMMAND**\n\nSimulated sectors, entrance/turnstile congestion and staff response. Restricted.')
        if st.button('Open Crowd Command 🔐',use_container_width=True):navigate(building,'crowd')
    st.caption('All three functions exist for the selected site; some functions depend on that site’s known or planned facilities.')
    disclaimer()


def connect_view(building):
    title(building+' / Campus Connect · Public')
    if st.button('← Back to building options'):navigate(building,None)
    st.subheader('🎓 Campus Connect')
    if building in db.ACADEMIC:
        choices=['Classrooms','Cafeteria','Parking','Library','Common room','Waiting areas','Lecture halls','Report an Issue','Track a Report']
    elif building=='Hospital':
        choices=['Waiting areas','Parking','Report an Issue','Track a Report']
    elif building=='Parking':
        choices=['Parking','Report an Issue','Track a Report']
    else:
        choices=['Event occupancy','Parking','Report an Issue','Track a Report']
    selected=st.radio('Choose a facility or service',choices,horizontal=True,key='connect_service_'+building)
    if selected=='Report an Issue':
        st.markdown('#### 📣 Report a broken or faulty facility')
        with st.form('report_'+building,clear_on_submit=True):
            loc=st.text_input('Floor / room / location',placeholder='e.g., Ground floor, Classroom 101')
            typ=st.selectbox('Problem category',['Projector / AV','Electrical / AC / Fan','Leaking Tap / Plumbing','Cleaning / Hygiene','Furniture / Fixtures','Other'])
            message=st.text_area('Describe the problem',placeholder='Tell maintenance what needs fixing')
            send=st.form_submit_button('Submit report',type='primary',use_container_width=True)
        if send:
            if not loc.strip() or not message.strip():st.error('Please include both the location and a description.')
            else:
                issue_id=db.add_ticket('Student / Faculty',building,loc.strip(),typ,message.strip())
                st.success(f'Report #MNT-{issue_id:04d} sent to Campus Control → Maintenance. Save this reference number.')
                st.caption('Staff will assess priority, assign a worker and a deadline; this example app does not send phone/SMS alerts.')
        disclaimer();return
    if selected=='Track a Report':
        num=st.number_input('Enter your report number',min_value=1,step=1,value=1)
        row=db.query('SELECT id,building,location,category,priority,deadline,status FROM tickets WHERE id=?',(int(num),))
        if not row: st.info('No report with that number yet.')
        elif row[0]['building']!=building:st.info('No report with that number for the selected building.')
        else:
            r=row[0];st.success(f'#{r["id"]:04d}: {r["status"]}')
            st.write({'Location':r['location'],'Issue':r['category'],'Priority':r['priority'],'Target deadline':r['deadline'] or 'Awaiting assignment'})
        disclaimer();return
    if selected=='Parking':
        st.markdown('#### 🚗 Smart Parking Analysis — Campus parking zones')
        allzones=db.parking()
        total=sum(z['capacity'] for z in allzones);used=sum(z['occupied'] for z in allzones)
        c1,c2,c3=st.columns(3)
        c1.metric('Total parking slots',total);c2.metric('Occupied',used);c3.metric('Free',total-used)
        for z in allzones:
            free=z['capacity']-z['occupied'];p=z['occupied']/z['capacity']
            with st.container(border=True):
                st.markdown(f'**{z["label"]}** — **{free} free** / {z["capacity"]} total')
                st.progress(p)
                st.caption('🔴 Full / nearly full' if p>=.9 else '🟡 Limited spaces' if p>=.7 else '🟢 Spaces available')
        best=max(allzones,key=lambda z:z['capacity']-z['occupied'])
        st.info(f'💡 Suggested zone: **{best["label"]}** ({best["capacity"]-best["occupied"]} simulated free spaces). Actual distance from your current location is not verified.')
        disclaimer();return
    category={'Classrooms':'classroom','Cafeteria':'cafeteria','Library':'library','Common room':'common','Waiting areas':'waiting','Lecture halls':'lecture','Event occupancy':'event'}[selected]
    records=db.spaces(building,category)
    if not records:
        st.info(f'No verified or sample {selected.lower()} facility is configured for this location. We will not invent one.')
        if st.button('Go back to 3D campus'):navigate(None,None)
        return
    if category in ('classroom','lecture'):
        floors=sorted(set(x['floor'] for x in records))
        picked_floor=st.selectbox('Select building floor',floors,format_func=level_label)
        records=[r for r in records if r['floor']==picked_floor]
    else:
        st.caption('The exact floor is unverified, or this is an outdoor facility (no academic floors).')
    opts={r['id']:r for r in records}
    pick=st.selectbox('Choose classroom / facility',list(opts),format_func=lambda key:opts[key]['label'])
    r=opts[pick]
    suffix=f'  ·  {level_label(r["floor"])}' if building in db.ACADEMIC else ''
    st.markdown(f'#### {r["label"]}{suffix}')
    if category=='classroom':
        a,b,c=st.columns(3)
        a.metric('Room',r['label'])
        b.metric('Status','Unoccupied' if r['occupied']==0 else 'Occupied')
        c.metric('Students inside',r['occupied'])
        label,p=classification(r)
        st.progress(min(1,p/100))
        st.caption(f'Classroom crowd density indicator: **{p:.0f}% ({label})** relative to a simulated reference capacity. No vacant-seat count is shown.')
    else:
        metric_cards(r)
        if category=='cafeteria':
            p=r['occupied']/r['capacity']
            st.info(('Estimated queue: 10–15 min; try outside lunch peak.' if p>.80 else 'Estimated queue: 2–5 min at this simulated occupancy.')+' Waiting times are illustrative.')
        if category=='library':st.info('Tip: The quieter visiting period depends on real footfall; the suggestion is illustrative.')
        if category=='lecture':st.caption('Scheduling / hall booking is demonstration-only, not linked to the official timetable.')
    photo={'cafeteria':('cafeteria.jpg','Tour cafeteria interior — exact building/floor to confirm'), 'library':('library.jpg','Tour library interior — exact building/floor to confirm'), 'lecture':('lecture_hall.jpg','Tour lecture hall interior — room identity to confirm')}.get(category)
    if photo and (ASSETS/photo[0]).exists():
        with st.expander('📸 See reference photo for this facility type'):
            st.image(str(ASSETS/photo[0]),caption=photo[1],use_container_width=True)
    disclaimer()


def control_waste(building):
    st.markdown('### 🗑️ Waste management & cleaning tasks')
    rows=db.bins(building)
    for b in rows:
        with st.container(border=True):
            left,right=st.columns([4,1])
            left.markdown(f'**{b["location"]} — Bin {b["id"].split("_")[-1]}**')
            left.progress(b['fill']/100)
            left.caption(f'Simulated fill: {b["fill"]}% • '+('Collection recommended' if b['fill']>=80 else 'Continue monitoring'))
            if b['fill']>=80 and right.button('Create task',key='bin_task_'+b['id']):
                tid=db.add_ticket('Waste Monitor',building,b['location'],'Waste Collection',f'Empty bin {b["id"]}: fill {b["fill"]}%',priority='High')
                st.success(f'Task MNT-{tid:04d} added to maintenance queue.')
            if role()=='Administrator':
                with st.expander('Update simulated sensor — '+b['id']):
                    value=st.slider('Fill %',0,100,b['fill'],key='fill_'+b['id'])
                    if st.button('Update bin',key='set_bin_'+b['id']):db.update_bin(b['id'],value);st.rerun()
    st.caption('Bins and their locations are sample/demo records, not mapped to verified installed sensors.')


def control_energy(building):
    st.markdown('### ⚡ Electricity monitoring')
    rooms=[r for r in db.spaces(building) if r['category'] in ('classroom','lecture')]
    if not rooms:
        st.info('No classroom-level power records are configured for this non-academic facility.')
        return
    meter=[]
    for r in rooms:
        e=db.energy_for(r['id'])
        meter.append({'room':r['label'],'floor':r['floor'],'kW':sum(e[k] for k in ('ac','lights','fans','other')) if e else 0})
    total=sum(m['kW'] for m in meter)
    a,b=st.columns(2)
    a.metric('Current building power (simulated)',f'{total:.2f} kW')
    b.metric('Sample rooms monitored',len(meter))
    fl=st.selectbox('Floor',sorted(set(x['floor'] for x in rooms)),format_func=level_label,key='energy_floor_'+building)
    scoped=[r for r in rooms if r['floor']==fl]
    sel=st.selectbox('Room',list(range(len(scoped))),format_func=lambda i:scoped[i]['label'])
    r=scoped[sel];e=db.energy_for(r['id'])
    if not e:return
    a,b,c,d=st.columns(4)
    a.metric('AC',f'{e["ac"]:.2f} kW');b.metric('Lights',f'{e["lights"]:.2f} kW');c.metric('Fans',f'{e["fans"]:.2f} kW');d.metric('Other',f'{e["other"]:.2f} kW')
    energy_total=sum(e[k] for k in ('ac','lights','fans','other'))
    st.metric('Total room power',f'{energy_total:.2f} kW')
    fig=go.Figure(go.Bar(x=['AC','Lights','Fans','Other'],y=[e[k] for k in ('ac','lights','fans','other')],marker_color=['#397dc3','#e7ab4a','#42b0a1','#8e7cc3']))
    fig.update_layout(height=260,margin=dict(l=10,r=10,t=12,b=10),yaxis_title='kW · simulated')
    st.plotly_chart(fig,use_container_width=True)
    if r['occupied']==0 and e['ac']+e['lights']+e['fans']>.35:
        st.warning(f'⚠️ Potential energy waste: {r["label"]} has 0 occupants but AC/lights/fans are consuming power.')
        if st.button('Assign inspection task'):
            tid=db.add_ticket('Energy Monitor',building,f'{level_label(fl)} · {r["label"]}','Energy Inspection','Check unnecessary energy use in an unoccupied room.',priority='Medium')
            st.success(f'Inspection ticket MNT-{tid:04d} created.')
    if role()=='Administrator':
        with st.expander('Change simulated room equipment readings'):
            with st.form('energy_edit_'+r['id']):
                vals={k:st.number_input(k.upper()+' kW',0.0,20.0,float(e[k]),step=.1,key='energy_'+r['id']+k) for k in ('ac','lights','fans','other')}
                if st.form_submit_button('Save energy readings'):
                    db.set_energy(r['id'],vals);st.rerun()
    st.caption('Classroom equipment readings are illustrative power draws, NOT metered measurements; energy totals are instantaneous kW, not kWh usage.')
    st.divider()
    st.markdown('#### 📈 Classroom energy vs occupancy — Synthetic / Demo')
    st.caption('Demo time intervals, not live sensors. Red = potential wastage; green = normal use; gray = unknown / incomplete.')
    records=load_energy_readings(BASE/'data'/'synthetic_classroom_energy.csv')
    records=[x for x in records if x['building']==building]
    if records:
        names=sorted(set(x['room'] for x in records))
        sample_room=st.selectbox('Classroom or AC lecture hall',names,key='energy_interval_'+building)
        intervals=sorted([x for x in records if x['room']==sample_room],key=lambda x:x['timestamp'])
        statuses=[classify_interval(x) for x in intervals]
        status_palette={'Possible wastage':'#e14b51','Normal use':'#28a36b','Unknown':'#9299aa'}
        graph=go.Figure()
        for status in ['Possible wastage','Normal use','Unknown']:
            matches=[r for r,c in zip(intervals,statuses) if c==status]
            if not matches:continue
            graph.add_trace(go.Scatter(
                x=[r['timestamp'] for r in matches],
                y=[r['electricity_consumption_kwh'] for r in matches],
                mode='markers',
                name=status,marker=dict(color=status_palette[status],size=13),
                line=dict(color=status_palette[status],width=2),
                customdata=[[r['occupancy'] if r['occupancy'] is not None else 'Missing',r['fan_status'] or 'Missing',r['light_status'] or 'Missing'] for r in matches],
                hovertemplate='%{x}<br>Energy: %{y:.2f} kWh<br>Occupancy: %{customdata[0]}<br>Fan: %{customdata[1]}<br>Light: %{customdata[2]}<extra>%{fullData.name}</extra>'
            ))
        graph.update_layout(height=315,margin=dict(l=8,r=8,t=14,b=25),xaxis_title='Demo timestamp',yaxis_title='Interval energy (kWh)',legend=dict(orientation='h'))
        st.plotly_chart(graph,use_container_width=True)
        table=[]
        for r,cls in zip(intervals,statuses):
            table.append({'Timestamp':r['timestamp'],'Duration (h)':r['duration_hours'],
                         'Occupancy':r['occupancy'],'Fan':r['fan_status'] or 'Unknown','Light':r['light_status'] or 'Unknown',
                         'Electricity (kWh)':r['electricity_consumption_kwh'],
                         'AC (kWh)':r['ac_energy_kwh'],
                         'AC kWh/person-hour':r['energy_per_person_hour_kwh'],
                         'Classification':cls})
        st.dataframe(pd.DataFrame(table),hide_index=True,use_container_width=True)
        st.caption('Energy per person-hour = AC energy (kWh) / (occupancy × hours). The result is blank for zero/missing occupancy. Red means an unoccupied room has fans or lights ON, regardless of AC readings.')
    else:
        st.info('No synthetic interval readings for this selected building.')


def maintenance(building):
    st.markdown('### 🔧 Campus Maintenance & Management')
    st.caption('Student reports, broken equipment, water leaks, plumbing, cleaning, deadlines and worker assignments appear together.')
    records=db.tickets(building)
    a,b,c=st.columns(3)
    a.metric('Total tickets',len(records))
    b.metric('Open tickets',sum(1 for r in records if r['status'] not in ('Verified','Resolved')))
    c.metric('Awaiting verification',sum(1 for r in records if r['status']=='Resolved'))
    if not records:st.info('No tickets yet. Submit a report via Campus Connect or create a waste/energy task.')
    for r in records[:35]:
        with st.expander(f'#{r["id"]:04d} · {r["category"]} · {r["status"]} · {r["location"]}',expanded=False):
            st.write(r['description'])
            st.caption(f'Source: {r["source"]} | Created: {r["created_at"]}')
            if role()=='Administrator':
                with st.form('ticket_'+str(r['id'])):
                    pri=st.selectbox('Importance / priority',['Critical','High','Medium','Low'],index=['Critical','High','Medium','Low'].index(r['priority']))
                    ass=st.selectbox('Assign maintenance worker',['Unassigned','Cleaning Team A','Cleaning Team B','Electrical Team','Plumbing Team','Facilities Team'],index=['Unassigned','Cleaning Team A','Cleaning Team B','Electrical Team','Plumbing Team','Facilities Team'].index(r['assigned_to']) if r['assigned_to'] in ['Unassigned','Cleaning Team A','Cleaning Team B','Electrical Team','Plumbing Team','Facilities Team'] else 0)
                    deadline=st.text_input('Deadline (local ISO date/time; editable)',value=r['deadline'] or db.due_for(pri))
                    sts=['Submitted','Assigned','In Progress','Resolved','Verified']
                    status=st.selectbox('Progress',sts,index=sts.index(r['status']))
                    saved=st.form_submit_button('Save ticket changes',use_container_width=True)
                if saved:
                    if pri != r['priority'] and deadline == r['deadline']:
                        deadline=db.due_for(pri) # Set a newly calculated deadline when importance changes.
                    db.update_ticket(r['id'],pri,ass,deadline,status)
                    st.success('Ticket updated and saved.');st.rerun()
            else:
                st.caption('Priority: '+r['priority']+' | Team: '+r['assigned_to']+' | Deadline: '+str(r['deadline']))
                if r['assigned_to']=='Unassigned':
                    st.info('Waiting for administrator assignment. Maintenance workers cannot assign or verify tickets.')
                elif r['status'] in ('Resolved','Verified'):
                    st.success('Repair finished / awaiting administrator verification.' if r['status']=='Resolved' else 'Verified and closed.')
                else:
                    with st.form('worker_ticket_'+str(r['id'])):
                        worker_status=st.selectbox('Worker progress',['Assigned','In Progress','Resolved'],index=['Assigned','In Progress','Resolved'].index(r['status']) if r['status'] in ('Assigned','In Progress','Resolved') else 0)
                        worker_save=st.form_submit_button('Update my task status')
                    if worker_save:
                        db.update_ticket(r['id'],r['priority'],r['assigned_to'],r['deadline'],worker_status)
                        st.rerun()
    st.caption('Priority time targets are demonstration policies (2h / 24h / 72h / 7d), not approved campus SLAs.')


def operations_simulator(building):
    st.markdown('### 🧪 Sensor & scenario simulator')
    st.caption('Only administrators can change simulated observations. The same data is used by Campus Connect and Campus Control.')
    if role()!='Administrator':st.info('Administrator privileges required to modify simulated sensors.');return
    rows=db.spaces(building)
    if rows:
        ids={r['id']:r for r in rows}
        pick=st.selectbox('Facility sensor',list(ids),format_func=lambda i:f'{ids[i]["label"]} / {level_label(ids[i]["floor"])}')
        r=ids[pick]
        value=st.slider('Simulated people inside',min_value=0,max_value=r['capacity'],value=r['occupied'],key='space_sensor_'+pick)
        if st.button('Apply occupancy reading'):
            db.update_occupancy(pick,value);st.success('Simulation updated');st.rerun()
    st.divider()
    st.markdown('**Parking space simulation (campus-wide)**')
    for z in db.parking():
        p=st.number_input(z['label']+' occupied',0,z['capacity'],z['occupied'],key='parking_num_'+z['id'])
        if st.button('Update '+z['id']):db.update_parking(z['id'],p);st.rerun()
    st.divider()
    col1,col2=st.columns(2)
    if col1.button('🎉 Load College Fest scenario',use_container_width=True):db.festival_scenario();st.rerun()
    if col2.button('↩️ Reset simulated sensors',use_container_width=True):db.reset_scenario();st.rerun()
    st.caption('Reset does not remove reports, worker assignments or incidents. They remain for the hackathon demo.')


def campus_brain(building):
    st.markdown('### 🧠 Campus Brain — Rule-based + Gemini LLM')
    st.caption('The existing local rule-based alerts are preserved. Below them you can also request a real Gemini LLM analysis of selected synthetic campus records.')
    findings=[]
    for b in db.bins(building):
        if b['fill']>=80:findings.append(f'🗑️ Bin {b["id"]} is {b["fill"]}% full: recommend collection task.')
    for r in db.spaces(building):
        if r['category'] in ('cafeteria','library','waiting','common'):
            s,p=classification(r)
            if p>=85: findings.append(f'👥 {r["label"]} at {p:.0f}%: flag high occupancy.')
        if r['category']=='classroom' and r['occupied']==0:
            e=db.energy_for(r['id'])
            if e and e['ac']>.5:findings.append(f'⚡ {r["label"]} empty while AC draws {e["ac"]:.1f} kW; inspect equipment.')
    for z in db.parking():
        if z['occupied']/z['capacity']>.9:findings.append(f'🚗 {z["label"]} nearly full: show alternate zone.')
    findings=findings[:12]
    if not findings:st.success('No simulated threshold alerts at present.')
    else:
        for item in findings:st.info(item)
    st.write('**What-if demonstration:** Administrators can activate College Fest Mode under Simulator; Campus Connect and Control then show changed conditions.')

    # CAMPUSVERSE_GEMINI_START - read-only external LLM enhancement
    st.divider()
    st.markdown('#### ✨ Gemini-powered Campus Brain (Live API)')
    st.caption('Uses a real Gemini LLM and a structured snapshot of the **synthetic/demo** campus database. No passwords, report descriptions or staff names are sent. AI suggestions never modify records.')
    api_key=secrets_get('GEMINI_API_KEY')
    if not api_key:
        st.info('Gemini is not configured yet. Add GEMINI_API_KEY to your private .streamlit/secrets.toml, restart Streamlit, and return here. The rule-based insights above still work.')
    else:
        prompts=[
            'Summarize the main simulated energy, occupancy, maintenance and parking issues.',
            'Which empty classrooms may be wasting electricity, and why?',
            'What maintenance categories should staff prioritize in this demo?',
            'How crowded are the simulated campus facilities and parking zones?',
            'Which resource-efficiency improvements would you suggest from these readings?',
        ]
        preset_key='gemini_preset_'+building
        question_key='gemini_question_'+building
        if question_key not in st.session_state:st.session_state[question_key]=prompts[0]
        def apply_gemini_preset():
            st.session_state[question_key]=st.session_state[preset_key]
        st.selectbox('Try a suggested question',prompts,key=preset_key,on_change=apply_gemini_preset)
        question=st.text_area('Your question for Gemini',key=question_key,max_chars=600)
        if st.button('✨ Analyze synthetic campus data with Gemini',key='gemini_ask_'+building,use_container_width=True):
            if not question.strip():
                st.warning('Please enter a question first.')
            else:
                with st.spinner('Asking Gemini to analyze the simulated campus records...'):
                    try:
                        from campusverse.gemini_brain import ask_gemini, DEFAULT_MODEL
                        model=secrets_get('GEMINI_MODEL') or DEFAULT_MODEL
                        reply=ask_gemini(building,question,api_key,model)
                        st.session_state['gemini_result_'+building]=reply
                    except Exception as exc:
                        st.error('The Gemini request failed. Check internet connection, model access, API key and quota. Error type: '+type(exc).__name__)
        if st.session_state.get('gemini_result_'+building):
            st.markdown('**Gemini analysis (generated from demo data):**')
            st.markdown(st.session_state['gemini_result_'+building])
        st.caption('AI output may be inaccurate. Verify recommendations with staff; crowd/evacuation safety decisions require approved procedures.')
    # CAMPUSVERSE_GEMINI_END


def control_view(building):
    title(building+' / Campus Control · Restricted')
    if st.button('← Back to building options'):navigate(building,None)
    if not login('control'):return
    st.success('🔓 Authorized: '+role())
    if st.button('Sign out',key='signout_control'):
        st.session_state.authenticated_role='';st.rerun()
    tabs=st.tabs(['🗑️ Waste','⚡ Electricity','🔧 Maintenance','🧪 Simulator','🧠 Campus Brain'])
    with tabs[0]:control_waste(building)
    with tabs[1]:control_energy(building)
    with tabs[2]:maintenance(building)
    with tabs[3]:operations_simulator(building)
    with tabs[4]:campus_brain(building)
    disclaimer()


def draw_sectors(crowd):
    # Abstract segmented holding areas without any claimed routing geometry.
    x=[0,1,0,1];y=[1,1,0,0]
    sizes=[crowd//4+(1 if i<crowd%4 else 0) for i in range(4)]
    colors=['#4f94cb','#e3ae57','#4eb79b','#ac8ad6']
    fig=go.Figure()
    for i,(xx,yy) in enumerate(zip(x,y)):
        fig.add_shape(type='rect',x0=xx-.42,y0=yy-.36,x1=xx+.42,y1=yy+.36,
                      fillcolor=colors[i],opacity=.23,line=dict(color=colors[i],width=3))
        fig.add_annotation(x=xx,y=yy,text=f'<b>Sector {"ABCD"[i]}</b><br>{sizes[i]} people',showarrow=False,font=dict(size=15,color='#25364b'))
    fig.add_annotation(x=.5,y=-.68,text='SHARED EVERYDAY ENTRY/EXIT CHECKPOINT · LOCATION NOT TO SCALE',showarrow=False,font=dict(size=11))
    fig.update_xaxes(visible=False,range=[-.55,1.55]);fig.update_yaxes(visible=False,range=[-1,1.48],scaleanchor='x')
    fig.update_layout(height=350,margin=dict(l=0,r=0,t=0,b=0),paper_bgcolor='#f2f6fb',plot_bgcolor='#f2f6fb')
    return fig,sizes


def crowd_view(building):
    title(building+' / Crowd Command · Restricted')
    if st.button('← Back to building options'):navigate(building,None)
    if not login('crowd'):return
    st.success('🔓 Authorized: '+role())
    if st.button('Sign out',key='signout_crowd'):
        st.session_state.authenticated_role='';st.rerun()
    st.error('⚠️ SIMULATION ONLY. This is NOT emergency guidance, a certified route, a verified exit capacity or a stampede-probability estimator. Any real incident requires the university’s approved safety plan and trained personnel.')
    st.markdown('### 🚨 Sectoral crowd monitoring & staff coordination')
    options=['Shared entrance and lobby','Corridor junction','Cafeteria surroundings','Central gathering area']
    if building=='SOE': options=['Exterior glass entrance','Interior lobby / blue-lit turnstiles','First-floor-style corridor (reference unverified)','Other gathering area']
    if building=='Open Auditorium':options=['Open auditorium grounds','Auditorium circulation area']
    if building=='Sports Facilities':options=['Sports grounds','Sports-facility access']
    if building in ('Cricket Ground','DSU Arena'):options=['Spectator gathering area','Event access zone','Outside queues']
    if building=='Parking':options=['Parking entry zone','Parking exit zone','Pedestrian circulation area']
    with st.form('crowd_config_'+building):
        location=st.selectbox('Illustrative monitoring location',options)
        count=st.slider('Simulated crowd count',0,1000,420,10)
        state=st.selectbox('Shared-gate report',['Unverified / Operating normally','Congested','Reported obstruction — investigate','Under inspection; not approved for routing'])
        staff=st.selectbox('Staff coordination',['Unassigned','Security Team A','Security Team B','Campus Operations Team'])
        submit=st.form_submit_button('Generate crowd response scenario',type='primary',use_container_width=True)
    # Threshold is illustrative only, not a safe occupancy capacity.
    if count>=700:st.error('HIGH simulated congestion indicator — notify operations control.')
    elif count>=350:st.warning('ELEVATED simulated congestion indicator — staff review suggested.')
    else:st.success('LOWER simulated congestion indicator — monitor conditions.')
    fig,sizes=draw_sectors(count)
    st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
    st.markdown('#### 📋 Simulated staff coordination steps')
    st.write('1. Notify trained staff to verify crowd size, source of congestion and shared entrance conditions.')
    st.write('2. Observe the four **conceptual sectors** and model *staggered* movement for normal dispersal; avoid intersecting opposing flows where possible.')
    st.write('3. At SOE, monitor both the exterior glass-door area and interior turnstile checkpoint as possible queues.')
    st.write('4. If a gate is reported obstructed, **investigate and escalate**; do not assume it can be reopened or redirect people to an unverified exit.')
    st.write('5. Wait for staff confirmation and the institution’s approved procedure before any physical crowd-control action.')
    if building in db.ACADEMIC:
        st.info('ℹ️ Academic blocks use one shared everyday entry/exit checkpoint in this simulation. Emergency exits, capacities and routes have NOT been verified.')
    else:
        st.info('ℹ️ Outdoor venue circulation, gates, capacities and safety routes are NOT verified. No official routing guidance is provided.')
    if submit:
        action='Verify congestion; coordinate conceptual staged sector movement; escalate any obstruction according to approved procedures.'
        eid=db.add_crowd_event(building,location,count,state,action,staff)
        st.success(f'Crowd alert C-{eid:04d} created for {staff}.')
    incidents=db.crowd_events(building)
    st.markdown('#### 📣 Staff incident response history')
    if not incidents:st.caption('No saved crowd incidents yet. Generate a scenario above.')
    for inc in incidents[:10]:
        with st.expander(f'C-{inc["id"]:04d} • {inc["location"]} • {inc["status"]} • {inc["count"]} simulated people'):
            st.caption('Shared gate: '+inc['shared_gate_status'])
            st.write(inc['action'])
            with st.form('crowd_status_'+str(inc['id'])):
                stat=st.selectbox('Staff progress',['New','Acknowledged','Investigating','Escalated','Closed'],index=['New','Acknowledged','Investigating','Escalated','Closed'].index(inc['status']))
                person=st.selectbox('Responsible team',['Unassigned','Security Team A','Security Team B','Campus Operations Team'],index=['Unassigned','Security Team A','Security Team B','Campus Operations Team'].index(inc['staff']) if inc['staff'] in ['Unassigned','Security Team A','Security Team B','Campus Operations Team'] else 0)
                save=st.form_submit_button('Save staff response')
            if save:db.update_crowd_event(inc['id'],stat,person);st.rerun()
    if building=='SOE':
        with st.expander('📸 SOE glass entrance, turnstile and corridor visual anchors'):
            for name,cap in [('soe_glass.jpg','SOE exterior glass doors viewed from inside'),('soe_turnstiles.jpg','Blue-lit turnstiles further inside the SAME SOE entrance'),('corridor.jpg','Corridor reference labelled towards first-floor lobby; exact layout unverified')]:
                if (ASSETS/name).exists():st.image(str(ASSETS/name),caption=cap,use_container_width=True)
    disclaimer()


if st.session_state.building is None:
    home()
elif st.session_state.mode is None:
    building_hub(st.session_state.building)
elif st.session_state.mode=='connect':
    connect_view(st.session_state.building)
elif st.session_state.mode=='control':
    control_view(st.session_state.building)
elif st.session_state.mode=='crowd':
    crowd_view(st.session_state.building)
else:
    st.session_state.mode=None;st.rerun()
