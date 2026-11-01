# SPDX-License-Identifier: AGPL-3.0-only
"""Independent approximate geometry check; never used as the production engine.
USNO approximate GAST + mean obliquity and Placidus semi-arc construction.
Shares input TT/UT1 epochs, not Swiss sidereal time, angles, or cusp routines.
Range deliberately restricted to |latitude| <= 50 and years ~2000-2100.
"""
import math as m

def approximate_houses(jd_tt,jd_ut1,latitude,longitude):
    if not all(m.isfinite(v) for v in (jd_tt,jd_ut1,latitude,longitude)):
        raise ValueError('Nonfinite input')
    if not 2451544.5<=jd_tt<2488434 or abs(latitude)>50 or abs(longitude)>180:
        raise ValueError('Outside independent checker range')
    d=jd_tt-2451545.;t=d/36525
    jd0=m.floor(jd_ut1-.5)+.5;h=(jd_ut1-jd0)*24
    gmst=(6.697375+.065707485828*(jd0-2451545)+1.0027379*h+.0854103*t+.0000258*t*t)%24
    eps=m.radians(23.4393-.0000004*d)
    omega=m.radians(125.04-.052954*d);sun=m.radians(280.47+.98565*d)
    gast=gmst+(-.000319*m.sin(omega)-.000024*m.sin(2*sun))*m.cos(eps)
    theta=(gast*15+longitude)%360;phi=m.radians(latitude)
    def lon(ra):
        a=m.radians(ra)
        return m.degrees(m.atan2(m.sin(a),m.cos(a)*m.cos(eps)))%360
    a=m.radians(theta)
    asc=(m.degrees(m.atan2(-m.cos(a),m.sin(a)*m.cos(eps)+m.tan(phi)*m.sin(eps)))+180)%360
    mc=lon(theta)
    # RA = ARMC + offset + factor * ascensional_difference(RA).
    # Solve a bracketed residual, independently of the native iteration.
    def cusp(offset,factor):
        def residual(ra):
            tan_delta=m.sin(m.radians(ra))*m.tan(eps)
            ad=m.degrees(m.asin(m.tan(phi)*tan_delta))
            return ra-theta-offset-factor*ad
        low=theta+offset-60;high=theta+offset+60
        if residual(low)*residual(high)>0:raise ValueError('Root not bracketed')
        for _ in range(80):
            mid=(low+high)/2
            if residual(mid)>0:high=mid
            else:low=mid
        return lon((low+high)/2)
    c={1:asc,10:mc,11:cusp(30,1/3),12:cusp(60,2/3),2:cusp(120,2/3),3:cusp(150,1/3)}
    for first,opposite in ((1,7),(10,4),(11,5),(12,6),(2,8),(3,9)):
        c[opposite]=(c[first]+180)%360
    return dict(ascendant=asc,midheaven=mc,house_cusps=[c[i] for i in range(1,13)],armc=theta,mean_obliquity=m.degrees(eps))

def difference(a,b):return abs((a-b+180)%360-180)*3600

if __name__=='__main__':
    import json,pathlib
    s=json.loads(pathlib.Path('calculated_sample.json').read_text());p=s['provenance'];c=s['coordinates']
    a=approximate_houses(p['jd_tt'],p['jd_ut1'],c['latitude'],c['longitude'])
    rows=[dict(name=k,error_arcsec=difference(a[k],s['chart'][k])) for k in ('ascendant','midheaven')]
    rows += [dict(name='house_'+str(i+1),error_arcsec=difference(v,s['chart']['house_cusps'][i])) for i,v in enumerate(a['house_cusps'])]
    r=dict(status='pass_approximate_geometry_for_sample' if max(x['error_arcsec'] for x in rows)<30 else 'review',threshold_arcsec=30,independence='Independent GAST and root-solving geometry; shared TT/UT1 epochs; approximate mean obliquity, not precision certification',approximation=a,rows=rows)
    pathlib.Path('house_geometry_comparison.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
