import os
import unittest
import logging
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

#
# SlicerPACSConnector
#

class SlicerPACSConnector(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "SlicerPACSConnector"  # TODO: make this more human readable by adding spaces
    self.parent.categories = ["Examples"]  # TODO: set categories (folders where the module shows up in the module selector)
    self.parent.dependencies = []  # TODO: add here list of module names that this module requires
    self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
    # TODO: update with short description of the module and a link to online module documentation
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://connect.sivc.ch/organization/,DanaInfo=github.com,SSL+projectname#SlicerPACSConnector" >module documentation</a>.
"""
    # TODO: replace with organization, grant and thanks
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""

    # Additional initialization step after application startup is complete
    slicer.app.connect("startupCompleted()", registerSampleData)

#
# Register sample data sets in Sample Data module
#

def registerSampleData():
  """
  Add data sets to Sample Data module.
  """
  # It is always recommended to provide sample data for users to make it easy to try the module,
  # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.


#
# SlicerPACSConnectorWidget
#

class SlicerPACSConnectorWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)  # needed for parameter node observation
    self.logic = None
    self._parameterNode = None
    self._updatingGUIFromParameterNode = False

  def setup(self):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.setup(self)

    # Load widget from .ui file (created by Qt Designer).
    # Additional widgets can be instantiated manually and added to self.layout.
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/SlicerPACSConnector.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
    # "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)

    # Create logic class. Logic implements all computations that should be possible to run
    # in batch mode, without a graphical user interface.
    self.logic = SlicerPACSConnectorLogic()

    # Connections

    # These connections ensure that we update parameter node when scene is closed
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
    self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

    # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
    # (in the selected parameter node).
    self.ui.patientIDLineEdit.connect("textChanged(static QString)", self.updateParameterNodeFromGUI)
    self.ui.accessionNumberLineEdit.connect("textChanged(static QString)", self.updateParameterNodeFromGUI)
    self.ui.modalityLineEdit.connect("textChanged(static QString)", self.updateParameterNodeFromGUI)
    self.ui.seriesDescriptionLineEdit.connect("textChanged(static QString)", self.updateParameterNodeFromGUI)
    self.ui.studyDateLineEdit.connect("textChanged(static QString)", self.updateParameterNodeFromGUI)
    self.ui.preferCGETCheckBox.connect('toggled(bool)', self.updateParameterNodeFromGUI)

    # Buttons
    self.ui.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.ui.queryButton.connect('clicked(bool)', self.onQueryButton)

    self.ui.patientIDLineEdit.text = "Anon" 
    self.ui.modalityLineEdit.text = "CT" 
    self.ui.accessionNumberLineEdit.text = "" 
    
    self.ui.callingAETitleLineEdit.text = "SLICER" 
    self.ui.calledAETitleLineEdit.text = "ANYE" 
    self.ui.storageAETitleLineEdit.text = "SLICER" 
    self.ui.calledHostLineEdit.text = "dicomserver.co.uk" 
    self.ui.calledPortLineEdit.text = "11112" 
    self.preferCGET = True
    self.ui.preferCGETCheckBox.checked = self.preferCGET
    


    # Make sure parameter node is initialized (needed for module reload)
    self.initializeParameterNode()

  def cleanup(self):
    """
    Called when the application closes and the module widget is destroyed.
    """
    self.removeObservers()

  def enter(self):
    """
    Called each time the user opens this module.
    """
    # Make sure parameter node exists and observed
    self.initializeParameterNode()

  def exit(self):
    """
    Called each time the user opens a different module.
    """
    # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
    self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

  def onSceneStartClose(self, caller, event):
    """
    Called just before the scene is closed.
    """
    # Parameter node will be reset, do not use it anymore
    self.setParameterNode(None)

  def onSceneEndClose(self, caller, event):
    """
    Called just after the scene is closed.
    """
    # If this module is shown while the scene is closed then recreate a new parameter node immediately
    if self.parent.isEntered:
      self.initializeParameterNode()

  def initializeParameterNode(self):
    """
    Ensure parameter node exists and observed.
    """
    # Parameter node stores all user choices in parameter values, node selections, etc.
    # so that when the scene is saved and reloaded, these settings are restored.

    self.setParameterNode(self.logic.getParameterNode())


  def setParameterNode(self, inputParameterNode):
    """
    Set and observe parameter node.
    Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
    """


    # Unobserve previously selected parameter node and add an observer to the newly selected.
    # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
    # those are reflected immediately in the GUI.
    if self._parameterNode is not None:
      self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    if self._parameterNode is not None:
      self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    # Initial GUI update
    self.updateGUIFromParameterNode()

  def updateGUIFromParameterNode(self, caller=None, event=None):
    """
    This method is called whenever parameter node is changed.
    The module GUI is updated to show the current state of the parameter node.
    """

    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
    self._updatingGUIFromParameterNode = True

    # Update node selectors and sliders
    self.ui.patientIDLineEdit.setText(self._parameterNode.GetNodeReference("patientIDLineEdit"))
    self.ui.accessionNumberLineEdit.setText(self._parameterNode.GetNodeReference("accessionNumberLineEdit"))
    self.ui.modalityLineEdit.setText(self._parameterNode.GetNodeReference("modalityLineEdit"))
    self.ui.seriesDescriptionLineEdit.setText(self._parameterNode.GetNodeReference("seriesDescriptionLineEdit"))
    self.ui.studyDateLineEdit.setText(self._parameterNode.GetNodeReference("studyDateLineEdit"))
    self.ui.preferCGETCheckBox.checked = self.preferCGET

    # Update buttons states and tooltips
    if self._parameterNode.GetNodeReference("patientIDLineEdit"):
      self.ui.applyButton.toolTip = "Start"
      self.ui.applyButton.enabled = True
    else:
      self.ui.applyButton.toolTip = "Enter at leat a patient ID"
      self.ui.applyButton.enabled = False

    # All the GUI updates are done
    self._updatingGUIFromParameterNode = False

  def updateParameterNodeFromGUI(self, caller=None, event=None):
    """
    This method is called when the user makes any change in the GUI.
    The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
    """

    if self._parameterNode is None or self._updatingGUIFromParameterNode:
      return

    wasModified = self._parameterNode.StartModify()  # Modify all properties in a single batch

    self._parameterNode.SetNodeReferenceID("patientIDLineEdit", self.ui.patientIDLineEdit.text)
    self._parameterNode.SetNodeReferenceID("accessionNumberLineEdit", self.ui.accessionNumberLineEdit.text)
    self._parameterNode.SetNodeReferenceID("modalityLineEdit", self.ui.modalityLineEdit.text)
    self._parameterNode.SetNodeReferenceID("seriesDescriptionLineEdit", self.ui.seriesDescriptionLineEdit.text)
    self._parameterNode.SetNodeReferenceID("studyDateLineEdit", self.ui.studyDateLineEdit.text)
    self.preferCGET = self.ui.preferCGETCheckBox.checked

    self._parameterNode.EndModify(wasModified)

  def onQueryButton(self):
    """
    Run query processing when user clicks "Query" button.
    """
    try:
      # Compute output
      queryFlag = 1
      
      self.patientIDStr = self.ui.patientIDLineEdit.text
      self.accessionNumberStr = self.ui.accessionNumberLineEdit.text
      self.modalityStr = self.ui.modalityLineEdit.text
      self.seriesDescriptionStr = self.ui.seriesDescriptionLineEdit.text
      self.studyDateStr = self.ui.studyDateLineEdit.text
      self.callingAETitleStr = self.ui.callingAETitleLineEdit.text
      self.calledAETitleStr = self.ui.calledAETitleLineEdit.text
      self.storageAETitleStr = self.ui.storageAETitleLineEdit.text
      self.calledHostStr = self.ui.calledHostLineEdit.text
      self.calledPortStr = self.ui.calledPortLineEdit.text
      self.preferCGET = self.ui.preferCGETCheckBox.checked
      
      self.logic.process(queryFlag,self.patientIDStr,self.accessionNumberStr,self.modalityStr,self.seriesDescriptionStr,self.studyDateStr, \
        self.callingAETitleStr, self.calledAETitleStr,self.storageAETitleStr, self.calledHostStr,self.calledPortStr,self.preferCGET)


    except Exception as e:
      slicer.util.errorDisplay("Failed to compute results: "+str(e))
      import traceback
      traceback.print_exc()

  def onApplyButton(self):
    """
    Run processing when user clicks "Apply" button.
    """
    try:

      # Compute output
      queryFlag = 0
      
      self.patientIDStr = self.ui.patientIDLineEdit.text
      self.accessionNumberStr = self.ui.accessionNumberLineEdit.text
      self.modalityStr = self.ui.modalityLineEdit.text
      self.seriesDescriptionStr = self.ui.seriesDescriptionLineEdit.text
      self.studyDateStr = self.ui.studyDateLineEdit.text
      self.callingAETitleStr = self.ui.callingAETitleLineEdit.text
      self.calledAETitleStr = self.ui.calledAETitleLineEdit.text
      self.storageAETitleStr = self.ui.storageAETitleLineEdit.text
      self.calledHostStr = self.ui.calledHostLineEdit.text
      self.calledPortStr = self.ui.calledPortLineEdit.text
      self.preferCGET = self.ui.preferCGETCheckBox.checked
      
      self.logic.process(queryFlag,self.patientIDStr,self.accessionNumberStr,self.modalityStr,self.seriesDescriptionStr,self.studyDateStr, \
        self.callingAETitleStr, self.calledAETitleStr,self.storageAETitleStr, self.calledHostStr,self.calledPortStr,self.preferCGET)


    except Exception as e:
      slicer.util.errorDisplay("Failed to compute results: "+str(e))
      import traceback
      traceback.print_exc()


#
# SlicerPACSConnectorLogic
#

class SlicerPACSConnectorLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self):
    """
    Called when the logic class is instantiated. Can be used for initializing member variables.
    """
    ScriptedLoadableModuleLogic.__init__(self)

  def setDefaultParameters(self, parameterNode):
    """
    Initialize parameter node with default settings.
    """

    


  def process(self, queryFlag, patientID, accessionNumber,modalities,seriesDescription,studyDate,\
               callingAETitle, calledAETitle,storageAETitle, calledHost,calledPort,preferCGET):
  

    """
    Run the processing algorithm.
    Can be used without GUI widget.
    """

    import subprocess
    from datetime import datetime


    import time
    startTime = time.time()
    logging.info('Processing started')

    if not patientID:
      raise ValueError("You need to specify a patient ID.")

   
    # Query
    dicomQuery = ctk.ctkDICOMQuery()
    dicomQuery.callingAETitle = callingAETitle
    dicomQuery.calledAETitle = calledAETitle
    dicomQuery.host = calledHost
    dicomQuery.port = int(calledPort)
    dicomQuery.preferCGET = bool(preferCGET)
    
    if len(studyDate)>0: 
        dicomQuery.filters = {'ID':patientID, 'AccessionNumber':accessionNumber, 'Modalities':modalities,'Series':seriesDescription,'StartDate':studyDate,'EndDate':studyDate}    
    else:
        dicomQuery.filters = {'ID':patientID, 'AccessionNumber':accessionNumber, 'Modalities':modalities,'Series':seriesDescription}    
    
    
    
    # temporary in-memory database for storing query results
    tempDb = ctk.ctkDICOMDatabase()
    tempDb.openDatabase('')
    dicomQuery.query(tempDb)

    # Retrieve
    dicomRetrieve = ctk.ctkDICOMRetrieve()
    dicomRetrieve.setDatabase(slicer.dicomDatabase)
    dicomRetrieve.keepAssociationOpen = True
    dicomRetrieve.connect("progress(QString)", print)
    dicomRetrieve.setCallingAETitle(dicomQuery.callingAETitle)
    dicomRetrieve.setCalledAETitle(dicomQuery.calledAETitle)
    dicomRetrieve.setHost(dicomQuery.host)
    dicomRetrieve.setPort(dicomQuery.port)
    dicomRetrieve.setMoveDestinationAETitle(dicomQuery.callingAETitle)
    
    for study in dicomQuery.studyInstanceUIDQueried:
      slicer.app.processEvents()
      if dicomQuery.preferCGET:
        print(f" ... getting  {study}")
        if queryFlag==0: 
            success = dicomRetrieve.getStudy(study)
      else:
        print(f"... moving {study}")
        if queryFlag==0: 
           success = dicomRetrieve.moveStudy(study)
      if queryFlag==0: 
        print(f"  - {'success' if success else 'failed'}")
      
    #if _process == False: 
    #  for obj in retrieveList: 
    #    print(obj.date,obj.name,obj.studyUID,obj.seriesUID,obj.acNumber) 
    #    success = dicomRetrieve.moveSeries(obj.studyUID.decode("utf-8"),obj.seriesUID.decode("utf-8"))
    #    print(f"  - {'success' if success else 'failed'}")

      
      
    slicer.dicomDatabase.updateDisplayedFields()    
    
    
    stopTime = time.time()
    logging.info('Processing completed in {0:.2f} seconds'.format(stopTime-startTime))

#
# SlicerPACSConnectorTest
#

class SlicerPACSConnectorTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear()

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_SlicerPACSConnector1()

  def test_SlicerPACSConnector1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")

    # Get/create input data


    # Test the module logic

    logic = SlicerPACSConnectorLogic()

    # Test algorithm with non-inverted threshold
    logic.process()

    # Test algorithm with inverted threshold
    logic.process()

    self.delayDisplay('Test passed')
