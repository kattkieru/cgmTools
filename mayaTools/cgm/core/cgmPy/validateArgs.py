"""
------------------------------------------
cgm_Meta: cgm.core
Authors: Josh Burton & Ryan Porter

Website : http://www.cgmonks.com
------------------------------------------

This is the Core of the MetaNode implementation of the systems.
It is uses Mark Jackson (Red 9)'s as a base.
================================================================
"""
import sys
import inspect
import os.path

import maya.cmds as mc
import maya.mel as mel

# From Red9 =============================================================

# From cgm ==============================================================
from cgm.lib import search
from cgm.core import cgm_General as cgmGeneral

# Shared Defaults ========================================================

#=========================================================================
import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
#=========================================================================
def isFloatEquivalent(lhs, rhs, **kwargs):
    """
    Return true if both floats are with E (epsilon) of one another, 
    where epsilon is the built-in system float point tolerance.

    :parameters:
        lhs | float
        rhs | float

    :returns
        bool
    """ 
    if not isinstance(lhs, (int, float)) or \
       not isinstance(rhs, (int, float)):
        raise TypeError("Arguments must be 'int' or 'float'")

    return abs(lhs-rhs) <= sys.float_info.epsilon

def isVectorEquivalent(lhs, rhs, **kwargs):
    """
    Return true if two vectors are of equal length and have equal values.

    :parameters:
        lhs | list or tuple of int or float
        rhs | list or tuple of int or float

    :returns
        bool
    """  
    result = False

    if isinstance(lhs, (list, tuple)) and \
       isinstance(rhs, (list, tuple)) and \
       len(lhs) == len(rhs):
        results = [isFloatEquivalent(*values) for values in zip(lhs, rhs)]
        result = False not in results

    return result

def isStringEquivalent(str1,str2):
    """
    Return true if two strings are the same word regardless of case.

    :parameters:
        str1 | 
        str2 |

    :returns
        bool
    """ 
    if str(str1).lower() == str(str2).lower():return True
    return False

#>>> Basics ============================================================== 
def stringArg(arg=None, noneValid=True, calledFrom = None, **kwargs):
    """
    Return 'arg' if 'arg' is a string, else return False if noneValid
    is True, else raise TypeError

    :parameters:
        arg | object
            value to be validated as a string
        noneValid | bool
            if True, returns 'None' if arg is not a string. 
            Otherwise, raises TypeError 

    :returns
        arg or None

    :raises
        TypeError | if arg is not a string and noneValid is False
    """
    log.debug("validateArgs.stringArg arg={0} noneValid={1}".format(arg, noneValid))

    _str_funcRoot = 'stringArg'
    if calledFrom: _str_funcName = "{0}.{1}({2})".format(calledFrom,_str_funcRoot,arg)    
    else:_str_funcName = "{0}({1})".format(_str_funcRoot,arg)    
    
    if not arg:
        if noneValid:return False
        raise ValueError,"Arg is None and not noneValid"

    if issubclass(type(arg),list or tuple):
        arg = arg[0]  
        
    result = arg
   
    if not isinstance(arg, basestring):      
        if noneValid:
            result = False
        else:
            fmt_args = (arg, _str_funcName, type(arg).__name__)
            s_errorMsg = "Arg {0} from func '{1}' is type '{2}', not 'str'"

            raise TypeError(s_errorMsg.format(*fmt_args))

    return result

def listArg(l_args=None, types=None):
    """
    Return list if possible, and all items in that list are 
    instances of types, else return False. If types is None, then the
    type of each item is not tested.

    :parameters:
        l_arg | object
            value to be validated as a list
        types | type, class, or list of types and/or classes

    :returns
        list

    :raises:
        Exception | if arg is not list and unable to convert to list
    """

    result = isinstance(l_args, (tuple, list))
    if not result:
        try:#Conversion -----------------------------------------------------------------------------
            if l_args is not None:
                l_args = [l_args]#try to make it a list
                result = isinstance(l_args, (tuple, list))#Try again
        except Exception,error:raise Exception,"Failed to convert to list | error: {0}".format(error)

    if result:
        if types is not None:
            for arg in l_args:
                if not isinstance(arg, types):
                    result = False
                    break
            result = l_args
        else:
            result = l_args
    return result

