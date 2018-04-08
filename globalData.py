
class GlobalData(object): # a data storage container that is passed to almost every function in reader.py

	def __init__(self):

		self._myHandlerDirectory = "" # where the log file is located
		self._detectedChange = False # used by Observer (operating system event handler) to check if the log file has been modified
		self._lineNum = 0 # store which line we last parsed, so we can start from that line when we continue parsing
		self._reachedEnd = False # have we parsed to the end of the file
		self._hasBeenModified = False # whether we have found new data
		self._startTime = 0 # used for storing the epoch time at which we start parsing, used by timeouts
		self._limit = 3 # seconds until timeout
		self._stop = False # should we terminate this process: has ^C been pressed

		self._plotType = "" # plot type: total or current
		self._pst = "" # graphing for pipeline stage or task?
	
		self._pipelineStates = [] # data container for [ID, state]
		self._stageStates = []
		self._taskStates = []

		self._pipelineLastIndex = 0 # used in processing event states in graphing
		self._stageLastIndex = 0 
		self._taskLastIndex = 0

		self._pipelineNewIndex = 0 # used in processing event states in graphing
		self._stageNewIndex = 0
		self._taskNewIndex = 0 

		self._pipelineStateHistory = [] # used in processing event states in graphing
		self._stageStateHistory = []
		self._taskStateHistory = []

		self._pipelineLastState = {}
		self._stageLastState = {}
		self._taskLastState = {} # dictionary holding last known state of each pst

		self._task_state_values = { # dictionary to convert from string to int to save mem
			'SCHEDULING': 0,
			'SCHEDULED': 1,
			'SUBMITTING': 2,
			'SUBMITTED': 3,
			'EXECUTED': 4,
			'DEQUEUEING': 5,
			'DEQUEUED': 6,
			'DONE': 7,
			'FAILED': 8,
			'CANCELED': 9
		}
		self._taskStatesTotal = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0] # used for plotting all the states possible for that pst
	
		self._stage_state_values = {
			'SCHEDULING': 0,
			'SCHEDULED': 1,
			'DONE': 2,
			'FAILED': 3,
			'CANCELED': 4
		}
		self._stageStatesTotal = [0, 0, 0, 0, 0]

		self._pipeline_state_values = {
			'SCHEDULING': 0,
			'DONE': 1,
			'FAILED': 2,
			'CANCELED': 3
		}
		self._pipelineStatesTotal = [0, 0, 0, 0]

		self._taskDuration = [[0.0, 0.0]]
		self._taskStartTimeTotal = {}
		self._taskStartTimeExecution = {}

	def reset(self): # to restart parsing
		self.__init__()
		print "reset self"

	# setters and getters below

	@property
	def myHandlerDirectory(self):
		"""'myHandlerDirectory' property."""
		return self._myHandlerDirectory
	@myHandlerDirectory.setter
	def myHandlerDirectory(self, value):
		self._myHandlerDirectory = value

	@property
	def detectedChange(self):
		"""'detectedChange' property."""
		return self._detectedChange
	@detectedChange.setter
	def detectedChange(self, value):
		self._detectedChange = value

	@property
	def lineNum(self):
		"""'lineNum' property."""
		return self._lineNum
	@lineNum.setter
	def lineNum(self, value):
		self._lineNum = value

	@property
	def reachedEnd(self):
		"""'reachedEnd' property."""
		return self._reachedEnd
	@reachedEnd.setter
	def reachedEnd(self, value):
		self._reachedEnd = value

	@property
	def hasBeenModified(self):
		"""'hasBeenModified' property."""
		return self._hasBeenModified
	@hasBeenModified.setter
	def hasBeenModified(self, value):
		self._hasBeenModified = value

	@property
	def startTime(self):
		"""'startTime' property."""
		return self._startTime
	@startTime.setter
	def startTime(self, value):
		self._startTime = value

	@property
	def limit(self):
		"""'limit' property."""
		return self._limit
	@limit.setter
	def limit(self, value):
		self._limit = value

	@property
	def stop(self):
		"""'stop' property."""
		return self._stop
	@stop.setter
	def stop(self, value):
		self._stop = value

	@property
	def plotType(self):
		"""'plotType' property."""
		return self._plotType
	@plotType.setter
	def plotType(self, value):
		self._plotType = value

	@property
	def pst(self):
		"""'pst' property."""
		return self._pst
	@pst.setter
	def pst(self, value):
		self._pst = value

	@property
	def pipelineStates(self):
		"""'pipelineStates' property."""
		return self._pipelineStates
	@pipelineStates.setter
	def pipelineStates(self, value):
		self._pipelineStates = value
	def __getitem__(self, idx):
		return self._pipelineStates[idx]
	def __setitem__(self, idx, value):
		self._pipelineStates[idx] = value
	def append(self, val):
		self._pipelineStates = self._pipelineStates + [val]
		return self._pipelineStates  
	def extend(self, val):
		return self._pipelineStates.extend(val)

	@property
	def stageStates(self):
		"""'stageStates' property."""
		return self._stageStates
	@stageStates.setter
	def stageStates(self, value):
		self._stageStates = value
	def __getitem__(self, idx):
		return self._stageStates[idx]
	def __setitem__(self, idx, value):
		self._stageStates[idx] = value
	def append(self, val):
		self._stageStates = self._stageStates + [val]
		return self._stageStates  
	def extend(self, val):
		return self._stageStates.extend(val)

	@property
	def taskStates(self):
		"""'taskStates' property."""
		return self._taskStates
	@taskStates.setter
	def taskStates(self, value):
		self._taskStates = value
	def __getitem__(self, idx):
		return self._taskStates[idx]
	def __setitem__(self, idx, value):
		self._taskStates[idx] = value
	def append(self, val):
		self._taskStates = self._taskStates + [val]
		return self._taskStates  
	def extend(self, val):
		return self._taskStates.extend(val)

	@property
	def pipelineLastIndex(self):
		"""'pipelineLastIndex' property."""
		return self._pipelineLastIndex
	@pipelineLastIndex.setter
	def pipelineLastIndex(self, value):
		self._pipelineLastIndex = value

	@property
	def stageLastIndex(self):
		"""'stageLastIndex' property."""
		return self._stageLastIndex
	@stageLastIndex.setter
	def stageLastIndex(self, value):
		self._stageLastIndex = value

	@property
	def taskLastIndex(self):
		"""'taskLastIndex' property."""
		return self._taskLastIndex
	@taskLastIndex.setter
	def taskLastIndex(self, value):
		self._taskLastIndex = value

	@property
	def pipelineNewIndex(self):
		"""'pipelineNewIndex' property."""
		return self._pipelineNewIndex
	@pipelineNewIndex.setter
	def pipelineNewIndex(self, value):
		self._pipelineNewIndex = value

	@property
	def stageNewIndex(self):
		"""'stageNewIndex' property."""
		return self._stageNewIndex
	@stageNewIndex.setter
	def stageNewIndex(self, value):
		self._stageNewIndex = value

	@property
	def taskNewIndex(self):
		"""'taskNewIndex' property."""
		return self._taskNewIndex
	@taskNewIndex.setter
	def taskNewIndex(self, value):
		self._taskNewIndex = value

	@property
	def pipelineStateHistory(self):
		"""'pipelineStateHistory' property."""
		return self._pipelineStateHistory
	@pipelineStateHistory.setter
	def pipelineStateHistory(self, value):
		self._pipelineStateHistory = value
	def __getitem__(self, idx):
		return self._pipelineStateHistory[idx]
	def __setitem__(self, idx, value):
		self._pipelineStateHistory[idx] = value
	def append(self, val):
		self._pipelineStateHistory = self._pipelineStateHistory + [val]
		return self._pipelineStateHistory  
	def extend(self, val):
		return self._pipelineStateHistory.extend(val)

	@property
	def stageStateHistory(self):
		"""'stageStateHistory' property."""
		return self._stageStateHistory
	@stageStateHistory.setter
	def stageStateHistory(self, value):
		self._stageStateHistory = value
	def __getitem__(self, idx):
		return self._stageStateHistory[idx]
	def __setitem__(self, idx, value):
		self._stageStateHistory[idx] = value
	def append(self, val):
		self._stageStateHistory = self._stageStateHistory + [val]
		return self._stageStateHistory  
	def extend(self, val):
		return self._stageStateHistory.extend(val)

	@property
	def taskStateHistory(self):
		"""'taskStateHistory' property."""
		return self._taskStateHistory
	@taskStateHistory.setter
	def taskStateHistory(self, value):
		self._taskStateHistory = value
	def __getitem__(self, idx):
		return self._taskStateHistory[idx]
	def __setitem__(self, idx, value):
		self._taskStateHistory[idx] = value
	def append(self, val):
		self._taskStateHistory = self._taskStateHistory + [val]
		return self._taskStateHistory  
	def extend(self, val):
		return self._taskStateHistory.extend(val)

	@property
	def pipelineLastState(self):
		"""'pipelineLastState' property."""
		return self._pipelineLastState
	@pipelineLastState.setter
	def pipelineLastState(self, value):
		self._pipelineLastState = value
	def __getitem__(self, idx):
		return self._pipelineLastState[idx]
	def __setitem__(self, idx, value):
		self._pipelineLastState[idx] = value
	def append(self, val):
		self._pipelineLastState = self._pipelineLastState + [val]
		return self._pipelineLastState  
	def extend(self, val):
		return self._pipelineLastState.extend(val)

	@property
	def stageLastState(self):
		"""'stageLastState' property."""
		return self._stageLastState
	@stageLastState.setter
	def stageLastState(self, value):
		self._stageLastState = value
	def __getitem__(self, idx):
		return self._stageLastState[idx]
	def __setitem__(self, idx, value):
		self._stageLastState[idx] = value
	def append(self, val):
		self._stageLastState = self._stageLastState + [val]
		return self._stageLastState  
	def extend(self, val):
		return self._stageLastState.extend(val)

	@property
	def taskLastState(self):
		"""'taskLastState' property."""
		return self._taskLastState
	@taskLastState.setter
	def taskLastState(self, value):
		self._taskLastState = value
	def __getitem__(self, idx):
		return self._taskLastState[idx]
	def __setitem__(self, idx, value):
		self._taskLastState[idx] = value
	def append(self, val):
		self._taskLastState = self._taskLastState + [val]
		return self._taskLastState  
	def extend(self, val):
		return self._taskLastState.extend(val)

	@property
	def task_state_values(self):
		"""'task_state_values' property."""
		return self._task_state_values
	@task_state_values.setter
	def task_state_values(self, value):
		self._task_state_values = value
	def __getitem__(self, idx):
		return self._task_state_values[idx]
	def __setitem__(self, idx, value):
		self._task_state_values[idx] = value

	@property
	def taskStatesTotal(self):
		"""'taskStatesTotal' property."""
		return self._taskStatesTotal
	@taskStatesTotal.setter
	def taskStatesTotal(self, value):
		self._taskStatesTotal = value
	def __getitem__(self, idx):
		return self._taskStatesTotal[idx]
	def __setitem__(self, idx, value):
		self._taskStatesTotal[idx] = value

	@property
	def stage_state_values(self):
		"""'stage_state_values' property."""
		return self._stage_state_values
	@stage_state_values.setter
	def stage_state_values(self, value):
		self._stage_state_values = value
	def __getitem__(self, idx):
		return self._stage_state_values[idx]
	def __setitem__(self, idx, value):
		self._stage_state_values[idx] = value

	@property
	def stageStatesTotal(self):
		"""'stageStatesTotal' property."""
		return self._stageStatesTotal
	@stageStatesTotal.setter
	def stageStatesTotal(self, value):
		self._stageStatesTotal = value
	def __getitem__(self, idx):
		return self._stageStatesTotal[idx]
	def __setitem__(self, idx, value):
		self._stageStatesTotal[idx] = value

	@property
	def pipeline_state_values(self):
		"""'pipeline_state_values' property."""
		return self._pipeline_state_values
	@pipeline_state_values.setter
	def pipeline_state_values(self, value):
		self._pipeline_state_values = value
	def __getitem__(self, idx):
		return self._pipeline_state_values[idx]
	def __setitem__(self, idx, value):
		self._pipeline_state_values[idx] = value

	@property
	def pipelineStatesTotal(self):
		"""'pipelineStatesTotal' property."""
		return self._pipelineStatesTotal
	@pipelineStatesTotal.setter
	def pipelineStatesTotal(self, value):
		self._pipelineStatesTotal = value
	def __getitem__(self, idx):
		return self._pipelineStatesTotal[idx]
	def __setitem__(self, idx, value):
		self._pipelineStatesTotal[idx] = value

	@property
	def taskDuration(self):
		"""'taskDuration' property."""
		return self._taskDuration
	@taskDuration.setter
	def taskDuration(self, value):
		self._taskDuration = value
	def __getitem__(self, idx):
		return self._taskDuration[idx]
	def __setitem__(self, idx, value):
		self._taskDuration[idx] = value
	def append(self, val):
		self._taskDuration = self._taskDuration + [val]
		return self._taskDuration  
	def extend(self, val):
		return self._taskDuration.extend(val)

	@property
	def taskStartTimeTotal(self):
		"""'taskStartTimeTotal' property."""
		return self._taskStartTimeTotal
	@taskStartTimeTotal.setter
	def taskStartTimeTotal(self, value):
		self._taskStartTimeTotal = value
	def __getitem__(self, idx):
		return self._taskStartTimeTotal[idx]
	def __setitem__(self, idx, value):
		self._taskStartTimeTotal[idx] = value

	@property
	def taskStartTimeExecution(self):
		"""'taskStartTimeExecution' property."""
		return self._taskStartTimeExecution
	@taskStartTimeExecution.setter
	def taskStartTimeExecution(self, value):
		self._taskStartTimeExecution = value
	def __getitem__(self, idx):
		return self._taskStartTimeExecution[idx]
	def __setitem__(self, idx, value):
		self._taskStartTimeExecution[idx] = value

