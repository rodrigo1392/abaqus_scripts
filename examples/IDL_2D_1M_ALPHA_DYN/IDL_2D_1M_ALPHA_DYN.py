xy0 = session.XYDataFromHistory(name='A1 PI: DAM-1 N: 210 NSET CREST-1',
    odb=odb,
    outputVariableName='Spatial acceleration: A1 PI: DAM-1 Node 210 in NSET CREST',
    steps=('HARMONIC', ), __linkedVpName__='Viewport: 1')
c0 = session.Curve(xyData=xy0)
#xy1 = session.XYDataFromHistory(name='A2 PI: DAM-1 N: 210 NSET CREST-1',
#    odb=odb,
#    outputVariableName='Spatial acceleration: A2 PI: DAM-1 Node 210 in NSET CREST',
#    steps=('HARMONIC', ), __linkedVpName__='Viewport: 1')
#c1 = session.Curve(xyData=xy1)
xy2 = session.XYDataFromHistory(name='U1 PI: DAM-1 N: 210 NSET CREST-1',
    odb=odb,
    outputVariableName='Spatial displacement: U1 PI: DAM-1 Node 210 in NSET CREST',
    steps=('HARMONIC', ), __linkedVpName__='Viewport: 1')
c2 = session.Curve(xyData=xy2)
#xy3 = session.XYDataFromHistory(name='U2 PI: DAM-1 N: 210 NSET CREST-1',
#    odb=odb,
#    outputVariableName='Spatial displacement: U2 PI: DAM-1 Node 210 in NSET CREST',
#    steps=('HARMONIC', ), __linkedVpName__='Viewport: 1')
#c3 = session.Curve(xyData=xy3)
xy4 = session.XYDataFromHistory(name='POR PI: WATER-1 N: 21 NSET WATER_BOTTOM-1', odb=odb,
    outputVariableName='Pore or Acoustic Pressure: POR PI: WATER-1 Node 21 in NSET WATER_BOTTOM',
    steps=('HARMONIC', ), __linkedVpName__='Viewport: 1')
c4 = session.Curve(xyData=xy4)