def isListArg(l_args=None, types=None):
    """
    Return True if l_args is a list, and all items in that list are 
    instances of types, else return False. If types is None, then the
    type of each item is not tested.

    :parameters:
        l_arg | object
            value to be validated as a list
        types | type, class, or list of types and/or classes

    :returns
        bool

    :raises:
        TypeError | if types is not None and is not a class, type, or list of classes and types
    """

    result = isinstance(l_args, (tuple, list))

    if result and types is not None:
        for arg in l_args:
            if not isinstance(arg, types):
                result = False
                break

    return result

def stringListArg(l_args=None, noneValid=False, calledFrom = None, **kwargs):
    """
    Return each 'arg' in 'l_arg' if it is a string. Raise an exception if 
    any arg is not a string and noneValid is False.

    :parameters:
        l_arg | object
            value to be validated as a list of strings
        noneValid | bool
            if True, returns 'None' if arg is not a string. 
            Otherwise, raises TypeError 

    :returns
        list

    :raises
        TypeError | if l_arg is not a list
        TypeError | if an arg in l_arg fails to pass stringArg and noneValid is False
    """
    log.debug("validateArgs.stringArg arg={0} noneValid={1}".format(str(l_args), noneValid))
    
    _str_funcRoot = 'stringListArg'
    if calledFrom: _str_funcName = "{0}.{1}({2})".format(calledFrom,_str_funcRoot,l_args)    
    else:_str_funcName = "{0}({1})".format(_str_funcRoot,l_args)    
    
    result = []

    if not isinstance(l_args, (tuple, list)):l_args = [l_args]
    
    for arg in l_args:
        tmp = stringArg(arg, noneValid)
        if isinstance(tmp, basestring):
            result.append(tmp)
        else:
            log.warning(
                "Arg {0} from func '{1}' ".format(arg, _str_funcName) +\
                " is type '{2}', not 'str'".format(type(arg).__name__)
            )
    return result
    
def boolArg(arg=None, calledFrom = None, **kwargs):
    """
    Validate that 'arg' is a bool, or an equivalent int (0 or 1), 
    otherwise return False or raise TypeError

    :parameters:
        arg | object
            value to be validated as a bool or equivalent int
        noneValid | bool
            if True, returns 'None' if arg is not a string. 
            Otherwise, raises TypeError 

    :returns
        arg or None

    :raises
        TypeError | if arg is not a bool or equivalent int
    """
    log.debug("validateArgs.boolArg arg={0}".format(arg))

    _str_funcRoot = 'boolArg'
    if calledFrom: _str_funcName = "{0}.{1}({2})".format(calledFrom,_str_funcRoot,arg)    
    else:_str_funcName = "{0}({1})".format(_str_funcRoot,arg) 
    
    result = arg

    if isinstance(arg, int) and arg in [0,1]:
        result = bool(arg)
    elif not isinstance(arg, bool):
        fmt_args = [arg, _str_funcName, type(arg).__name__]
        s_errorMsg = "Arg {0} from func '{1}' is type '{2}', not 'bool' or 0/1".format(*fmt_args)
    
        raise TypeError(s_errorMsg)
    
    return result

