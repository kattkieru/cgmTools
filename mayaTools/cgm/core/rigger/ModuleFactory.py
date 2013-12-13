import copy
import re
import time

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# From Maya =============================================================
import maya.cmds as mc

# From Red9 =============================================================
from Red9.core import Red9_Meta as r9Meta
from Red9.core import Red9_CoreUtils as r9Core
from Red9.core import Red9_AnimationUtils as r9Anim

# From cgm ==============================================================
from cgm.core import cgm_General as cgmGeneral
from cgm.core.rigger import TemplateFactory as tFactory
from cgm.core.rigger import JointFactory as jFactory
from cgm.core.rigger import RigFactory as mRig
from cgm.lib import (modules,curves,distance,attributes)
from cgm.lib.ml import ml_resetChannels

from cgm.core.lib import nameTools
from cgm.core.classes import DraggerContextFactory as dragFactory

from cgm.lib.ml import (ml_breakdownDragger,
                        ml_resetChannels)

##>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Shared libraries
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
l_moduleStates = ['define','size','template','skeleton','rig']
__l_modulesClasses__ = ['cgmModule','cgmLimb','cgmEyeball','cgmEyelids','cgmEyebrow','cgmMouthNose']
__l_faceModules__ = ['eyebrow','eyelids','eyeball','mouthNose']
_d_moduleKWARG = {'kw':'mModule',"default":None,'help':"cgmModule mNode or str name","argType":"cgmModule"}
'''
ml_modules = getModules(self.mi_puppet)
int_lenModules = len(ml_modules)  
_str_module = mModule.p_nameShort	 				
self.progressBar_set(status = "Checking Module: '%s' "%(_str_module),progress = i, maxValue = int_lenModules)
	    
'''
class ModuleFunc(cgmGeneral.cgmFuncCls):
    def __init__(self,*args,**kws):
	"""
	"""	
	try:
	    try:mModule = kws['mModule']
	    except:
		try:mModule = args[0]
		except:pass
	    try:
		assert isModule(mModule)
	    except Exception,error:raise StandardError,"[mModule: %s]{Not a module instance : %s}"%(mModule,error)	
	except Exception,error:raise StandardError,"ModuleFunc failed to initialize | %s"%error
	self._str_funcName= "testFModuleFuncunc"		
	super(ModuleFunc, self).__init__(*args, **kws)
	self.mi_module = mModule	
	self._str_moduleName = mModule.p_nameShort	
	self._l_ARGS_KWS_DEFAULTS = [_d_moduleKWARG]	
	#=================================================================

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# Modules
#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> 
def isSized(*args,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """	
	    super(fncWrap, self).__init__(*args,**kws)
	    self._str_funcName = "isSized('%s')"%self._str_moduleName
	    self.__dataBind__(*args,**kws)
	    #=================================================================
	def __func__(self): 
	    mi_module = self.mi_module
	    try:
		if mi_module.moduleType in __l_faceModules__:
		    if mi_module.getMessage('helper'):
			log.debug("%s has size helper, good to go."%self._str_reportStart)	    
			return True
		    else:
			log.debug("%s No size helper found."%self._str_reportStart)	
	    except Exception,error:raise StandardError,"[Face check]{%s}"%error
	    
	    handles = mi_module.templateNull.handles
	    i_coreNames = mi_module.coreNames
	    if len(i_coreNames.value) < handles:
		#log.debug("%s Not enough names for handles"%self._str_reportStart)
		return False
	    if len(i_coreNames.value) > handles:
		#log.debug("%s Not enough handles for names"%self._str_reportStart)	
		return False
	    if mi_module.templateNull.templateStarterData:
		if len(mi_module.templateNull.templateStarterData) == handles:
		    for i,pos in enumerate(mi_module.templateNull.templateStarterData):
			if not pos:
			    log.debug("%s [%s] has no data"%(self._str_reportStart,i))			    
			    return False
		    return True
		else:
		    #log.debug("%s %i is not == %i handles necessary"%(self._str_reportStart,len(mi_module.templateNull.templateStarterData),handles))			    	    
		    return False
	    else:
		pass
		#log.debug("%s No template starter data found"%self._str_reportStart)	
	    return False	 
    return fncWrap(*args,**kws).go() 

def deleteSizeInfo(*args,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """	
	    super(fncWrap, self).__init__(*args,**kws)
	    self._str_funcName = "deleteSizeInfo('%s')"%self._str_moduleName
	    self.__dataBind__(*args,**kws)
	    #=================================================================
	def __func__(self): 
	    mi_module = self.mi_module
	    mi_module.templateNull.__setattr__('templateStarterData','',lock=True)
	    return True
    return fncWrap(*args,**kws).go() 


def doSize(*args,**kws):
    """ 
    Size a module
    1) Determine what points we need to gather
    2) Initiate draggerContextFactory
    3) Prompt user per point
    4) at the end of the day have a pos list the length of the handle list
    
    @ sizeMode
    'all' - pick every handle position
    'normal' - first/last, if child, will use last position of parent as first
    'manual' - provide a pos list to size from
    
    TODO:
    Add option for other modes
    Add geo argument that can be passed for speed
    Add clamp on value
    Add a way to pull size info from a mirror module
    """    
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "doSize('%s')"%self._str_moduleName	
	    self._l_ARGS_KWS_DEFAULTS.extend( [{'kw':'sizeMode',"default":'normal','help':"What way we're gonna size","argType":"int/string"},
	                                       {'kw':'geo',"default":[],'help':"List of geo to use","argType":"list"},
	                                       {'kw':'posList',"default":[],'help':"Position list for manual mode ","argType":"list"}] )		
	    self.__dataBind__(*args,**kws)	    
	    #=================================================================
	    
	def __func__(self,*args,**kws):
	    """
	    """
	    mi_module = self.mi_module
	    kws = self.d_kws
	    sizeMode = kws['sizeMode']
	    geo = kws['geo']
	    posList = kws['posList']
	    clickMode = {"heel":"surface"}    
	    i_coreNames = mi_module.coreNames
	    
	    #Gather info
	    #==============      
	    handles = mi_module.templateNull.handles
	    if len(i_coreNames.value) == handles:
		names = i_coreNames.value
	    else:
		log.warning("Not enough names. Generating")
		names = getGeneratedCoreNames(mi_module)
	    if not geo and not mi_module.getMessage('helper'):
		geo = mi_module.modulePuppet.getGeo()
	    log.debug("Handles: %s"%handles)
	    log.debug("Names: %s"%names)
	    log.debug("Puppet: %s"%mi_module.getMessage('modulePuppet'))
	    log.debug("Geo: %s"%geo)
	    log.debug("sizeMode: %s"%sizeMode)
	    
	    i_module = mi_module #Bridge holder for our module class to go into our sizer class
	    
	    #Variables
	    #============== 
	    if sizeMode == 'manual':#To allow for a pos list to be input
		if not posList:
		    log.error("Must have posList arg with 'manual' sizeMode!")
		    return False
		
		if len(posList) < handles:
		    log.warning("Creating curve to get enough points")                
		    curve = curves.curveFromPosList(posList)
		    mc.rebuildCurve (curve, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0,s=(handles-1), d=1, tol=0.001)
		    posList = curves.returnCVsPosList(curve)#Get the pos of the cv's
		    mc.delete(curve) 
		    
		mi_module.templateNull.__setattr__('templateStarterData',posList,lock=True)
		log.debug("'%s' manually sized!"%mi_module.getShortName())
		return True
		    
	    elif sizeMode == 'normal':
		if len(names) > 1:
		    namesToCreate = names[0],names[-1]
		else:
		    namesToCreate = names
		log.debug("Names: %s"%names)
	    else:
		namesToCreate = names        
		sizeMode = 'all'
	    
	    class moduleSizer(dragFactory.clickMesh):
		"""Sublass to get the functs we need in there"""
		def __init__(self,i_module = mi_module,**kws):
		    log.debug(">>> moduleSizer.__init__")    
		    if kws:log.info("kws: %s"%str(kws))
		    
		    super(moduleSizer, self).__init__(**kws)
		    self.mi_module = i_module
		    self.toCreate = namesToCreate
		    log.info("Please place '%s'"%self.toCreate[0])
		    
		def release(self):
		    if len(self.l_return)< len(self.toCreate)-1:#If we have a prompt left
			log.info("Please place '%s'"%self.toCreate[len(self.l_return)+1])            
		    dragFactory.clickMesh.release(self)
	
		    
		def finalize(self):
		    log.debug("returnList: %s"% self.l_return)
		    log.debug("createdList: %s"% self.l_created)   
		    buffer = [] #self.mi_module.templateNull.templateStarterData
		    log.debug("starting data: %s"% buffer)
		    
		    #Make sure we have enough points
		    #==============  
		    handles = self.mi_module.templateNull.handles
		    if len(self.l_return) < handles:
			log.warning("Creating curve to get enough points")                
			curve = curves.curveFromPosList(self.l_return)
			mc.rebuildCurve (curve, ch=0, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0,s=(handles-1), d=1, tol=0.001)
			self.l_return = curves.returnCVsPosList(curve)#Get the pos of the cv's
			mc.delete(curve)
	
		    #Store info
		    #==============                  
		    for i,p in enumerate(self.l_return):
			buffer.append(p)#need to ensure it's storing properly
			#log.info('[%s,%s]'%(buffer[i],p))
			
		    #Store locs
		    #==============  
		    log.debug("finish data: %s"% buffer)
		    self.mi_module.templateNull.__setattr__('templateStarterData',buffer,lock=True)
		    #self.mi_module.templateNull.templateStarterData = buffer#store it
		    log.info("'%s' sized!"%self._str_moduleName)
		    dragFactory.clickMesh.finalize(self)
		
	    #Start up our sizer    
	    return moduleSizer(mode = 'midPoint',
	                       mesh = geo,
	                       create = 'locator',
	                       toCreate = namesToCreate)
    return fncWrap(*args,**kws).go() 
    

def doSetParentModule(*args,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """	
	    super(fncWrap, self).__init__(*args,**kws)
	    self._str_funcName = "doSetParentModule('%s')"%self._str_moduleName
	    self._l_ARGS_KWS_DEFAULTS = [{'kw':'moduleParent',"default":None,'help':"Module parent target","argType":"cgmModule"},
	                                 {'kw':'force',"default":False,'help':"Whether to force things","argType":"bool"}] 			    
	    self.__dataBind__(*args,**kws)
	    #=================================================================
	def __func__(self): 
	    mi_module = self.mi_module
	    kws = self.d_kws
	    moduleParent = self.d_kws['moduleParent']
	    try:
		moduleParent.mNode#See if we have an instance
	    except:
		if mc.objExists(moduleParent):
		    moduleParent = r9Meta.MetaClass(moduleParent)#initialize
		else:
		    log.warning("'%s' doesn't exist"%moduleParent)#if it doesn't initialize, nothing is there		
		    return False	
	
	    #Logic checks
	    #==============
	    if not moduleParent.hasAttr('mClass'):
		log.warning("'%s' lacks an mClass attr"%module.mNode)	    
		return False
	
	    if moduleParent.mClass not in __l_modulesClasses__:
		self.log_warning("'%s' is not a recognized module type"%moduleParent.mClass)
		return False
	
	    if not moduleParent.hasAttr('moduleChildren'):#Quick check
		self.log_warning("'%s'doesn't have 'moduleChildren' attr"%moduleParent.getShortName())#if it doesn't initialize, nothing is there		
		return False	
	    buffer = copy.copy(moduleParent.getMessage('moduleChildren',False)) or []#Buffer till we have have append functionality	
	    ml_moduleChildren = moduleParent.moduleChildren

	    if mi_module in ml_moduleChildren:
		self.log_warning("already connnected to '%s'"%(moduleParent.getShortName()))
		return
	    else:
		try:#Connect ==========================================================================================
		    buffer.append(mi_module.mNode) #Revist when children has proper add/remove handling
		    moduleParent.moduleChildren = buffer
		    mi_module.moduleParent = moduleParent.mNode
		    self.log_info("parent set to: '%s'!"%moduleParent.getShortName())    
		except Exception,error:raise StandardError,"[Connection]{%s}"%(error)	
	    mi_module.parent = moduleParent.parent
	    return True	 
    return fncWrap(*args,**kws).go() 

def getGeneratedCoreNames(*args,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """	
	    super(fncWrap, self).__init__(*args,**kws)
	    self._str_funcName = "getGeneratedCoreNames('%s')"%self._str_moduleName			    
	    self.__dataBind__(*args,**kws)
	    #=================================================================
	def __func__(self): 
	    mi_module = self.mi_module
	    kws = self.d_kws
	    mi_coreNamesBuffer = mi_module.coreNames
		
	    ### check the settings first ###
	    partType = mi_module.moduleType
	    log.debug("%s partType is %s"%(mi_module.getShortName(),partType))
	    settingsCoreNames = modules.returncgmTemplateCoreNames(partType)
	    int_handles = mi_module.templateNull.handles
	    partName = nameTools.returnRawGeneratedName(mi_module.mNode,ignore=['cgmType','cgmTypeModifier'])
	
	    ### if there are no names settings, genearate them from name of the limb module###
	    l_generatedNames = []
	    if settingsCoreNames == False: 
		if mi_module.moduleType.lower() == 'eyeball':
		    l_generatedNames.append('%s' % (partName))	    
		else:
		    cnt = 1
		    for handle in range(int_handles):
			l_generatedNames.append('%s%s%i' % (partName,'_',cnt))
			cnt+=1
	    elif int(int_handles) > (len(settingsCoreNames)):
		log.debug(" We need to make sure that there are enough core names for handles")       
		cntNeeded = int_handles  - len(settingsCoreNames) +1
		nonSplitEnd = settingsCoreNames[len(settingsCoreNames)-2:]
		toIterate = settingsCoreNames[1]
		iterated = []
		for i in range(cntNeeded):
		    iterated.append('%s%s%i' % (toIterate,'_',(i+1)))
		l_generatedNames.append(settingsCoreNames[0])
		for name in iterated:
		    l_generatedNames.append(name)
		for name in nonSplitEnd:
		    l_generatedNames.append(name) 
	    else:
		l_generatedNames = settingsCoreNames[:self.templateNull.handles]
	    
		#figure out what to do with the names
		mi_coreNamesBuffer.value = l_generatedNames
		    
	    return l_generatedNames
    return fncWrap(*args,**kws).go() 

'''
def getGeneratedCoreNamesBAK(self):
    """ 
    Generate core names for a module and return them

    self MUST be cgmModule

    RETURNS:
    generatedNames(list)
    
    TODO:
    Where to store names?
    """
    _str_funcName = "getGeneratedCoreNames('%s')"%self.p_nameShort   
    log.info(">>> %s "%(_str_funcName) + "="*75)    
    try:
	i_coreNames = self.coreNames
    
	### check the settings first ###
	partType = self.moduleType
	log.debug("%s partType is %s"%(self.getShortName(),partType))
	settingsCoreNames = modules.returncgmTemplateCoreNames(partType)
	handles = self.templateNull.handles
	partName = nameTools.returnRawGeneratedName(self.mNode,ignore=['cgmType','cgmTypeModifier'])
    
	### if there are no names settings, genearate them from name of the limb module###
	generatedNames = []
	if settingsCoreNames == False: 
	    if self.moduleType.lower() == 'eyeball':
		generatedNames.append('%s' % (partName))	    
	    else:
		cnt = 1
		for handle in range(handles):
		    generatedNames.append('%s%s%i' % (partName,'_',cnt))
		    cnt+=1
	elif int(self.templateNull.handles) > (len(settingsCoreNames)):
	    log.debug(" We need to make sure that there are enough core names for handles")       
	    cntNeeded = self.templateNull.handles  - len(settingsCoreNames) +1
	    nonSplitEnd = settingsCoreNames[len(settingsCoreNames)-2:]
	    toIterate = settingsCoreNames[1]
	    iterated = []
	    for i in range(cntNeeded):
		iterated.append('%s%s%i' % (toIterate,'_',(i+1)))
	    generatedNames.append(settingsCoreNames[0])
	    for name in iterated:
		generatedNames.append(name)
	    for name in nonSplitEnd:
		generatedNames.append(name) 
    
	else:
	    log.debug(" Culling from settingsCoreNames")        
	    generatedNames = settingsCoreNames[:self.templateNull.handles]
    
	#figure out what to do with the names
	i_coreNames.value = generatedNames
	"""
	if not self.templateNull.templateStarterData:
	    buffer = []
	    for n in generatedNames:
		buffer.append([str(n),[]])
	    self.templateNull.templateStarterData = buffer
	else:
	    for i,pair in enumerate(self.templateNull.templateStarterData):
		pair[0] = generatedNames[i]    
	"""
	    
	return generatedNames
    except Exception,error:
	raise StandardError,"%s >> %s"%(_str_funcName,error)   
    '''
#=====================================================================================================
#>>> Rig
#=====================================================================================================
def doRig(*args,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "doRig('%s')"%self._str_moduleName	
	    
	    self.__dataBind__(*args,**kws)		    
	    #=================================================================
	    
	def __func__(self):
	    """
	    """
	    mi_module = self.mi_module
	    kws = self.d_kws
	    
	    if not isSkeletonized(mi_module):
		log.warning("%s Not skeletonized"%self._str_reportStart)
		return False      
	    if mi_module.moduleParent and not isRigged(mi_module.moduleParent):
		log.warning("%s Parent module is not rigged: '%s'"%(self._str_reportStart,mi_module.moduleParent.getShortName()))
		return False 
	    
	    kws.pop('mModule')
	    mRig.go(**kws)      
	    if not isRigged(**kws):
		log.warning("%s Failed To Rig"%self._str_reportStart)
		return False
	    
	    rigConnect(**kws)
	    
    return fncWrap(*args,**kws).go()


def isRigged(*args,**kws):
    """
    Return if a module is rigged or not
    """    
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """    
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "isRigged('%s')"%self._str_moduleName	
	    self.__dataBind__(*args,**kws)	
	    #=================================================================
	    
	def __func__(self):
	    kws = self.d_kws
	    mi_module = self.mi_module
	    
	    if not isSkeletonized(**kws):
		log.debug("%s Not skeletonized"%self._str_reportStart)
		return False   
		
	    mi_rigNull = mi_module.rigNull
	    str_shortName = self._str_moduleName
	    
	    ml_rigJoints = mi_rigNull.msgList_get('rigJoints',asMeta = True)
	    l_rigJoints = [i_j.p_nameShort for i_j in ml_rigJoints] or []
	    l_skinJoints = mRig.get_skinJoints(mi_module,asMeta=False)
	    
	    if not ml_rigJoints:
		log.debug("%s>>>> No rig joints"%self._str_reportStart)
		mi_rigNull.version = ''#clear the version	
		return False
	    
	    #See if we can find any constraints on the rig Joints
	    if mi_module.moduleType.lower() in __l_faceModules__:
		self.log_warning("Need to find a better face rig joint test rather than constraints")	    
	    else:
		b_foundConstraint = False
		for i,mJoint in enumerate(ml_rigJoints):
		    if mJoint.getConstraintsTo():
			b_foundConstraint = True
		    elif i == (len(ml_rigJoints) - 1) and not b_foundConstraint:
			log.warning("%s No rig joints are constrained"%(self._str_reportStart))	    
			return False
		
	    if len( l_skinJoints ) < len( ml_rigJoints ):
		self.log_warning(" %s != %s. Not enough rig joints"%(len(l_skinJoints),len(l_rigJoints)))
		mi_rigNull.version = ''#clear the version        
		return False
	    
	    for attr in ['controlsAll']:
		if not mi_rigNull.msgList_get(attr,asMeta = False):
		    self.log_warning("No data found on '%s'"%(attr))
		    mi_rigNull.version = ''#clear the version            
		    return False    
	    return True	     
    return fncWrap(*args,**kws).go()


def rigDelete(*args,**kws):
    """
    Return if a module is rigged or not
    """    
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """    
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "rigDelete('%s')"%self._str_moduleName	
	    self.__dataBind__(*args,**kws)	
	    #=================================================================
	    
	def __func__(self):
	    kws = self.d_kws
	    
	    #if not isRigged(self):
		#raise StandardError,"moduleFactory.rigDelete('%s')>>>> Module not rigged"%(str_shortName)
	    if isRigConnected(self.mi_module,**kws):
		rigDisconnect(self.mi_module,**kws)#Disconnect
	    """
	    try:
		objList = returnTemplateObjects(self)
		if objList:
		    mc.delete(objList)
		for obj in self.templateNull.getChildren():
		    mc.delete(obj)
		return True
	    except Exception,error:
		log.warning(error)"""
	    mi_rigNull = self.mi_module.rigNull
	    l_rigNullStuff = mi_rigNull.getAllChildren()
	    
	    #Build a control master group List
	    l_masterGroups = []
	    for i_obj in mi_rigNull.msgList_get('controlsAll'):
		if i_obj.hasAttr('masterGroup'):
		    l_masterGroups.append(i_obj.getMessage('masterGroup',False)[0])
		    
	    log.debug("%s masterGroups found: %s"%(self._str_reportStart,l_masterGroups))  
	    for obj in l_masterGroups:
		if mc.objExists(obj):
		    mc.delete(obj)
		    
	    if self.mi_module.getMessage('deformNull'):
		mc.delete(self.mi_module.getMessage('deformNull'))
		
	    mc.delete(mi_rigNull.getChildren())
	    mi_rigNull.version = ''#clear the version
	    
	    return True   
    return fncWrap(*args,**kws).go()

def isRigConnected(*args,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "isRigConnected('%s')"%self._str_moduleName	
	    
	    #self._l_ARGS_KWS_DEFAULTS.extend( [{'kw':'FILLIN',"default":None,'help':"FILLIN","argType":"FILLIN"}] )		
	    self.__dataBind__(*args,**kws)		    
	    #=================================================================
	    
	def __func__(self):
	    """
	    """
	    mi_module = self.mi_module
	    #str_shortName = self._str_moduleName
	    if not isRigged(mi_module):
		log.debug("%s Module not rigged"%(self._str_reportStart))
		return False
	    mi_rigNull = mi_module.rigNull
	    ml_rigJoints = mi_rigNull.msgList_get('rigJoints',asMeta = True)
	    ml_skinJoints = mRig.get_skinJoints(mi_module,asMeta=True)
	    
	    for i,i_jnt in enumerate(ml_skinJoints):
		try:
		    if not i_jnt.isConstrainedBy(ml_rigJoints[i].mNode):
			log.warning("'%s'>>not constraining>>'%s'"%(ml_rigJoints[i].getShortName(),i_jnt.getShortName()))
			return False
		except Exception,error:
		    log.error(error)
		    raise StandardError,"%s Joint failed: %s"%(self._str_reportStart,i_jnt.getShortName())
	    return True
    return fncWrap(*args,**kws).go()

def rigConnect(*args,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "rigConnect('%s')"%self._str_moduleName	
	    
	    #self._l_ARGS_KWS_DEFAULTS.extend( [{'kw':'FILLIN',"default":None,'help':"FILLIN","argType":"FILLIN"}] )		
	    self.__dataBind__(*args,**kws)		    
	    #=================================================================
	    
	def __func__(self):
	    """
	    """
	    mi_module = self.mi_module
	    str_shortName = self._str_moduleName
	    
	    if not isRigged(mi_module):
		raise StandardError,"Module not rigged"
	    if isRigConnected(mi_module):
		raise StandardError,"Module already connected"
	    
	    mi_rigNull = mi_module.rigNull
	    ml_rigJoints = mi_rigNull.msgList_get('rigJoints',asMeta = True)
	    ml_skinJoints = mRig.get_skinJoints(mi_module,asMeta=True)
	    
	    if mi_module.moduleType in __l_faceModules__:
		_b_faceState = True
		mi_faceDeformNull = mi_module.faceDeformNull
	    else:_b_faceState = False

	    if len(ml_skinJoints)!=len(ml_rigJoints):
		raise StandardError,"Rig/Skin joint chain lengths don't match"
	    
	    for i,i_jnt in enumerate(ml_skinJoints):
		try:
		    log.debug("'%s'>>drives>>'%s'"%(ml_rigJoints[i].getShortName(),i_jnt.getShortName()))       
		    if _b_faceState:
			pntConstBuffer = mc.parentConstraint(ml_rigJoints[i].mNode,i_jnt.mNode,maintainOffset=True,weight=1)        			
			scConstBuffer = mc.scaleConstraint(ml_rigJoints[i].mNode,i_jnt.mNode,maintainOffset=True,weight=1) 
			for str_a in 'xyz':
			    attributes.doConnectAttr('%s.s%s'%(i_jnt.parent,str_a),'%s.offset%s'%(scConstBuffer[0],str_a.capitalize()))			    
			    #attributes.doConnectAttr('%s.s%s'%(mi_faceDeformNull.mNode,str_a),'%s.offset%s'%(scConstBuffer[0],str_a.capitalize()))
		    else:
			pntConstBuffer = mc.pointConstraint(ml_rigJoints[i].mNode,i_jnt.mNode,maintainOffset=True,weight=1)        
			orConstBuffer = mc.orientConstraint(ml_rigJoints[i].mNode,i_jnt.mNode,maintainOffset=True,weight=1) 			
			attributes.doConnectAttr((ml_rigJoints[i].mNode+'.s'),(i_jnt.mNode+'.s'))
		except Exception,error:
		    raise StandardError,"Joint failed: %s | %s"%(i_jnt.getShortName(),error)
	    return True
    return fncWrap(*args,**kws).go()

def rigDisconnect(*args,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "rigDisconnect('%s')"%self._str_moduleName	
	    
	    self._l_ARGS_KWS_DEFAULTS.extend( [{'kw':'FILLIN',"default":None,'help':"FILLIN","argType":"FILLIN"}] )		
	    self.__dataBind__(*args,**kws)	    
	    #=================================================================
	    
	def __func__(self):
	    """
	    """
	    mi_module = self.mi_module
	    """
	    if not isRigged(mi_module):
		raise StandardError,"Module not rigged"
	    if not isRigConnected(mi_module):
		raise StandardError,"Module not connected"
	    """
	    if mi_module.moduleType in __l_faceModules__:_b_faceState = True
	    else:_b_faceState = False
	    
	    mc.select(cl=True)
	    mc.select(mi_module.rigNull.msgList_getMessage('controlsAll'))
	    ml_resetChannels.main(transformsOnly = False)
	    
	    mi_rigNull = mi_module.rigNull
	    l_rigJoints = mi_rigNull.getMessage('rigJoints') or False
	    l_skinJoints = mi_rigNull.getMessage('skinJoints') or False
	    if not l_skinJoints:raise Exception,"No skin joints found"	    
	    l_constraints = []
	    for i,i_jnt in enumerate(mi_rigNull.skinJoints):
		try:
		    l_constraints.extend( i_jnt.getConstraintsTo() )
		    if not _b_faceState:attributes.doBreakConnection("%s.scale"%i_jnt.mNode)
		except Exception,error:
		    log.error(error)
		    raise StandardError,"Joint failed: %s"%(i_jnt.getShortName())
	    log.debug("%s constraints found: %s"%(self._str_reportStart,l_constraints))
	    if l_constraints:mc.delete(l_constraints)
	    return True
    return fncWrap(*args,**kws).go()
 
    
def rig_getReport(self,*args,**kws):    
    mRig.get_report(self,*args,**kws)      
    return True
    #except Exception,error:
        #log.warning(error)
	
def rig_getSkinJoints(self,asMeta = True): 
    """
    if not isSkeletonized(self):
        log.warning("%s.rig_getSkinJoints>>> Not skeletonized"%self.getShortName())
        return False    """   
    return mRig.get_skinJoints(self,asMeta)      
	
def rig_getHandleJoints(self,asMeta = True):
    """
    Find the module handle joints
    """
    _str_funcName = "rig_getHandleJoints('%s')"%self.p_nameShort   
    log.debug(">>> %s "%(_str_funcName) + "="*75)  	    
    try:
	return mRig.get_handleJoints(self,asMeta)
    except Exception,error:
	raise StandardError,"%s >> %s"%(_str_funcName,error)
    
def rig_getRigHandleJoints(self,asMeta = True):
    """
    Find the module handle joints
    """
    try:
	return mRig.get_rigHandleJoints(self,asMeta)
    except Exception,error:
	raise StandardError,"%s.rig_getRigHandleJoints >> failed: %s"%(self.getShortName(),error)
    
#=====================================================================================================
#>>> Template
#=====================================================================================================
def isTemplated(*args,**kws):
    """
    Return if a module is templated or not
    """    
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "isTemplated('%s')"%self._str_moduleName	
	    
	    self.__dataBind__(*args,**kws)	
	    #=================================================================
	    
	def __func__(self):
	    """
	    """
	    mi_module = self.mi_module
	    
	    if mi_module.moduleType in __l_faceModules__:
		if mi_module.getMessage('helper'):
		    log.debug("%s has size helper, good to go."%self._str_reportStart)	    
		    return True
		
	    coreNamesValue = mi_module.coreNames.value
	    if not coreNamesValue:
		log.debug("No core names found")
		return False
	    if not mi_module.getMessage('templateNull'):
		log.debug("No template null")
		return False       
	    if not mi_module.templateNull.getChildren():
		log.debug("No children found in template null")
		return False   
	    if not mi_module.getMessage('modulePuppet'):
		log.debug("No modulePuppet found")
		return False   	
	    if not mi_module.modulePuppet.getMessage('masterControl'):
		log.debug("No masterControl")
		return False
		
	    if mi_module.mClass in ['cgmModule','cgmLimb']:
		#Check our msgList attrs
		#=====================================================================================
		ml_controlObjects = mi_module.templateNull.msgList_get('controlObjects')
		for attr in 'controlObjects','orientHelpers':
		    if not mi_module.templateNull.msgList_getMessage(attr):
			log.warning("No data found on '%s'"%attr)
			return False        
		
		#Check the others
		for attr in 'root','curve','orientRootHelper':
		    if not mi_module.templateNull.getMessage(attr):
			if attr == 'orientHelpers' and len(controlObjects)==1:
			    pass
			else:
			    log.warning("No data found on '%s'"%attr)
			    return False    
		    
		if len(coreNamesValue) != len(ml_controlObjects):
		    log.debug("Not enough handles.")
		    return False    
		    
		if len(ml_controlObjects)>1:
		    for i_obj in ml_controlObjects:#check for helpers
			if not i_obj.getMessage('helper'):
			    log.debug("'%s' missing it's helper"%i_obj.getShortName())
			    return False
		return True    
    return fncWrap(*args,**kws).go()
'''
def isTemplated(self):
    """
    Return if a module is templated or not
    """
    _str_funcName = "isTemplated('%s')"%self.p_nameShort   
    log.debug(">>> %s "%(_str_funcName) + "="*75)    
    try:
	if self.mClass in ['cgmEyelids','cgmEyeball','cgmEyebrow']:
	    if self.getMessage('helper'):
		log.debug("%s.isTemplated>>> has size helper, good to go."%self.getShortName())	    
		return True
	    
	coreNamesValue = self.coreNames.value
	if not coreNamesValue:
	    log.debug("No core names found")
	    return False
	if not self.getMessage('templateNull'):
	    log.debug("No template null")
	    return False       
	if not self.templateNull.getChildren():
	    log.debug("No children found in template null")
	    return False   
	if not self.getMessage('modulePuppet'):
	    log.debug("No modulePuppet found")
	    return False   	
	if not self.modulePuppet.getMessage('masterControl'):
	    log.debug("No masterControl")
	    return False
	    
	if self.mClass in ['cgmModule','cgmLimb']:
	    #Check our msgList attrs
	    #=====================================================================================
	    ml_controlObjects = self.templateNull.msgList_get('controlObjects')
	    for attr in 'controlObjects','orientHelpers':
		if not self.templateNull.msgList_getMessage(attr):
		    log.warning("No data found on '%s'"%attr)
		    return False        
	    
	    #Check the others
	    for attr in 'root','curve','orientRootHelper':
		if not self.templateNull.getMessage(attr):
		    if attr == 'orientHelpers' and len(controlObjects)==1:
			pass
		    else:
			log.warning("No data found on '%s'"%attr)
			return False    
		
	    if len(coreNamesValue) != len(ml_controlObjects):
		log.debug("Not enough handles.")
		return False    
		
	    if len(ml_controlObjects)>1:
		for i_obj in ml_controlObjects:#check for helpers
		    if not i_obj.getMessage('helper'):
			log.debug("'%s' missing it's helper"%i_obj.getShortName())
			return False
	    
	    #self.moduleStates['templateState'] = True #Not working yet
	    return True
	elif self.mClass == 'cgmEyeball':
	    return True
    except Exception,error:
	raise StandardError,"%s >> %s"%(_str_funcName,error)   
'''

def doTemplate(*args,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "doTemplate('%s')"%self._str_moduleName	
	    self.__dataBind__(*args,**kws)	
	    #=================================================================
	    
	def __func__(self,*args,**kws):
	    mi_module = self.mi_module
	    kws = self.d_kws
	    
	    if isTemplated(*args,**kws):
		return True
	    if not isSized(*args,**kws):
		log.warning("%s: Not sized"%self._str_reportStart)
		return False    
	    tFactory.go(mi_module,*args,**kws)      
	    if not isTemplated(*args,**kws):
		log.warning("%s Template failed"%self._str_reportStart)
		return False
	    return True  
    return fncWrap(*args,**kws).go()
   
def deleteTemplate(*args,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "deleteTemplate('%s')"%self._str_moduleName	
	    self.__dataBind__(*args,**kws)		    
	    #=================================================================
	def __func__(self,*args,**kws):
	    mi_module = self.mi_module
	    kws = self.d_kws
	    
	    objList = returnTemplateObjects(*args,**kws)
	    if objList:
		mc.delete(objList)
	    for obj in mi_module.templateNull.getChildren():
		mc.delete(obj)
	    return True	    
    return fncWrap(*args,**kws).go()
 
def returnTemplateObjects(*args,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "returnTemplateObjects('%s')"%self._str_moduleName	
	    self.__dataBind__(*args,**kws)		    
	    #=================================================================
	def __func__(self,*args,**kws):
	    mi_module = self.mi_module
	    kws = self.d_kws
	    
	    templateNull = mi_module.templateNull.getShortName()
	    returnList = []
	    for obj in mc.ls(type = 'transform'):
		if attributes.doGetAttr(obj,'templateOwner') == templateNull:
		    returnList.append(obj)
	    return returnList
    return fncWrap(*args,**kws).go()
#=====================================================================================================
#>>> Skeleton
#=====================================================================================================
def get_rollJointCountList(*args,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "get_rollJointCountList('%s')"%self._str_moduleName	
	    self.__dataBind__(*args,**kws)		    
	    #=================================================================
	def __func__(self,*args,**kws):
	    mi_module = self.mi_module
	    kws = self.d_kws
	    
	    int_rollJoints = mi_module.templateNull.rollJoints
	    d_rollJointOverride = mi_module.templateNull.rollOverride
	    if type(d_rollJointOverride) is not dict:d_rollJointOverride = {}
	    
	    l_segmentRollCount = [int_rollJoints for i in range(mi_module.templateNull.handles-1)]
		
	    if d_rollJointOverride:
		for k in d_rollJointOverride.keys():
		    try:
			l_segmentRollCount[int(k)]#If the arg passes
			l_segmentRollCount[int(k)] = d_rollJointOverride.get(k)#Override the roll value
		    except:log.warning("%s:%s rollOverride arg failed"%(k,d_rollJointOverride.get(k)))
	    log.debug("%s %s"%(self._str_reportStart,l_segmentRollCount))
	    return l_segmentRollCount
    return fncWrap(*args,**kws).go()

def isSkeletonized(*args,**kws):
    """
    Return if a module is skeletonized or not
    """    
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "isSkeletonized('%s')"%self._str_moduleName	
	    self.__dataBind__(*args,**kws)		    
	    #=================================================================
	def __func__(self,*args,**kws):
	    mi_module = self.mi_module
	    kws = self.d_kws
	    
	    l_moduleJoints = mi_module.rigNull.msgList_get('moduleJoints',asMeta=False)
	    if not l_moduleJoints:
		log.debug("No skin joints found")
		return False  
	    
	    #>>> How many joints should we have 
	    goodCount = returnExpectedJointCount(*args,**kws)
	    currentCount = len(l_moduleJoints)
	    if  currentCount < (goodCount-1):
		log.warning("%s Expected at least %s joints. %s found"%(self._str_reportStart,goodCount-1,currentCount))
		return False
	    return True
    return fncWrap(*args,**kws).go()

def doSkeletonize(*args,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "doSkeletonize('%s')"%self._str_moduleName	
	    self.log_info("here")
	    self.__dataBind__(*args,**kws)	
	    self.log_info("here")	    
	    #=================================================================
	def __func__(self,*args,**kws):
	    mi_module = self.mi_module
	    kws = self.d_kws
	    
	    if not isTemplated(*args,**kws):
		log.warning("%s Not templated, can't skeletonize"%self._str_reportStart)
		return False      
	    jFactory.go(*args,**kws)      
	    if not isSkeletonized(*args,**kws):
		log.warning("%s Skeleton build failed"%self._str_reportStart)
		return False
	    return True
    return fncWrap(*args,**kws).go()

def deleteSkeleton(*args,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "deleteSkeleton('%s')"%self._str_moduleName	
	    self.__dataBind__(*args,**kws)		    
	    #=================================================================
	def __func__(self,*args,**kws):
	    mi_module = self.mi_module
	    kws = self.d_kws
	    if isSkeletonized(*args,**kws):
		jFactory.deleteSkeleton(mi_module, *args,**kws)
	    return True
    return fncWrap(*args,**kws).go()
       

def returnExpectedJointCount(*args,**kws):
    """
    Function to figure out how many joints we should have on a module for the purpose of isSkeletonized check
    """    
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "returnExpectedJointCount('%s')"%self._str_moduleName	
	    self.__dataBind__(*args,**kws)		    
	    #=================================================================
	def __func__(self,*args,**kws):
	    mi_module = self.mi_module
	    kws = self.d_kws
	    
	    handles = mi_module.templateNull.handles
	    if handles == 0:
		log.warning("%s Can't count expected joints. 0 handles: '%s'"%self._str_reportStart)
		return False
	    
	    if mi_module.templateNull.getAttr('rollJoints'):
		rollJoints = mi_module.templateNull.rollJoints 
		d_rollJointOverride = mi_module.templateNull.rollOverride 
		
		l_spanDivs = []
		for i in range(0,handles-1):
		    l_spanDivs.append(rollJoints)    
		log.debug("l_spanDivs before append: %s"%l_spanDivs)
	    
		if type(d_rollJointOverride) is dict:
		    for k in d_rollJointOverride.keys():
			try:
			    l_spanDivs[int(k)]#If the arg passes
			    l_spanDivs[int(k)] = d_rollJointOverride.get(k)#Override the roll value
			except:log.warning("%s %s:%s rollOverride arg failed"%(self._str_reportStart,k,d_rollJointOverride.get(k)))    
		log.debug("l_spanDivs: %s"%l_spanDivs)
		int_count = 0
		for i,n in enumerate(l_spanDivs):
		    int_count +=1
		    int_count +=n
		int_count+=1#add the last handle back
		return int_count
	    else:
		return mi_module.templateNull.handles
    return fncWrap(*args,**kws).go()

#=====================================================================================================
#>>> States
#=====================================================================================================   
def validateStateArg(*args,**kws):
    class fncWrap(cgmGeneral.cgmFuncCls):
	def __init__(self,*args,**kws):
	    """
	    """
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "validateStateArg"	
	    self._l_ARGS_KWS_DEFAULTS = [{'kw':'stateArg',"default":None,'help':"Needs to be a valid cgm module state","argType":"string/int"}] 	
	    self.__dataBind__(*args,**kws)		    
	    #=================================================================
	    
	def __func__(self,*args,**kws):
	    stateArg = self.d_kws['stateArg']
	    
	    #>>> Validate argument
	    if type(stateArg) in [str,unicode]:
		stateArg = stateArg.lower()
		if stateArg in l_moduleStates:
		    stateIndex = l_moduleStates.index(stateArg)
		    stateName = stateArg
		else:
		    log.warning("Bad stateArg: %s"%stateArg)
		    return False
	    elif type(stateArg) is int:
		if stateArg<= len(l_moduleStates):
		    stateIndex = stateArg
		    stateName = l_moduleStates[stateArg]         
		else:
		    log.warning("Bad stateArg: %s"%stateArg)
		    return False        
	    else:
		log.warning("Bad stateArg: %s"%stateArg)
		return False
	    return [stateIndex,stateName]
	    
    return fncWrap(*args,**kws).go()    

def isModule(*args,**kws):
    class fncWrap(cgmGeneral.cgmFuncCls):
	def __init__(self,*args,**kws):
	    super(fncWrap, self).__init__(*args,**kws)
	    self._str_funcHelp = "Simple module check"	
	    self._str_funcName = "isModule"
	    self._l_ARGS_KWS_DEFAULTS = [_d_moduleKWARG]	    
	    self.__dataBind__(*args,**kws)
	    self.l_funcSteps = [{'step':'Gather Info','call':self._query_},
	                        {'step':'process','call':self._process_}]

	def _query_(self):
	    try:self._str_moduleName = self.d_kws['mModule'].p_nameShort	
	    except:raise StandardError,"[mi_module : %s]{Not an cgmNode, can't be a module!} "%(self.d_kws['mModule'])
	    self._str_funcName = "isModule('%s')"%self._str_moduleName	
	    self.__updateFuncStrings__()
	    
	def _process_(self):
	    mi_module = self.d_kws['mModule']
	    if not mi_module.hasAttr('mClass'):
		self.log_error("Has no 'mClass'")
		return False
	    if mi_module.mClass not in __l_modulesClasses__:
		self.log_error("Class not a known module type: '%s'"%mi_module.mClass)
		return False  
	    return True
    return fncWrap(*args,**kws).go()

def getState(*args,**kws):
    """ 
    Check module state ONLY from the state check attributes
    
    RETURNS:
    state(int) -- indexed to ModuleFactory.l_moduleStates
    
    Possible states:
    define
    sized
    templated
    skeletonized
    rigged
    """    
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "getState('%s')"%self._str_moduleName	
	    self.__dataBind__(*args,**kws)		    
	    #=================================================================
	def __func__(self,*args,**kws):
	    mi_module = self.mi_module
	    kws = self.d_kws
	    d_CheckList = {'size':isSized,
	                   'template':isTemplated,
	                   'skeleton':isSkeletonized,
	                   'rig':isRigged,
	                   }
	    goodState = 0
	    l_moduleStatesReverse = copy.copy(l_moduleStates)
	    l_moduleStatesReverse.reverse()
	    for i,state in enumerate(l_moduleStatesReverse):
		log.debug("Checking: %s"%state)	
		if state in d_CheckList.keys():
		    if d_CheckList[state](*args,**kws):
			log.debug("good: %s"%state)
			goodState = l_moduleStates.index(state)
			break
		else:
		    goodState = 0
	    log.debug("'%s' state: %s | '%s'"%(mi_module.getShortName(),goodState,l_moduleStates[goodState]))
	    return goodState
    return fncWrap(*args,**kws).go()
'''
def SampleFunc(*args,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "testFunc('%s')"%self._str_moduleName	
	    
	    self._l_ARGS_KWS_DEFAULTS.extend( [{'kw':'FILLIN',"default":None,'help':"FILLIN","argType":"FILLIN"}] )		
	    self.__dataBind__(*args,**kws)	
	    self.l_funcSteps = [{'step':'Get Data','call':self.__func__}]
	    
	    #=================================================================
	    
	def __func__(self,*args,**kws):
	    """
	    """
	    mi_module = self.mi_module
	    kws = self.d_kws
	    
    return fncWrap(*args,**kws).go()
'''
def setState(*args,**kws):
    """ 
    Set a module's state
    
    @rebuild -- force it to rebuild each step
    TODO:
    Make template info be stored when leaving
    """    
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "setState('%s')"%self._str_moduleName	
	    
	    self._l_ARGS_KWS_DEFAULTS.extend( [{'kw':'stateArg',"default":None,'help':"What state is desired","argType":"int/string"},
	                                       {'kw':'rebuildFrom',"default":None,'help':"State to rebuild from","argType":"int/string"}] )		
	    self.__dataBind__(*args,**kws)		    
	    #=================================================================
	def __func__(self,*args,**kws):
	    """
	    """
	    mi_module = self.mi_module
	    kws = self.d_kws
	    rebuildFrom = kws['rebuildFrom']
	    
	    if rebuildFrom is not None:
		rebuildArgs = validateStateArg(rebuildFrom,**kws)
		if rebuildArgs:
		    log.debug("'%s' rebuilding from: '%s'"%(mi_module.getShortName(),rebuildArgs[1]))
		    changeState(self.mi_module,rebuildArgs[1],**kws)
	    changeState(*args,**kws)	
	    return True
    return fncWrap(*args,**kws).go()

def checkState(*args,**kws):
    """ 
    Set a module's state
    
    @rebuild -- force it to rebuild each step
    TODO:
    Make template info be stored when leaving
    """    
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "checkState('%s')"%self._str_moduleName	
	    
	    self._l_ARGS_KWS_DEFAULTS.extend( [{'kw':'stateArg',"default":None,'help':"What state is desired","argType":"int/string"},
	                                       ] )		
	    self.__dataBind__(*args,**kws)		    
	    #=================================================================    
	def __func__(self,*args,**kws):
	    """
	    """
	    mi_module = self.mi_module
	    kws = self.d_kws
	    stateArg = kws['stateArg']
	    
	    l_stateArg = validateStateArg(stateArg)
	    if not l_stateArg:raise StandardError,"Couldn't find valid state"
	    
	    if getState(self,*args,**kws) > l_stateArg[0]:
		return True
		
	    changeState(self,stateArg,*args,**kws)
	    return True
    return fncWrap(*args,**kws).go()
    
def changeState(*args,**kws):
    """ 
    Changes a module state
    
    TODO:
    Make template info be stored skeleton builds
    Make template builder read and use pose data stored
    """    
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """
	    super(fncWrap, self).__init__(*args, **kws)
	    self._str_funcName= "changeState('%s')"%self._str_moduleName	
	    
	    self._l_ARGS_KWS_DEFAULTS.extend( [{'kw':'stateArg',"default":None,'help':"What state is desired","argType":"int/string"},
	                                       {'kw':'rebuildFrom',"default":None,'help':"State to rebuild from","argType":"int/string"},
	                                       {'kw':'forceNew',"default":False,'help':"typical kw ","argType":"bool"}] )		
	    self.__dataBind__(*args,**kws)	    
	    #=================================================================
	    
	def __func__(self,*args,**kws):
	    """
	    """
	    mi_module = self.mi_module
	    kws = self.d_kws
	    stateArg = kws['stateArg']
	    rebuildFrom = kws['rebuildFrom']
	    forceNew = kws['forceNew']
    
	    d_upStateFunctions = {'size':doSize,
		                   'template':doTemplate,
		                   'skeleton':doSkeletonize,
		                   'rig':doRig,
		                   }
	    d_downStateFunctions = {'define':deleteSizeInfo,
		                    'size':deleteTemplate,
		                    'template':deleteSkeleton,
		                    'skeleton':rigDelete,
		                    }
	    d_deleteStateFunctions = {'size':deleteSizeInfo,
		                      'template':deleteTemplate,#handle from factory now
		                      'skeleton':deleteSkeleton,
		                      'rig':rigDelete,
		                      }    

	    stateArgs = validateStateArg(stateArg,**kws)
	    if not stateArgs:
		log.warning("Bad stateArg from changeState: %s"%stateArg)
		return False
	    
	    stateIndex = stateArgs[0]
	    stateName = stateArgs[1]
	    
	    log.debug("stateIndex: %s | stateName: '%s'"%(stateIndex,stateName))
	    
	    #>>> Meat
	    #========================================================================
	    currentState = getState(*args,**kws) 
	    if currentState == stateIndex and rebuildFrom is None and not forceNew:
		if not forceNew:log.warning("'%s' already has state: %s"%(mi_module.getShortName(),stateName))
		return True
	    #If we're here, we're going to move through the set states till we get to our spot
	    log.debug("Changing states now...")
	    if stateIndex > currentState:
		startState = currentState+1        
		log.debug(' up stating...')        
		log.debug("Starting doState: '%s'"%l_moduleStates[startState])
		doStates = l_moduleStates[startState:stateIndex+1]
		log.debug("doStates: %s"%doStates)        
		for doState in doStates:
		    if doState in d_upStateFunctions.keys():
			if not d_upStateFunctions[doState](self.mi_module,*args,**kws):return False
			else:
			    log.debug("'%s' completed: %s"%(mi_module.getShortName(),doState))
		    else:
			log.warning("No up state function for: %s"%doState)
	    elif stateIndex < currentState:#Going down
		log.debug('down stating...')        
		l_reverseModuleStates = copy.copy(l_moduleStates)
		l_reverseModuleStates.reverse()
		startState = currentState      
		log.debug(' up stating...')     
		log.debug("l_reverseModuleStates: %s"%l_reverseModuleStates)
		log.debug("Starting downState: '%s'"%l_moduleStates[startState])
		rev_start = l_reverseModuleStates.index( l_moduleStates[startState] )+1
		rev_end = l_reverseModuleStates.index( l_moduleStates[stateIndex] )+1
		doStates = l_reverseModuleStates[rev_start:rev_end]
		log.debug("toDo: %s"%doStates)
		
		for doState in doStates:
		    log.debug("doState: %s"%doState)
		    if doState in d_downStateFunctions.keys():
			if not d_downStateFunctions[doState](self.mi_module,*args,**kws):return False
			else:log.debug("'%s': %s"%(mi_module.getShortName(),doState))
		    else:
			log.warning("No down state function for: %s"%doState)  
	    else:
		log.debug('Forcing recreate')
		if stateName in d_upStateFunctions.keys():
		    if not d_upStateFunctions[stateName](self.mi_module,*args,**kws):return False
		    return True
		    
    return fncWrap(*args,**kws).go()

def storePose_templateSettings(self):
    """
    Builds a template's data settings for reconstruction.
    
    exampleDict = {'root':{'test':[0,1,0]},
                'controlObjects':{0:[1,1,1]}}
    """  
    _str_funcName = "storePose_templateSettings('%s')"%self.p_nameShort  
    log.info(">>> %s "%(_str_funcName) + "="*75)   
    
    if self.getMessage('helper'):
	log.warning(">>> %s | Error: Cannot currently store pose with rigBlocks"%_str_funcName)
	return False
    def buildDict_AnimAttrsOfObject(node,ignore = ['visibility']):
        attrDict = {}
        attrs = r9Anim.getSettableChannels(node,incStatics=True)
        if attrs:
            for attr in attrs:
                if attr not in ignore:
                    try:attrDict[attr]=mc.getAttr('%s.%s' % (node,attr))
                    except:log.debug('%s : attr is invalid in this instance' % attr)
        return attrDict
        
    exampleDict = {'root':{'test':[0,1,0]},
                   'orientRootHelper':{'test':[0,1,0]},
                   'controlObjects':{0:[1,1,1]},
                   'helperObjects':{0:[]}}    
    try:
	poseDict = {}
	i_templateNull = self.templateNull
	i_templateNull.addAttr('controlObjectTemplatePose',attrType = 'string')#make sure attr exists
	#>>> Get the root
	poseDict['root'] = buildDict_AnimAttrsOfObject(i_templateNull.getMessage('root')[0])
	poseDict['orientRootHelper'] = buildDict_AnimAttrsOfObject(i_templateNull.getMessage('orientRootHelper')[0])
	poseDict['controlObjects'] = {}
	poseDict['helperObjects'] = {}
	
	for i,i_node in enumerate(i_templateNull.controlObjects):
	    poseDict['controlObjects'][str(i)] = buildDict_AnimAttrsOfObject(i_node.mNode)
	    if i_node.getMessage('helper'):
		poseDict['helperObjects'][str(i)] = buildDict_AnimAttrsOfObject(i_node.helper.mNode)
	
	#Store it        
	i_templateNull.controlObjectTemplatePose = poseDict
	return poseDict
    except Exception,error:
	raise StandardError,"%s >> %s"%(_str_funcName,error)    

def readPose_templateSettings(self):
    """
    Builds a template's data settings for reconstruction.
    
    exampleDict = {'root':{'test':[0,1,0]},
                'controlObjects':{0:[1,1,1]}}
    """   
    _str_funcName = "getState('%s')"%self.p_nameShort   
    log.debug(">>> %s "%(_str_funcName) + "="*75)       
    try:
	i_templateNull = self.templateNull    
	poseDict = i_templateNull.controlObjectTemplatePose
	if type(poseDict) is not dict:
	    return False
	
	#>>> Get the root
	for key in ['root','orientRootHelper']:
	    if poseDict[key]:
		for attr, val in poseDict[key].items():
		    try:
			val=eval(val)
		    except:pass      
		    try:
			mc.setAttr('%s.%s' % (i_templateNull.getMessage(key)[0],attr), val)
		    except Exception,err:
			log.error(err)   
			
	for key in poseDict['controlObjects']:
	    for attr, val in poseDict['controlObjects'][key].items():
		try:
		    val=eval(val)
		except:pass      
	    
		try:
		    mc.setAttr('%s.%s' % (i_templateNull.getMessage('controlObjects')[int(key)], attr), val)
		except Exception,err:
		    log.error(err) 
		    
	for key in poseDict['helperObjects']:
	    for attr, val in poseDict['helperObjects'][key].items():
		try:
		    val=eval(val)
		except:pass      
	    
		try:
		    if i_templateNull.controlObjects[int(key)].getMessage('helper'):
			log.debug(i_templateNull.controlObjects[int(key)].getMessage('helper')[0])
			mc.setAttr('%s.%s' % (i_templateNull.controlObjects[int(key)].getMessage('helper')[0], attr), val)
		except Exception,err:
		    log.error(err)    
		    
	return True
    except Exception,error:
	raise StandardError,"%s >> %s"%(_str_funcName,error)   
    
#=====================================================================================================
#>>> Anim functions functions
#=====================================================================================================
def get_mirror(*args,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,goInstance = None):
	    """
	    """	
	    super(fncWrap, self).__init__(*args,**kws)
	    self._str_funcName = "get_mirror('%s')"%self._str_moduleName
	    self.__dataBind__(*args,**kws)
	    self.l_funcSteps = [{'step':'Process','call':self.__func__}]
	    #The idea is to register the functions needed to be called
	    #=================================================================
	def __func__(self): 
	    mi_module = self.mi_module
	    l_direction = ['left','right']
	    if mi_module.getAttr('cgmDirection') not in l_direction:
		log.debug("Module doesn't have direction")
		return False
	    int_direction = l_direction.index(mi_module.cgmDirection)
	    d = {'cgmName':mi_module.cgmName,'moduleType':mi_module.moduleType,'cgmDirection':l_direction[not int_direction]}
	    return mi_module.modulePuppet.getModuleFromDict(d)	 
    return fncWrap(*args,**kws).go()  
    
def animReset(self,transformsOnly = True):
    _str_funcName = "%s.animReset()"%self.p_nameShort  
    log.debug(">>> %s "%(_str_funcName) + "="*75)  		
    try:
	self.rigNull.moduleSet.select()
	if mc.ls(sl=True):
	    ml_resetChannels.main(transformsOnly = transformsOnly)
	    return True
	return False
    except Exception,error:
	log.error("%s >> error: %s"%(_str_funcName,error))
	return False
    
def mirrorPush(*args,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """	
	    super(fncWrap, self).__init__(*args,**kws)
	    self._str_funcName = "mirrorPush('%s')"%self._str_moduleName
	    self.__dataBind__(*args,**kws)
	    self.l_funcSteps = [{'step':'Process','call':self.__func__}]
	    #=================================================================
	def __func__(self): 
	    mi_module = self.mi_module
	    l_buffer = mi_module.rigNull.moduleSet.getList()
	    mi_mirror = get_mirror(mi_module)
	    if mi_mirror:
		l_buffer.extend(mi_mirror.rigNull.moduleSet.getList())
	    else:raise StandardError, "Module doesn't have mirror"
	    
	    if l_buffer:
		r9Anim.MirrorHierarchy(l_buffer).makeSymmetrical(mode = '',primeAxis = mi_module.cgmDirection.capitalize() )
		mc.select(l_buffer)
		return True
	    return False	 
	
    return fncWrap(*args,**kws).go()   
        
def mirrorPull(*args,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """	
	    super(fncWrap, self).__init__(*args,**kws)
	    self._str_funcName = "mirrorPull('%s')"%self._str_moduleName
	    self.__dataBind__(*args,**kws)
	    self.l_funcSteps = [{'step':'Process','call':self.__func__}]
	    #The idea is to register the functions needed to be called
	    #=================================================================
	    
	def __func__(self): 
	    mi_module = self.mi_module
	    l_buffer = mi_module.rigNull.moduleSet.getList()
	    mi_mirror = get_mirror(mi_module)
	    if mi_mirror:
		l_buffer.extend(mi_mirror.rigNull.moduleSet.getList())
	    else:raise StandardError, "Module doesn't have mirror"
	    
	    if l_buffer:
		r9Anim.MirrorHierarchy(l_buffer).makeSymmetrical(mode = '',primeAxis = mi_mirror.cgmDirection.capitalize() )
		mc.select(l_buffer)
		return True
	    return False	 
	
    return fncWrap(*args,**kws).go()
     
def mirrorMe(*args,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """	
	    super(fncWrap, self).__init__(*args,**kws)
	    self._str_funcName = "mirrorMe('%s')"%self._str_moduleName
	    self.__dataBind__(*args,**kws)
	    #The idea is to register the functions needed to be called
	    #=================================================================
	def __func__(self): 
	    mi_module = self.mi_module
	    l_buffer = mi_module.rigNull.moduleSet.getList()
	    try:mi_mirror = get_mirror(mi_module)
	    except Exception,error:raise StandardError,"get_mirror | %s"%error
	    if mi_mirror:
		l_buffer.extend(mi_mirror.rigNull.moduleSet.getList())
	    if l_buffer:
		r9Anim.MirrorHierarchy(l_buffer).mirrorData(mode = '')
		mc.select(l_buffer)
		return True
	    return False  
	
    return fncWrap(*args,**kws).go()

def mirrorSymLeft(*args,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """	
	    super(fncWrap, self).__init__(*args,**kws)
	    self._str_funcName = "mirrorSymLeft('%s')"%self._str_moduleName
	    self.__dataBind__(*args,**kws)
	    #=================================================================
	def __func__(self): 
	    mi_module = self.mi_module
	    l_buffer = mi_module.rigNull.moduleSet.getList()
	    if l_buffer:
		r9Anim.MirrorHierarchy(l_buffer).makeSymmetrical(mode = '',primeAxis = "Left" )
		mc.select(l_buffer)
		return True
	    return False	 
    return fncWrap(*args,**kws).go() 
def mirrorSymRight(*args,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,*args,**kws):
	    """
	    """	
	    super(fncWrap, self).__init__(*args,**kws)
	    self._str_funcName = "mirrorSymRight('%s')"%self._str_moduleName
	    self.__dataBind__(*args,**kws)
	    #=================================================================
	def __func__(self): 
	    mi_module = self.mi_module
	    l_buffer = mi_module.rigNull.moduleSet.getList()
	    if l_buffer:
		r9Anim.MirrorHierarchy(l_buffer).makeSymmetrical(mode = '',primeAxis = "Right" )
		mc.select(l_buffer)
		return True
	    return False	 
    return fncWrap(*args,**kws).go() 
#=====================================================================================================
#>>> Sibling functions
#=====================================================================================================  
def mirrorMe_siblings(moduleInstance = None, excludeSelf = True):
    class fncWrap(ModuleFunc):
	def __init__(self,goInstance = None, excludeSelf = True):
	    """
	    """	
	    super(fncWrap, self).__init__(moduleInstance)
	    self._str_funcName = "mirrorMe_siblings('%s')"%self._str_moduleName
	    self.__dataBind__()
	    self.d_kws['excludeSelf'] = excludeSelf	    	    
	    self.l_funcSteps = [{'step':'Process','call':self.__func__}]
	    #The idea is to register the functions needed to be called
	    #=================================================================
	    
	def __func__(self): 
	    try:
		mi_moduleParent = self.mi_module.moduleParent
		mi_parentMirror = get_mirror(mi_moduleParent)
		if not mi_moduleParent and mi_parentMirror:
		    raise StandardError,"Must have module parent and mirror"
		ml_buffer = getAllModuleChildren(mi_moduleParent)
		ml_buffer.extend(getAllModuleChildren(mi_parentMirror))
		
		mayaMainProgressBar = cgmGeneral.doStartMayaProgressBar(len(ml_buffer))  
		l_controls = []
		for i,mModule in enumerate(ml_buffer):
		    try:
			mc.progressBar(mayaMainProgressBar, edit=True, status = "%s >> step:'%s' "%(self._str_reportStart,mModule.p_nameShort), progress=i)    				        			
			l_controls.extend(mModule.rigNull.moduleSet.getList())			
		    except Exception,error:
			log.error("%s  child: %s | %s"%(self._str_reportStart,i_c.getShortName(),error))
		cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar 
		if l_controls:
		    r9Anim.MirrorHierarchy(l_controls).mirrorData(mode = '')		    
		    mc.select(l_controls)
		
	    except Exception,error:
		try:cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar        	
		except:
		    raise StandardError,error
		
	    return False  
	
    #We wrap it so that it autoruns and returns
    return fncWrap(moduleInstance,excludeSelf).go()

def animReset_siblings(moduleInstance = None, transformsOnly = True, excludeSelf = True):
    class fncWrap(ModuleFunc):
	def __init__(self,goInstance = None,  transformsOnly = True, excludeSelf = True):
	    """
	    """	
	    super(fncWrap, self).__init__(moduleInstance)
	    self._str_funcName = "animReset_siblings('%s')"%self._str_moduleName
	    self.__dataBind__()
	    self.d_kws['excludeSelf'] = excludeSelf	  
	    self.d_kws['transformsOnly'] = transformsOnly	    	    	    
	    self.l_funcSteps = [{'step':'Process','call':self.__func__}]
	    #The idea is to register the functions needed to be called
	    #=================================================================
	    
	def __func__(self): 
	    try:
		ml_buffer = getSiblings(self.mi_module,self.d_kws['excludeSelf'])
		
		mayaMainProgressBar = cgmGeneral.doStartMayaProgressBar(len(ml_buffer))  
		l_controls = []
		for i,mModule in enumerate(ml_buffer):
		    try:
			mc.progressBar(mayaMainProgressBar, edit=True, status = "%s >> step:'%s' "%(self._str_reportStart,mModule.p_nameShort), progress=i)    				        			
			l_controls.extend(mModule.rigNull.moduleSet.getList())			
		    except Exception,error:
			log.error("%s  child: %s | %s"%(self._str_reportStart,i_c.getShortName(),error))
		cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar 
		if l_controls:
		    mc.select(l_controls)
		    ml_resetChannels.main(transformsOnly = self.d_kws['transformsOnly'])
		    return True
		return False
		
	    except Exception,error:
		try:cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar        	
		except:
		    raise StandardError,error
	    return False  
	
    #We wrap it so that it autoruns and returns
    return fncWrap(moduleInstance,transformsOnly,excludeSelf).go()

def animReset_children(moduleInstance = None, transformsOnly = True, excludeSelf = True):
    class fncWrap(ModuleFunc):
	def __init__(self,goInstance = None,  transformsOnly = True, excludeSelf = True):
	    """
	    """	
	    super(fncWrap, self).__init__(moduleInstance)
	    self._str_funcName = "animReset_siblings('%s')"%self._str_moduleName
	    self.__dataBind__()
	    self.d_kws['excludeSelf'] = excludeSelf	  
	    self.d_kws['transformsOnly'] = transformsOnly	    	    	    
	    self.l_funcSteps = [{'step':'Process','call':self.__func__}]
	    #The idea is to register the functions needed to be called
	    #=================================================================
	    
	def __func__(self): 
	    try:
		ml_buffer = getAllModuleChildren(self.mi_module,self.d_kws['excludeSelf'])
		mayaMainProgressBar = cgmGeneral.doStartMayaProgressBar(len(ml_buffer))  
		l_controls = []
		for i,mModule in enumerate(ml_buffer):
		    try:
			mc.progressBar(mayaMainProgressBar, edit=True, status = "%s >> step:'%s' "%(self._str_reportStart,mModule.p_nameShort), progress=i)    				        			
			l_controls.extend(mModule.rigNull.moduleSet.getList())			
		    except Exception,error:
			log.error("%s  child: %s | %s"%(self._str_reportStart,i_c.getShortName(),error))
		cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar 
		if l_controls:
		    mc.select(l_controls)
		    ml_resetChannels.main(transformsOnly = self.d_kws['transformsOnly'])
		    return True
		return False
		
	    except Exception,error:
		try:cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar        	
		except:
		    raise StandardError,error
	    return False  
	
    #We wrap it so that it autoruns and returns
    return fncWrap(moduleInstance,transformsOnly,excludeSelf).go()

def mirrorPush_siblings(moduleInstance = None, excludeSelf = True):
    class fncWrap(ModuleFunc):
	def __init__(self,goInstance = None, excludeSelf = True):
	    """
	    """	
	    super(fncWrap, self).__init__(moduleInstance)
	    self._str_funcName = "mirrorPush_siblings('%s')"%self._str_moduleName
	    self.__dataBind__()
	    self.d_kws['excludeSelf'] = excludeSelf	    	    
	    self.l_funcSteps = [{'step':'Process','call':self.__func__}]
	    #The idea is to register the functions needed to be called
	    #=================================================================
	    
	def __func__(self): 
	    try:
		ml_buffer = getSiblings(self.mi_module,self.d_kws.get('excludeSelf'))
		mayaMainProgressBar = cgmGeneral.doStartMayaProgressBar(len(ml_buffer))  
		l_controls = []
		for i,i_c in enumerate(ml_buffer):
		    try:
			mc.progressBar(mayaMainProgressBar, edit=True, status = "%s >> step:'%s' "%(self._str_reportStart,i_c.p_nameShort), progress=i)    				        			
			mirrorPush(i_c)
			l_controls.extend(i_c.rigNull.moduleSet.getList())			
		    except Exception,error:
			log.error("%s  child: %s | %s"%(self._str_reportStart,i_c.getShortName(),error))
		cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar 
		if l_controls:mc.select(l_controls)
	    except Exception,error:
		try:cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar        	
		except:
		    raise StandardError,error
	    return False  
	
    #We wrap it so that it autoruns and returns
    return fncWrap(moduleInstance,excludeSelf).go()   

def mirrorPull_siblings(moduleInstance = None, excludeSelf = True):
    class fncWrap(ModuleFunc):
	def __init__(self,goInstance = None, excludeSelf = True):
	    """
	    """	
	    super(fncWrap, self).__init__(moduleInstance)
	    self._str_funcName = "mirrorPull_siblings('%s')"%self._str_moduleName
	    self.__dataBind__()
	    self.d_kws['excludeSelf'] = excludeSelf	    	    
	    self.l_funcSteps = [{'step':'Process','call':self.__func__}]
	    #The idea is to register the functions needed to be called
	    #=================================================================
	    
	def __func__(self): 
	    try:
		ml_buffer = getSiblings(self.mi_module,self.d_kws.get('excludeSelf'))
		mayaMainProgressBar = cgmGeneral.doStartMayaProgressBar(len(ml_buffer))  
		l_controls = []
		for i,i_c in enumerate(ml_buffer):
		    try:
			mc.progressBar(mayaMainProgressBar, edit=True, status = "%s >> step:'%s' "%(self._str_reportStart,i_c.p_nameShort), progress=i)    				        			
			mirrorPull(i_c)
			l_controls.extend(i_c.rigNull.moduleSet.getList())
		    except Exception,error:
			log.error("%s  child: %s | %s"%(self._str_reportStart,i_c.getShortName(),error))
		cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar 
		
		if l_controls:mc.select(l_controls)
		
	    except Exception,error:
		try:cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar        	
		except:
		    raise StandardError,error
	    return False  
	
    #We wrap it so that it autoruns and returns
    return fncWrap(moduleInstance,excludeSelf).go()  

def getSiblings(moduleInstance = None, excludeSelf = True):
    l_sibblingIgnoreCheck = ['finger','thumb']
    class fncWrap(ModuleFunc):
	def __init__(self,goInstance = None, excludeSelf = True):
	    """
	    """	
	    super(fncWrap, self).__init__(moduleInstance)
	    self._str_funcName = "getSiblings('%s')"%self._str_moduleName
	    self.__dataBind__()
	    self.d_kws['excludeSelf'] = excludeSelf	    	    
	    self.l_funcSteps = [{'step':'Process','call':self.__func__}]
	    #The idea is to register the functions needed to be called
	    #=================================================================
	    
	def __func__(self):
	    ml_buffer = copy.copy(self.mi_module.moduleParent.moduleChildren)
	    ml_return = []
	    for i,m in enumerate(ml_buffer):
		if m.mNode == self.mi_module.mNode and not self.d_kws['excludeSelf']:
		    ml_return.append(self.mi_module)
		if self.mi_module.moduleType == m.moduleType or self.mi_module.moduleType in l_sibblingIgnoreCheck:
		    if self.mi_module.getAttr('cgmDirection') and self.mi_module.getAttr('cgmDirection') == m.getAttr('cgmDirection'):
			ml_return.append(m)
	    if len(ml_return)>1: return ml_return
	    return []

    #We wrap it so that it autoruns and returns
    return fncWrap(moduleInstance,excludeSelf).go()

#=====================================================================================================
#>>> Children functions
#=====================================================================================================  
def getAllModuleChildren(moduleInstance = None,excludeSelf = True):
    class fncWrap(ModuleFunc):
	def __init__(self,goInstance = None,excludeSelf = True):
	    """
	    """	
	    super(fncWrap, self).__init__(moduleInstance)
	    self._str_funcName = "getAllModuleChildren('%s')"%self._str_moduleName
	    self.__dataBind__()
	    self.d_kws['excludeSelf'] = excludeSelf	    	    	    
	    self.l_funcSteps = [{'step':'Process','call':self.__func__}]
	    #The idea is to register the functions needed to be called
	    #=================================================================
	    
	def __func__(self): 
	    try:
		ml_children = []
		ml_childrenCull = copy.copy(self.mi_module.moduleChildren)
			       
		cnt = 0
		#Process the childdren looking for parents as children and so on and so forth, appending them as it finds them
		while len(ml_childrenCull)>0 and cnt < 100:#While we still have a cull list
		    cnt+=1                        
		    if cnt == 99:
			raise StandardError,"Max count reached"
		    for i_child in ml_childrenCull:
			if i_child not in ml_children:
			    ml_children.append(i_child)
			for i_subChild in i_child.moduleChildren:
			    ml_childrenCull.append(i_subChild)
			ml_childrenCull.remove(i_child) 
			
		if not self.d_kws['excludeSelf']:
		    ml_children.append(self.mi_module)		
		return ml_children
		
	    except Exception,error:
		try:cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar        	
		except:raise StandardError,error
	    return False  
    #We wrap it so that it autoruns and returns
    return fncWrap(moduleInstance,excludeSelf).go()    

def animKey_children(self,**kws):
    """
    Key module and all module children controls
    """   
    _str_funcName = "animKey_children('%s')"%self.p_nameShort   
    log.debug(">>> %s "%(_str_funcName) + "="*75)         
    try:
	l_controls = self.rigNull.msgList_getMessage('controlsAll') or []
	ml_children = getAllModuleChildren(self)
	if ml_children:mayaMainProgressBar = cgmGeneral.doStartMayaProgressBar(len(ml_children)) 
	for i,i_c in enumerate(ml_children):
	    mc.progressBar(mayaMainProgressBar, edit=True, status = "%s.animKey_children>> gathering controls:'%s' "%(self.p_nameShort,i_c.p_nameShort), progress=i)    				        				    
	    buffer = i_c.rigNull.msgList_getMessage('controlsAll')
	    if buffer:
		l_controls.extend(buffer)
		
	if ml_children:
	    try:cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar        	
	    except:pass	   
	    
	if l_controls:
	    mc.select(l_controls)
	    mc.setKeyframe(**kws)
	    return True
	return False
    except Exception,error:
	raise StandardError,"%s >> %s"%(_str_funcName,error)   
    
def animKey_siblings(moduleInstance = None, excludeSelf = True,**kws):
    class fncWrap(ModuleFunc):
	def __init__(self,goInstance = None, excludeSelf = True,**kws):
	    """
	    """	
	    super(fncWrap, self).__init__(moduleInstance)
	    self._str_funcName = "animKey_siblings('%s')"%self._str_moduleName
	    self.__dataBind__()
	    self.d_kws['excludeSelf'] = excludeSelf	    	    
	    self.l_funcSteps = [{'step':'Process','call':self.__func__}]
	    #The idea is to register the functions needed to be called
	    #=================================================================
	    
	def __func__(self): 
	    try:
		ml_buffer = getSiblings(self.mi_module,self.d_kws.get('excludeSelf'))
		mayaMainProgressBar = cgmGeneral.doStartMayaProgressBar(len(ml_buffer))  
		l_controls = []
		for i,i_c in enumerate(ml_buffer):
		    log.info(i_c.p_nameShort)
		    try:
			mc.progressBar(mayaMainProgressBar, edit=True, status = "%s.dynSwitch_children>> step:'%s' "%(self._str_moduleName,i_c.p_nameShort), progress=i)    				        			
			l_controls.extend(i_c.rigNull.moduleSet.getList())
		    except Exception,error:
			log.error("%s  child: %s | %s"%(self._str_reportStart,i_c.getShortName(),error))
		cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar 
		if l_controls:
		    mc.select(l_controls)
		    kws = self._d_funcKWs
		    mc.setKeyframe(**kws)
		
	    except Exception,error:
		try:cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar        	
		except:
		    raise StandardError,error
		
	    return False  
    #We wrap it so that it autoruns and returns
    return fncWrap(moduleInstance,excludeSelf,**kws).go() 

def animSelect_children(self,**kws):
    """
    Select module and all module children controls
    """     
    _str_funcName = "animSelect_children('%s')"%self.p_nameShort   
    log.debug(">>> %s "%(_str_funcName) + "="*75)        
    try:
	l_controls = self.rigNull.msgList_getMessage('controlsAll') or []
	ml_children = getAllModuleChildren(self)
	if ml_children:mayaMainProgressBar = cgmGeneral.doStartMayaProgressBar(len(ml_children)) 
	for i,i_c in enumerate(ml_children):
	    mc.progressBar(mayaMainProgressBar, edit=True, status = "%s.animSelect_children>> gathering controls:'%s' "%(self.p_nameShort,i_c.p_nameShort), progress=i)    				        				    
	    buffer = i_c.rigNull.msgList_getMessage('controlsAll')
	    if buffer:
		l_controls.extend(buffer)
		
	if ml_children:
	    try:cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar        	
	    except:pass	   
	
	if l_controls:
	    mc.select(l_controls)
	    return True
	return False
    except Exception,error:
	raise StandardError,"%s >> %s"%(_str_funcName,error) 
    
def animSelect_siblings(moduleInstance = None, excludeSelf = True):
    class fncWrap(ModuleFunc):
	def __init__(self,goInstance = None, excludeSelf = True):
	    """
	    """	
	    super(fncWrap, self).__init__(moduleInstance)
	    self._str_funcName = "animSelect_siblings('%s')"%self._str_moduleName
	    self.__dataBind__()
	    self.d_kws['excludeSelf'] = excludeSelf	    	    
	    self.l_funcSteps = [{'step':'Process','call':self.__func__}]
	    #The idea is to register the functions needed to be called
	    #=================================================================
	    
	def __func__(self): 
	    try:
		ml_buffer = getSiblings(self.mi_module,self.d_kws.get('excludeSelf'))
		mayaMainProgressBar = cgmGeneral.doStartMayaProgressBar(len(ml_buffer))  
		l_controls = []
		for i,i_c in enumerate(ml_buffer):
		    try:
			mc.progressBar(mayaMainProgressBar, edit=True, status = "%s >> step:'%s' "%(self._str_reportStart,i_c.p_nameShort), progress=i)    				        			
			l_controls.extend(i_c.rigNull.moduleSet.getList())
		    except Exception,error:
			log.error("%s  child: %s | %s"%(self._str_reportStart,i_c.getShortName(),error))
		cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar 
		
		if l_controls:
		    mc.select(l_controls)
		    return True	
		
	    except Exception,error:
		try:cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar        	
		except:
		    raise StandardError,error
		
	    return False  
    #We wrap it so that it autoruns and returns
    return fncWrap(moduleInstance,excludeSelf).go()

def animPushPose_siblings(moduleInstance = None,):
    class fncWrap(ModuleFunc):
	def __init__(self,goInstance = None):
	    """
	    """	
	    super(fncWrap, self).__init__(moduleInstance)
	    self._str_funcName = "animPushPose_siblings('%s')"%self._str_moduleName
	    self.__dataBind__()
	    self.l_funcSteps = [{'step':'Process','call':self.__func__}]
	    #The idea is to register the functions needed to be called
	    #=================================================================
	    
	def __func__(self): 
	    try:
		ml_buffer = getSiblings(self.mi_module)
		mayaMainProgressBar = cgmGeneral.doStartMayaProgressBar(len(ml_buffer)) 
		l_moduleControls = self.mi_module.rigNull.msgList_getMessage('controlsAll')
		l_controls = []
		for i,i_c in enumerate(ml_buffer):
		    log.info(i_c.p_nameShort)
		    try:
			mc.progressBar(mayaMainProgressBar, edit=True, status = "%s >> step:'%s' "%(self._str_reportStart,i_c.p_nameShort), progress=i)    				        			
			l_siblingControls = i_c.rigNull.msgList_getMessage('controlsAll')
			for i,c in enumerate(l_siblingControls):
			    log.info("%s %s >> %s"%(self._str_reportStart,l_moduleControls[i],c))
			    r9Anim.AnimFunctions().copyAttributes(nodes=[l_moduleControls[i],c])
			l_controls.extend(l_siblingControls)
		    except Exception,error:
			log.error("%s  child: %s | %s"%(self._str_reportStart,i_c.getShortName(),error))
		cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar 
		
		if l_controls:
		    mc.select(l_controls)
		    return True	
		
	    except Exception,error:
		try:cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar        	
		except:
		    raise StandardError,error
		
	    return False  
    #We wrap it so that it autoruns and returns
    return fncWrap(moduleInstance).go()

def dynSwitch_children(self,arg):
    """
    Key module and all module children
    """  
    _str_funcName = "dynSwitch_children('%s')"%self.p_nameShort   
    log.debug(">>> %s "%(_str_funcName) + "="*75)   
    try:
	try:
	    ml_children = getAllModuleChildren(self)
	    mayaMainProgressBar = cgmGeneral.doStartMayaProgressBar(len(ml_children))    
	    for i,i_c in enumerate(ml_children):
		try:
		    mc.progressBar(mayaMainProgressBar, edit=True, status = "%s.dynSwitch_children>> step:'%s' "%(self.p_nameShort,i_c.p_nameShort), progress=i)    				        			
		    i_c.rigNull.dynSwitch.go(arg)
		except Exception,error:
		    log.error("%s.dynSwitch_children>>  child: %s | %s"%(self.getBaseName(),i_c.getShortName(),error))
	    cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar        	
	except Exception,error:
	    try:cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar        	
	    except:pass
	    log.error("%s.dynSwitch_children>> fail | %s"%(self.getBaseName(),error))
	    return False  
    except Exception,error:
	raise StandardError,"%s >> %s"%(_str_funcName,error) 
    
def dynSwitch_siblings(moduleInstance = None, arg = None, excludeSelf = True):
    class fncWrap(ModuleFunc):
	def __init__(self,goInstance = None, arg = None, excludeSelf = True):
	    """
	    """	
	    super(fncWrap, self).__init__(moduleInstance)
	    self._str_funcName = "dynSwitch_siblings('%s')"%self._str_moduleName
	    self.__dataBind__()
	    self.d_kws['arg'] = arg	    	    	    
	    self.d_kws['excludeSelf'] = excludeSelf	    	    
	    self.l_funcSteps = [{'step':'Process','call':self.__func__}]
	    #The idea is to register the functions needed to be called
	    #=================================================================
	    
	def __func__(self): 
	    try:
		ml_buffer = getSiblings(self.mi_module,self.d_kws['excludeSelf'])
		mayaMainProgressBar = cgmGeneral.doStartMayaProgressBar(len(ml_buffer))    
		for i,i_c in enumerate(ml_buffer):
		    try:
			mc.progressBar(mayaMainProgressBar, edit=True, status = "%s.dynSwitch_children>> step:'%s' "%(self._str_moduleName,i_c.p_nameShort), progress=i)    				        			
			i_c.rigNull.dynSwitch.go(self.d_kws['arg'])
		    except Exception,error:
			log.error("%s  child: %s | %s"%(self._str_reportStart,i_c.getShortName(),error))
		cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar        	
	    except Exception,error:
		try:cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar        	
		except:
		    raise StandardError,error
		
	    return False  
    #We wrap it so that it autoruns and returns
    return fncWrap(moduleInstance,arg,excludeSelf).go()
  
def get_mirrorSideAsString(self):
    _str_funcName = "get_mirrorSideAsString('%s')"%self.p_nameShort   
    log.debug(">>> %s "%(_str_funcName) + "="*75)   
    try:
	_str_direction = self.getAttr('cgmDirection') 
	if _str_direction is not None and _str_direction.lower() in ['right','left']:
	    return _str_direction.capitalize()
	else:
	    return 'Centre'
    except Exception,error:
	raise StandardError,"%s >> %s"%(_str_funcName,error) 

def toggle_subVis(moduleInstance = None):
    class fncWrap(ModuleFunc):
	def __init__(self,goInstance = None):
	    """
	    """	
	    super(fncWrap, self).__init__(moduleInstance)
	    self._str_funcName = "toggle_subVis('%s')"%self._str_moduleName
	    self.__dataBind__()
	    self.l_funcSteps = [{'step':'Process','call':self.__func__}]
	    #The idea is to register the functions needed to be called
	    #=================================================================
	    
	def __func__(self): 
	    mi_module = self.mi_module
	    try:
		if mi_module.moduleType in __l_faceModules__:
		    mi_module.rigNull.settings.visSubFace = not mi_module.rigNull.settings.visSubFace		    
		else:
		    mi_module.rigNull.settings.visSub = not mi_module.rigNull.settings.visSub
		return True
	    except Exception,error:
		log.error("%s | %s"%(self._str_reportStart,error))
	    return False  
	
    #We wrap it so that it autoruns and returns
    return fncWrap(moduleInstance).go()

def animSetAttr_children(moduleInstance = None, attr = None, value = None, settingsOnly = False, excludeSelf = True):
    class fncWrap(ModuleFunc):
	def __init__(self,goInstance = None, attr = None, value = None, settingsOnly = False,excludeSelf = True):
	    """
	    """	
	    super(fncWrap, self).__init__(moduleInstance)
	    self._str_funcName = "animReset_siblings('%s')"%self._str_moduleName
	    self.__dataBind__()
	    self.d_kws['excludeSelf'] = excludeSelf	
	    self.d_kws['attr'] = attr	  
	    self.d_kws['value'] = value	  
	    self.d_kws['settingsOnly'] = settingsOnly	  
	    self.l_funcSteps = [{'step':'Process','call':self.__func__}]
	    #The idea is to register the functions needed to be called
	    #=================================================================
	    
	def __func__(self): 
	    try:
		ml_buffer = getAllModuleChildren(self.mi_module,self.d_kws['excludeSelf'])

		mayaMainProgressBar = cgmGeneral.doStartMayaProgressBar(len(ml_buffer))  
		for i,mModule in enumerate(ml_buffer):
		    try:
			mc.progressBar(mayaMainProgressBar, edit=True, status = "%s >> step:'%s' "%(self._str_reportStart,mModule.p_nameShort), progress=i)    				        			
			if self.d_kws['settingsOnly']:
			    mmi_rigNull = mModule.rigNull
			    if mmi_rigNull.getMessage('settings'):
				mmi_rigNull.settings.__setattr__(self.d_kws['attr'],self.d_kws['value'])
			else:
			    for o in mModule.rigNull.moduleSet.getList():
				attributes.doSetAttr(o,self.d_kws['attr'],self.d_kws['value'])
		    except Exception,error:
			log.error("%s  child: %s | %s"%(self._str_reportStart,mModule.p_nameShort,error))
		cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar 
		return False
		
	    except Exception,error:
		try:cgmGeneral.doEndMayaProgressBar(mayaMainProgressBar)#Close out this progress bar        	
		except:
		    raise StandardError,error
	    return False  
	
    #We wrap it so that it autoruns and returns
    return fncWrap(moduleInstance,attr,value,settingsOnly,excludeSelf).go()


