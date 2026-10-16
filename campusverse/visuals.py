"""Reference-inspired 3D campus exterior and small operations charts.
Geometry/position/height is conceptual and MUST NOT be used for navigation or evacuation.
"""
from __future__ import annotations
import math
import plotly.graph_objects as go

# SOE appears left of CDSIMER in the user's courtyard screenshot.
# Other coordinates are illustrative until independently confirmed.
PLACES = [
    dict(id='SOE', x=0.7, y=1.6, w=6.0, d=2.7, h=4.2, label='SOE', kind='castle'),
    dict(id='CDSIMER', x=12.6, y=1.6, w=6.0, d=2.7, h=4.2, label='CDSIMER', kind='castle'),
    dict(id='AI Block', x=0.7, y=8.9, w=5.2, d=2.5, h=3.4, label='AI Block', kind='castle'),
    dict(id='Hospital', x=13.1, y=8.9, w=5.2, d=2.5, h=3.5, label='Hospital', kind='castle'),
    dict(id='Sports Facilities', x=0.9, y=14.1, w=5.3, d=3.1, h=.1, label='Sports', kind='sport'),
    dict(id='Open Auditorium', x=13.4, y=14.1, w=4.9, d=3.1, h=.35, label='Auditorium', kind='aud'),
]


def cube(fig,x,y,z,w,d,h,color='#e8dcc5',opacity=1):
    # 8 vertices, 12 triangles, vertical sides + roof + bottom
    vx=[x,x+w,x+w,x,x,x+w,x+w,x]
    vy=[y,y,y+d,y+d,y,y,y+d,y+d]
    vz=[z]*4+[z+h]*4
    ti=[0,0,4,4,0,0,1,1,2,2,3,3]
    tj=[1,2,5,6,1,5,2,6,3,7,0,4]
    tk=[2,3,6,7,5,4,6,5,7,6,4,7]
    fig.add_trace(go.Mesh3d(x=vx,y=vy,z=vz,i=ti,j=tj,k=tk,
        color=color,opacity=opacity,flatshading=True,showscale=False,
        hoverinfo='skip',lighting=dict(ambient=.72,diffuse=.55,roughness=.88),showlegend=False))


def path(fig,points,color='#e4d4b7',width=7):
    fig.add_trace(go.Scatter3d(x=[v[0] for v in points],y=[v[1] for v in points],
       z=[v[2] for v in points],mode='lines',line=dict(color=color,width=width),
       hoverinfo='skip',showlegend=False))


def facade(fig,b):
    x,y,w,d,h=b['x'],b['y'],b['w'],b['d'],b['h']
    # Cornice + neoclassical piers on front face
    path(fig,[(x-.09,y-.1,h+.12),(x+w+.09,y-.1,h+.12)],'#e2c8a1',6)
    lines_x=[];lines_y=[];lines_z=[]
    for f in range(1,7):
        xx=x+w*f/7
        lines_x.extend([xx,xx,None]);lines_y.extend([y-.03,y-.03,None]);lines_z.extend([.12,h-.16,None])
        for floor in range(1,5):
            z=(floor-.45)*h/4
            # Window facade, blue glazing, no claim of actual count
            rx=.18
            lines_x.extend([xx-rx,xx+rx,xx+rx,xx-rx,xx-rx,None])
            lines_y.extend([y-.065]*5+[None])
            lines_z.extend([z-.26,z-.26,z+.26,z+.26,z-.26,None])
    fig.add_trace(go.Scatter3d(x=lines_x,y=lines_y,z=lines_z,mode='lines',
      line=dict(color='#60798a',width=3),hoverinfo='skip',showlegend=False))
    # Central portico and entrance pediment visible in photos
    mid=x+w*.50
    cube(fig,mid-.56,y-.45,0,1.12,.52,h*.39,color='#f7edd7')
    cube(fig,mid-.38,y-.49,.03,.76,.06,h*.30,color='#7892a2')
    path(fig,[(mid-.72,y-.51,h*.41),(mid,y-.51,h*.56),(mid+.72,y-.51,h*.41)],'#c9ab81',9)
    # Angular pediment at central upper roof
    path(fig,[(mid-.91,y-.05,h+.13),(mid,y-.05,h+.75),(mid+.91,y-.05,h+.13)],'#b7a187',9)