def objString(arg=None, mayaType=None, isTransform=None, noneValid=False, calledFrom = None, **kwargs):
    """
    Return 'arg' if 'arg' is an existing, uniquely named Maya object, meeting
    the optional requirements of mayaType and isTransform, otherwise
    return False if noneValid or raise an exception.

    :parameters:
        arg | str
            The name of the Maya object to be validated
        mayaType | str, list
            One or more Maya types - arg must be in this list for the test to pass.
        isTransform | bool
            Test whether 'arg' is a transform 
        noneValid | bool
            Return False if arg does not pass rather than raise an exception

    :returns:
        'arg' or False

    :raises:
        TypeError | if 'arg' is not a string
        NameError | if more than one object name 'arg' exists in the Maya scene
        NameError | if 'arg' does not exist in the Maya scene
        TypeError | if the Maya type of 'arg' is in the list 'mayaType' and noneValid is False
        TypeError | if isTransform is True, 'arg' is not a transform, and noneValid is False
    """
    log.debug("validateArgs.objString arg = {0}".format(arg))

    _str_funcRoot = 'objString'
    if calledFrom: _str_funcName = "{0}.{1} | arg:{2}".format(calledFrom,_str_funcRoot,arg)    
    else:_str_funcName = "{0} | arg:{1}".format(_str_funcRoot,arg) 

    result = None 
    
    if issubclass(type(arg),list or tuple):
        arg = arg[0]  
    
    if not isinstance(arg, basestring):
        raise TypeError('{0}: arg must be string'.format(_str_funcName))

    if len(mc.ls(arg)) > 1:
        raise NameError("{1}: More than one object is named '{0}'".format(arg,_str_funcName))

    if result is None and not mc.objExists(arg):
        if noneValid:
            result = False
        else:
            raise NameError("{1}: '{0}' does not exist".format(arg,_str_funcName))
    
    if result != False and mayaType is not None:
        l_mayaTypes = mayaType
        if isinstance(mayaType, (basestring)):
            l_mayaTypes = [mayaType]

        str_argMayaType = search.returnObjectType(arg)

        if not str_argMayaType in l_mayaTypes:
            if noneValid: 
                result = False
            else:
                str_mayaTypes_formatted = ', '.join(l_mayaTypes)
                fmt_args = [arg, str_argMayaType, str_mayaTypes_formatted, _str_funcName]

                raise TypeError("{3}: Arg {0} is type '{1}', expected '{2}'".format(*fmt_args))

    if result is None and isTransform:
        if not mc.objectType(arg, isType="transform"):
            if noneValid:
                result = False
            else:
                str_argMayaType = search.returnObjectType(arg)
                fmt_args = [arg, str_argMayaType, _str_funcName]
                raise TypeError("{2}: 'Arg {0}' is type {1}, expected 'transform'").format(*fmt_args)

    if result is None:
        result = arg

    return result

def objStringList(l_args=None, mayaType=None, noneValid=False, isTransform=False, calledFrom = None, **kwargs):
    """
    Return each item in l_args if that item is an existing, uniquely named Maya object, 
    meeting the optional requirements of mayaType and isTransform, otherwise raise an
    exception if noneValid is False

    :parameters:

    :returns:
        list

    """
    log.debug("validateArgs.objString arg={0}".format(l_args))

    _str_funcRoot = 'objStringList'
    if calledFrom: _str_funcName = "{0}.{1}({2})".format(calledFrom,_str_funcRoot,l_args)    
    else:_str_funcName = "{0}({1})".format(_str_funcRoot,l_args) 

    result = []

    if not isinstance(l_args, (list, tuple)):l_args = [l_args]

    for arg in l_args:
        tmp = objString(arg, mayaType, noneValid, isTransform)
        if tmp != False:
            result.append(tmp)
        else:
            str_argMayaType = search.returnObjectType(arg)
            log.warning(
                "Arg {0} from func '{1}' ".format(arg, _str_funcName) +\
                " is Maya type '{2}', not 'str'".format(str_argMayaType)
            )

    return result

def valueArg(numberToCheck=None, noneValid=True,
             inRange=None, minValue=None, maxValue=None, autoClamp=False,
             isValue=None, isEquivalent=None,calledFrom = None):
    '''
    Validate that 'numberToCheck' fits the expected parameters and returns False or
    raises exceptions in numberToCheck is invalid. 

    Some parameters are mutually exclusive.

    :parameters:
        numberToCheck | int, float
        noneValid | bool
            Will return False if numberToCheck is invalid rather than raising an exception.
        inRange | list, tuple
            A pair of values, within which numberToCheck must fall
        minValue | int, float
        maxValue | int, float
        autoClamp | bool
            If testing inRange, minValue, or maxValue, and numberToCheck 
            does not pass, return the value clamped to within the expected range.
        isValue | int
        isEquivalent | float

    :returns:
        arg or False

    :raises:
        TypeError | if numberToCheck is not an int or a float
        TypeError | if isValue is not an int
        TypeError | if isEquivalent is not a float
        ValueError | if inRange is not a list or tuple with two values
        ArgumentError | if autoClamp is True but neither inRange, minValue, or maxValue is specified
        ArgumentError | if inRange is specified and either minValue or maxValue
                        is also specified.
    '''
    _str_funcRoot = 'valueArg'
    if calledFrom: _str_funcName = "{0}.{1}({2})".format(calledFrom,_str_funcRoot,numberToCheck)    
    else:_str_funcName = "{0}({1})".format(_str_funcRoot,numberToCheck) 
    
    if not isinstance(numberToCheck, (float, int)):
        if numberToCheck is None and noneValid is True:
            pass
        else:
            raise TypeError('numberToCheck must be an int or a float and noneValid is False')

    result = None

    if result is None and inRange is not None:
        if not isinstance(inRange, (list, tuple)) or len(inRange) != 2:
            raise ValueError('inRange must be a list of two numbers')

        if numberToCheck < min(inRange) or numberToCheck > max(inRange):
            if autoClamp:
                if numberToCheck < min(inRange):
                    numberToCheck = min(inRange)
                elif numberToCheck > max(inRange):
                    numberToCheck = max(inRange)
            else: result = False
        else:
            result = numberToCheck

    if result is None and isinstance(minValue, (float, int)):
        if numberToCheck < minValue:
            if autoClamp:
                result = minValue
            else: result = False
        else:
            result = numberToCheck

    if result is None and isinstance(maxValue, (float, int)):
        if numberToCheck > maxValue:
            if autoClamp:
                result = maxValue
            else: result = False
        else:
            result = numberToCheck

    if result is None and isinstance(isEquivalent, (float, int)):
        if isFloatEquivalent(numberToCheck, isEquivalent):
            result = numberToCheck
        else:
            result = False

    if result is None and isinstance(isValue, (float, int)):
        if numberToCheck == isValue:
            result = numberToCheck
        else:
            result = False

    if result is None:
        if numberToCheck is not None:
            result = numberToCheck
        else:
            result = False

    return result
   
