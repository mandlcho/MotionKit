-- Bone Axis Speed Calculator
-- For 3ds Max 2023
-- Just drag this file into 3ds Max viewport to run

-- Close existing instance if open
try
(
	if boneSpeedDialog != undefined then
	(
		destroyDialog boneSpeedDialog
	)
)
catch()

rollout boneSpeedRollout "Bone Axis Speed Calculator"
(
	-- UI Elements
	group "Bone Selection"
	(
		pickbutton btnPickBone "Pick Bone" width:160 height:30
		label lblSelectedBone "Selected: None" align:#left offset:[5,5]
	)
	
	group "Axis Selection"
	(
		checkbox chkX "X" checked:false across:3 offset:[10,5]
		checkbox chkY "Y" checked:false offset:[10,5]
		checkbox chkZ "Z" checked:true offset:[10,5]
	)
	
	group "Settings"
	(
		checkbox chkAutoUpdate "Auto-Update While Scrubbing" checked:true offset:[5,5]
	)
	
	group "Speed Information"
	(
		label lblCurrentFrame "Current Frame: --" align:#left offset:[5,5]
		edittext txtSpeedX "X-Speed:" readonly:true fieldwidth:120 offset:[0,5]
		edittext txtSpeedY "Y-Speed:" readonly:true fieldwidth:120 offset:[0,5]
		edittext txtSpeedZ "Z-Speed:" readonly:true fieldwidth:120 offset:[0,5]
	)
	
	-- Variables
	local selectedBone = undefined
	local lastFrame = -1
	local isCallbackActive = false
	
	-- Calculate Speed Function
	function calculateSpeed =
	(
		if selectedBone == undefined or not isValidNode selectedBone then
			return()
		
		local currentF = sliderTime.frame as integer
		
		-- Check if we're not at the last frame
		if currentF >= animationRange.end.frame then
		(
			lblCurrentFrame.text = "Current Frame: " + (currentF as string)
			if chkX.checked then txtSpeedX.text = "N/A (last frame)"
			if chkY.checked then txtSpeedY.text = "N/A (last frame)"
			if chkZ.checked then txtSpeedZ.text = "N/A (last frame)"
			return()
		)
		
		-- Calculate speed at current frame
		local fps = frameRate as float
		local timeDelta = 1.0 / fps
		
		local pos1 = in coordsys world selectedBone.transform.pos
		
		at time (currentF + 1)
		(
			local pos2 = in coordsys world selectedBone.transform.pos
			
			-- Convert to meters per second (assuming scene units are centimeters)
			local conversionFactor = 100.0  -- for centimeters to meters
			
			-- Calculate X speed
			if chkX.checked then
			(
				local speedX = (pos2.x - pos1.x) / timeDelta
				local speedXMS = speedX / conversionFactor
				txtSpeedX.text = (speedXMS as string) + " m/s"
			)
			else
			(
				txtSpeedX.text = "--"
			)
			
			-- Calculate Y speed
			if chkY.checked then
			(
				local speedY = (pos2.y - pos1.y) / timeDelta
				local speedYMS = speedY / conversionFactor
				txtSpeedY.text = (speedYMS as string) + " m/s"
			)
			else
			(
				txtSpeedY.text = "--"
			)
			
			-- Calculate Z speed
			if chkZ.checked then
			(
				local speedZ = (pos2.z - pos1.z) / timeDelta
				local speedZMS = speedZ / conversionFactor
				txtSpeedZ.text = (speedZMS as string) + " m/s"
			)
			else
			(
				txtSpeedZ.text = "--"
			)
			
			-- Display current frame
			lblCurrentFrame.text = "Current Frame: " + (currentF as string)
		)
	)
	
	-- Redraw callback function
	function updateCallback =
	(
		local currentF = sliderTime.frame as integer
		if currentF != lastFrame then
		(
			lastFrame = currentF
			boneSpeedRollout.calculateSpeed()
		)
	)
	
	-- Pick Bone Handler
	on btnPickBone picked obj do
	(
		if isValidNode obj then
		(
			selectedBone = obj
			lblSelectedBone.text = "Selected: " + obj.name
			btnPickBone.text = obj.name
			
			-- Always calculate immediately when bone is picked
			calculateSpeed()
		)
		else
		(
			messageBox "Please select a valid object!"
		)
	)
	
	-- Axis checkbox handlers
	on chkX changed state do
	(
		if selectedBone != undefined then calculateSpeed()
	)
	
	on chkY changed state do
	(
		if selectedBone != undefined then calculateSpeed()
	)
	
	on chkZ changed state do
	(
		if selectedBone != undefined then calculateSpeed()
	)
	
	-- Auto-Update Toggle
	on chkAutoUpdate changed state do
	(
		if state then
		(
			-- Enable auto-update
			if not isCallbackActive then
			(
				try
				(
					registerRedrawViewsCallback updateCallback
					isCallbackActive = true
				)
				catch()
			)
			calculateSpeed()
		)
		else
		(
			-- Disable auto-update
			if isCallbackActive then
			(
				try
				(
					unregisterRedrawViewsCallback updateCallback
					isCallbackActive = false
				)
				catch()
			)
		)
	)
	
	-- Initialize on open
	on boneSpeedRollout open do
	(
		-- Enable auto-update by default
		if chkAutoUpdate.checked then
		(
			try
			(
				registerRedrawViewsCallback updateCallback
				isCallbackActive = true
			)
			catch()
		)
	)
	
	-- Cleanup on close
	on boneSpeedRollout close do
	(
		if isCallbackActive then
		(
			try
			(
				unregisterRedrawViewsCallback updateCallback
				isCallbackActive = false
			)
			catch()
		)
	)
)

-- Create Dialog and store reference
global boneSpeedDialog = createDialog boneSpeedRollout 200 320