def model():
    fig=go.Figure()
    cube(fig,-1,-1,-.24,21.0,20,.18,color='#486b57')
    # main pale-paver road, central courtyard crosswalks
    cube(fig,7.55,.1,-.049,3.3,17.6,.06,'#b3a999')
    cube(fig,-.4,5.2,-.048,19.3,2.05,.05,'#b7afa2')
    cube(fig,-.4,12.85,-.046,19.3,.72,.05,'#c9bd9f')
    # DSU-like formal garden quadrants
    for xx in [7.8,9.65]:
        for yy in [6.0,8.0,10.0]:
            cube(fig,xx,yy,.009,1.25,1.15,.09,color='#638b53')
            cube(fig,xx+.08,yy+.08,.105,1.09,.99,.04,color='#3b6d49')
    # focal circular courtyard feature (approximate geometry)
    theta=[i*math.tau/48 for i in range(49)]
    fig.add_trace(go.Scatter3d(x=[9.2+1.03*math.cos(t) for t in theta],
      y=[6.12+.88*math.sin(t) for t in theta],z=[.10]*len(theta),
      mode='lines',line=dict(color='#d8c5aa',width=9),hoverinfo='skip',showlegend=False))
    fig.add_trace(go.Scatter3d(x=[9.2],y=[6.12],z=[.15],mode='markers',
      marker=dict(color='#8abbd2',size=9),hoverinfo='skip',showlegend=False))
    for b in PLACES:
        if b['kind']=='castle':
            cube(fig,b['x'],b['y'],0,b['w'],b['d'],b['h'],'#e5ddcd')
            cube(fig,b['x']+.05,b['y']+.08,b['h'],b['w']-.1,b['d']-.16,.19,'#afa595')
            facade(fig,b)
        elif b['kind']=='sport':
            cube(fig,b['x'],b['y'],0,b['w'],b['d'],.07,'#367c5c')
            path(fig,[(b['x']+.25,b['y']+.25,.1),(b['x']+b['w']-.25,b['y']+.25,.1),
               (b['x']+b['w']-.25,b['y']+b['d']-.25,.1),(b['x']+.25,b['y']+b['d']-.25,.1),
               (b['x']+.25,b['y']+.25,.1)],'#f4edd4',3)
            path(fig,[(b['x']+b['w']/2,b['y']+.24,.1),(b['x']+b['w']/2,b['y']+b['d']-.24,.1)],'#e6eee2',2)
        else:
            cube(fig,b['x'],b['y'],0,b['w'],b['d'],.11,'#c5b59a')
            for i in range(4):
                cube(fig,b['x']+.4+i*.95,b['y']+.25+i*.1,.13,.59,2.0,.18,'#6d8290')
            path(fig,[(b['x']+.1,b['y']+.1,.26),(b['x']+b['w']/2,b['y']+b['d']*.9,.82),(b['x']+b['w']-.1,b['y']+.1,.26)],'#e4dfcd',9)
    # Above-roof markers are conspicuous / clickable where 3D point selection is supported.
    fig.add_trace(go.Scatter3d(
      x=[b['x']+b['w']/2 for b in PLACES],
      y=[b['y']+b['d']/2 for b in PLACES],
      z=[b['h']+(1.35 if b['kind']=='castle' else .95) for b in PLACES],
      mode='markers+text',text=[b['label'] for b in PLACES],textposition='top center',
      textfont=dict(size=13,color='#f7f6e9',family='Arial Black'),
      customdata=[b['id'] for b in PLACES],
      marker=dict(size=10,symbol='diamond',color=['#a4d8f1','#edcd7d','#9cdcb2','#e8c0d2','#8ec9bd','#e8ac8c'],line=dict(color='white',width=2)),
      hovertemplate='<b>%{customdata}</b><extra>Campus area</extra>',showlegend=False))
    fig.update_layout(
      height=670,margin=dict(l=0,r=0,t=0,b=0),paper_bgcolor='#102134',
      font=dict(color='#f7f9fa'),
      scene=dict(bgcolor='#102134',dragmode='turntable',aspectmode='manual',
        aspectratio=dict(x=1.46,y=1.30,z=.61),
        xaxis=dict(visible=False,range=[-1.8,20]),
        yaxis=dict(visible=False,range=[-1.9,19.1]),
        zaxis=dict(visible=False,range=[-.4,8.5]),
        camera=dict(eye=dict(x=1.55,y=-1.65,z=1.5),center=dict(x=0,y=0,z=-.10)),
        uirevision='campus-view'),
      showlegend=False)
    return fig


def occupancy_chart(rows):
    names=[r['label'] for r in rows]
    percents=[round(r['occupied']/r['capacity']*100) if r['capacity'] else 0 for r in rows]
    color=['#21a67a' if p<60 else '#efa83f' if p<85 else '#e77167' for p in percents]
    fig=go.Figure(go.Bar(x=names,y=percents,marker_color=color,text=[f'{p}%' for p in percents],textposition='outside'))
    fig.update_layout(height=280,margin=dict(l=0,r=0,t=15,b=55),yaxis=dict(range=[0,115],title='Occupancy %'),xaxis=dict(tickangle=-15),showlegend=False)
    return fig