#>>> Maya orientation ============================================================================

# TODO - Maya constants should be centrally grouped?
d_rotateOrder = { 
    'xyz':0,
    'yzx':1,
    'zxy':2,
    'xzy':3,
    'yxz':4,
    'zyx':5
}   

class simpleOrientation():
    """ 
    """
    def __init__(self,arg=None, calledFrom = None, **kwargs):
        
        _str_funcRoot = 'simpleOrientation'
        if calledFrom: _str_funcName = "{0}.{1}({2})".format(calledFrom,_str_funcRoot,arg)    
        else:_str_funcName = "{0}({1})".format(_str_funcRoot,arg)    
        
        log.debug('Caller: {0}, arg: {1}'.format(_str_funcName, arg))

        str_arg = stringArg(arg, noneValid=True)

        if str_arg is False:
            fmt_args = [str_arg, _str_funcName]
            error_msg = "Arg '{0}'' from function '{1}' must be a string"

            raise ValueError(error_msg.format(*fmt_args))

        str_arg = str_arg.lower()

        if not d_rotateOrder.has_key(str_arg):
            fmt_args = [str_arg, 
                        _str_funcName, 
                        'xyz, yzx, zxy, xzy, yxz, or zyx']
            error_msg = 'Arg {0} from function {1} must be a rotation order: {2}'

            raise ValueError(error_msg.format(*fmt_args))
        
        self.__s_orientation_enum = str_arg
        self.__i_orientation_index = d_rotateOrder[str_arg]

        self.__aimAxis = simpleAxis(self.__s_orientation_enum[0])
        self.__upAxis = simpleAxis(self.__s_orientation_enum[1])
        self.__outAxis = simpleAxis(self.__s_orientation_enum[2])

        self.__negativeAimAxis = simpleAxis("{0}-".format(self.__s_orientation_enum[0]))
        self.__negativepUpAxis = simpleAxis("{0}-".format(self.__s_orientation_enum[1]))
        self.__negativeOutAxis = simpleAxis("{0}-".format(self.__s_orientation_enum[2]))

    def __str__(self):
        '''Implementation of Python's built-in 'to string' conversion'''
        return self.__s_orientation_enum

    @property
    def p_string(self):
        return self.__str__()
    
    @property
    def p_aim(self):
        return self.__aimAxis
    
    @property
    def p_up(self):
        return self.__upAxis
    
    @property
    def p_out(self):
        return self.__outAxis

    @property
    def p_aimNegative(self):
        return self.__negativeAimAxis

    @property
    def p_upNegative(self):
        return self.__negativepUpAxis

    @property
    def p_outNegative(self):
        return self.__negativeOutAxis

    def p_ro(self):
        return self.__i_orientation_index
    
#>>> Simple Axis ==========================================================================
l_axisDirectionsByString = ['x+','y+','z+','x-','y-','z-'] #Used for several menus and what not

