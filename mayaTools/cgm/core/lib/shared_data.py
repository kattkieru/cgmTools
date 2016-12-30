"""
------------------------------------------
shared_data: cgm.core.lib.shared_data
Author: Josh Burton
email: jjburton@cgmonks.com
Website : http://www.cgmonks.com
------------------------------------------
"""
#>>> Naming
#==================================================================
_d_node_to_suffix = {'follicle':'foll','curveInfo':'crvInfo','condition':'condNode','multiplyDivide':'mdNode','pointOnSurfaceInfo':'posInfoNode','closestPointOnSurface':'cPntOnSurfNode','closestPointOnMesh':'cPntOnMeshNode','plusMinusAverage':'pmAvNode','frameCache':'fCacheNode'}


#>>> Positional data
#===================================================================
_d_rotateOrder_to_index = {'xyz':0,'yzx':1 ,'zxy':2 ,'xzy':3 ,'yxz':4,'zyx':5,'none':6}
_d_rotateOrder_from_index = {0: 'xyz', 1: 'yzx', 2: 'zxy', 3: 'xzy', 4: 'yxz', 5: 'zyx', 6: 'none'}

_d_pivotArgs = {'rp':['rp','r','rotate','rotatePivot','pivot'],'sp':['scale','s','scalePivot'],'boundingBox':['bb','bbCenter'],'closestPoint':['cpos','closest','closestPoint']}
_d_spaceArgs = {'object':['os','objectSpace','local','o'],'world':['w','worldSpace','ws']}




#>>> Axis data
#===================================================================
_d_axis_string_to_vector = {'x+':[1,0,0],
                            'x-':[-1,0,0],
                            'y+':[0,1,0],
                            'y-':[0,-1,0],
                            'z+':[0,0,1],
                            'z-':[0,0,-1]}

_d_axis_vector_to_string = {'[1,0,0]':'x+',
                           '[-1,0,0]':'x-',
                           '[0,1,0]':'y+',
                           '[0,-1,0]':'y-',
                           '[0,0,1]':'z+',
                           '[0,0,-1]':'z-'}

_l_axis_by_string = ['x+','y+','z+','x-','y-','z-'] #Used for several menus and what not
_d_short_axis_to_long = {'x':'x+',
                         'y':'y+',
                         'z':'z+'}

d_vectorToString = {
    '[1, 0, 0]' :'x+',
    '[-1, 0, 0]':'x-',
    '[0, 1, 0]' :'y+',
    '[0,-1, 0]':'y-',
    '[0, 0, 1]' :'z+',
    '[0, 0,-1]':'z-'
}

d_tupleToString = {
    '(1, 0, 0)':'x+',
    '(-1, 0, 0)':'x-',
    '(0, 1, 0)':'y+',
    '(0,-1, 0)':'y-',
    '(0, 0, 1)':'z+',
    '(0, 0,-1)':'z-'
}

d_shortAxisToLong = {
    'x':'x+',
    'y':'y+',
    'z':'z+'
}


#>>> Colors
#===================================================================
_d_curve_colors_to_indices = {'black':1,'grayDark':2,'grayLight':3,'redDark':4,
                              'blueDark':5,'blueBright':6,'greenDark':7,'violetDark':8,
                              'violetBright':9,'brownReg':10,'brownDark':11,
                              'orangeDark':12,'redBright':13,'greenBright':14,'blueDull':15,
                              'white':16,'yellowBright':17,'blueSky':18,'teal':19,
                              'pink':20,'peach':21,'yellow':22,'greenBlue':23,'tan':24,
                              'olive':25,'greenYellow':26,'greenBlue':27,'blueGray':28,
                              'blueGrayDark':29,'purple':30,'purpleBrown':31}

#>>> Gui
#===================================================================
_d_gui_state_colors = {'normal':[1,1,1],
                       'ready':[ 0.166262 ,0.388495 , 0.022797],
                       'keyed':[0.870588, 0.447059, 0.478431],
                       'locked':[0.360784, 0.407843, 0.454902],
                       'connected':[0.945098, 0.945098, 0.647059],
                       'reserved':[0.411765 , 0.411765 , 0.411765],
                       'semiLocked':[ 0.89, 0.89, 0.89],
                       'help':[0.8, 0.8, 0.8],
                       'warning':[0.837, 0.399528, 0.01674],
                       'error':[1, 0.0470588, 0.0677366],
                       'black':[0,0,0]}

_d_gui_direction_colors = {'center':[0.971679, 1, 0],
                           'centerSub':[0.972, 1, 0.726],
                           'left':[0.305882 ,0.814528, 1],
                           'right':[0.976471 ,0.355012, 0.310173]}

    