d_stringToVector = {
    'x+':[1, 0, 0],
    'x-':[-1, 0, 0],
    'y+':[0, 1, 0],
    'y-':[0,-1, 0],
    'z+':[0, 0, 1],
    'z-':[0, 0,-1]
}

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

class simpleAxis():
    """ 
    """
    def __init__(self,arg,calledFrom = None):
        _str_funcRoot = 'simpleAxis'
        if calledFrom: _str_funcName = "{0}.{1}({2})".format(calledFrom,_str_funcRoot,arg)    
        else:_str_funcName = "{0}({1})".format(_str_funcRoot,arg) 
        #log.debug('Caller: {0}, arg: {1}'.format(_str_funcName, arg))
    
        self.__str_axis = None
        self.__v_axis = None
        
        str_arg = arg
        
        if isListArg(arg, types=int):
            str_arg = str(list(arg))
        elif isinstance(arg, basestring):
            pass
        else:
            fmt_args = [str_arg, 
                        _str_funcName]
            error_msg = 'Arg {0} from function {1} must be an axis or a vector'
            raise ValueError(error_msg.format(*fmt_args))

        str_arg = str_arg.replace(' ','')

        if d_shortAxisToLong.has_key(str_arg):
            self.__str_axis = d_shortAxisToLong[str_arg]
            self.__v_axis = d_stringToVector.get(self.__str_axis)
        elif d_stringToVector.has_key(str_arg):
            self.__str_axis = str_arg
            self.__v_axis = d_stringToVector[str_arg]
        elif d_vectorToString.has_key(str_arg):
            self.__str_axis = d_vectorToString[str_arg]
            self.__v_axis = d_stringTovector(self.__str_axis)
        else:
            fmt_args = [str_arg, 
                        _str_funcName]
            error_msg = 'Arg {0} from function {1} is an invalid axis or vector'
            raise ValueError(error_msg.format(*fmt_args))

    def __str__(self):
        return self.__str_axis

    @property
    def p_string(self):
        return self.__str__()

    @property
    def p_vector(self):
        return self.__v_axis
    
    
#>>> Transforms ==========================================================================
def getTransform(arg):
    """Find the transform of the object"""
    buffer = mc.ls(arg, type = 'transform') or False
    if buffer:
        return buffer[0]
    else:
        buffer = mc.listRelatives(arg,parent=True,type='transform') or False
    if buffer:
        return buffer[0]
    return False

def MeshDict(mesh = None, pointCounts = True, calledFrom = None):
    """
    Validates a mesh and returns a dict of data.
    If a shape is the calling object, it will be the shape returned, otherwise, the first shape in the chain will be

    :param mesh: mesh to evaluate
    
    :returns:
    dict -- mesh,meshType,shapes,shape,pointCount,pointCountPerShape
    

    """        
    _str_funcName = 'MeshDict'
    if calledFrom: _str_funcName = "{0} calling {1}".format(calledFrom,_str_funcName) 
    
    _mesh = None 
    
    if mesh is None:
        _bfr = mc.ls(sl=True)
        if not _bfr:raise ValueError,"No selection found and no source arg"
        mesh = _bfr[0]
        log.info("{0}>> No source specified, found: '{1}'".format(_str_funcName,mesh))
           
    _type = search.returnObjectType(mesh)
    _shape = None
    _callObjType = None
    
    if _type in ['mesh']:
        _mesh = mesh
        _callObjType = 'meshCall'
    elif _type in ['shape']:
        _shape = mesh
        _callObjType = 'shapeCall'
        _mesh = getTransform(mesh)
    else:
        raise ValueError,"{0} error. Not a usable mesh type : obj: '{1}' | type: {2}".format(_str_funcName, mesh, _type)

    _shapes = mc.listRelatives(_mesh,shapes=True,fullPath=False)
    
    if _shape is None:
        _shape = _shapes[0]
        
    _return = {'mesh':_mesh,
               'meshType':_type,
               'shapes':_shapes,
               'shape':_shape,
               'callType':_callObjType,
               }
    
    if pointCounts:
        if _callObjType == 'shapeCall':
            _return['pointCount'] = mc.polyEvaluate(_shape, vertex=True)
        else:
            _l_counts = []
            for s in _return['shapes']:
                _l_counts.append( mc.polyEvaluate(s, vertex=True))
            _return['pointCountPerShape'] = _l_counts
            _return['pointCount'] = sum(_l_counts)

    return _return   

def filepath(filepath = None, fileMode = 0, fileFilter = 'Config file (*.cfg)', startDir = None):
    '''
    Validates a given filepath or generates one with dialog if necessary
    
    :parameters:
        filepath | string
        fileMode | int
            0: open
            1: save
            2:find dir (not using currently)
        fileFilter | string
            Descriptor and starred prefix -- 'Config file (*.cfg)'
        startDir | string, None
    '''        
    _d_modes = {0:'save',
                1:'open'}
    
    if filepath is None:
        if startDir is None:
            startDir = mc.workspace(q=True, rootDirectory=True)
        filepath = mc.fileDialog2(dialogStyle=2,
                                  fileMode=fileMode,
                                  startingDirectory=startDir,
                                  fileFilter= fileFilter)
        if filepath:filepath = filepath[0]

    _result = False
    if filepath:
        if fileMode == 1:
            if os.path.exists(filepath):
                log.info("{0} mode | filepath validated... {1}".format(_d_modes.get(fileMode),filepath))                    
                _result = filepath
            else:
                log.info("Invalid filepath ... {0}".format(filepath))                    
        elif fileMode == 0:
            log.info("{0} mode | filepath validated... {1}".format(_d_modes.get(fileMode),filepath))                    
            _result = filepath
    return _result

def kw_fromDict(arg = None ,d = None, indexCallable = False, returnIndex = False,  noneValid = False, calledFrom = None):
    """
    Returns valid kw if it matches a key of a dict or a list of possible options provided.
    
    :parameters:
        arg | string
        d | dict -- Example: {'k1':['KONE','k1']...}
        indexCallable | bool -- if an index value for a list is acceptable or not
        noneValid | bool -- if False and it fails, raise valueError
        calledFrom | string -- calling function for error reporting

    """        
    _str_funcName = 'kw_fromDict'
    if calledFrom: _str_funcName = "{0} calling {1}".format(calledFrom,_str_funcName) 
       
    if arg is None or d is None:
        raise ValueError,"{0}: Must have k and d arguments | arg: {1} | d: {2}".format(_str_funcName, arg, d)
    
    if not isinstance(d, dict):
        raise ValueError,"{0}: d arg must be a dict | d: {1}".format(_str_funcName,d)
    
    for k in d.keys():
        if isStringEquivalent(k,arg):return k
        _l = d[k]
        if not isListArg(_l):
            raise ValueError,"{0}: Invalid list on dict key | k: {1} | Not a list: {2}".format(_str_funcName,k,_l)
        for o in _l:
            if isStringEquivalent(o,arg):return k 
            
    if not noneValid:
        raise ValueError,"{0}: Invalid arg | arg: {1} | options: {2}".format(_str_funcName, arg, d)

def kw_fromList(arg = None ,l = None, indexCallable = False, returnIndex = False, noneValid = False, calledFrom = None):
    """
    Returns valid kw if it matches a list of possible options provided.
    
    :parameters:
        arg | string
        l | list -- Example: {'k1':['KONE','k1']...}
        noneValid | bool -- if False and it fails, raise valueError
        indexCallable | bool -- Whether an index is an acceptable calling method
        returnIndex | bool -- whether you want index returned or the list value
        calledFrom | string -- calling function for error reporting

    """        
    _str_funcName = 'kw_fromList'
    _res = None
    if calledFrom: _str_funcName = "{0} calling {1}".format(calledFrom,_str_funcName) 
       
    if arg is None or l is None:
        if noneValid:return False
        raise ValueError,"{0}: Must have k and l arguments | arg: {1} | l: {2}".format(_str_funcName, arg, l)
    
    if not isListArg(l):
        if noneValid:return False        
        raise ValueError,"{0}: l arg must be a list | l: {1} | type:{2}".format(_str_funcName,l,type(l))
    
    if returnIndex:
        if type(arg) is int:
            if arg <= len(l):
                return arg
            
    for i,o in enumerate(l):
        if o == arg:_res = o
        if i == arg and indexCallable:
            if returnIndex:_res = i
            else:_res = o      
        if isStringEquivalent(o,arg):_res = o
    if _res is None and not noneValid:
        raise ValueError,"{0}: Invalid arg | arg: {1} | options: {2}".format(_str_funcName, arg, l)
    return _res
        
    
    
