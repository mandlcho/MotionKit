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
	
	group "Root Smoothing"
	(
		label lblRootHelp "Smooth root animation to target speed:" align:#left offset:[5,5]
		spinner spnTargetSpeed "Target Speed (m/s):" range:[0,100,10] type:#float fieldwidth:60 offset:[0,5]
		spinner spnBlendFrames "Blend Frames:" range:[1,100,30] type:#integer fieldwidth:60 offset:[0,5]
		button btnSmoothRoot "Smooth Root to Target" width:160 height:30 offset:[0,5]
	)
	
	-- Variables
	local selectedBone = undefined
	local lastFrame = -1
	local isCallbackActive = false
	local transformCallback = undefined
	
	-- Calculate Speed Function
	function calculateSpeed =
	(
		if selectedBone == undefined or not isValidNode selectedBone then
			return()
		
		local currentF = sliderTime.frame as integer
		local fps = frameRate as float
		local timeDelta = 1.0 / fps
		local conversionFactor = 100.0  -- for centimeters to meters
		
		-- Calculate current frame speed
		if currentF < animationRange.end.frame then
		(
			-- Normal case: calculate speed from current to next frame
			local pos1 = in coordsys world selectedBone.transform.pos
			
			at time (currentF + 1)
			(
				local pos2 = in coordsys world selectedBone.transform.pos
				
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
			)
			
			lblCurrentFrame.text = "Current Frame: " + (currentF as string)
		)
		else if currentF == animationRange.end.frame and currentF > animationRange.start.frame then
		(
			-- On last frame: show speed coming INTO this frame (from previous frame)
			at time (currentF - 1)
			(
				local pos1 = in coordsys world selectedBone.transform.pos
				
				at time currentF
				(
					local pos2 = in coordsys world selectedBone.transform.pos
					
					-- Calculate X speed
					if chkX.checked then
					(
						local speedX = (pos2.x - pos1.x) / timeDelta
						local speedXMS = speedX / conversionFactor
						txtSpeedX.text = (speedXMS as string) + " m/s (into last frame)"
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
						txtSpeedY.text = (speedYMS as string) + " m/s (into last frame)"
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
						txtSpeedZ.text = (speedZMS as string) + " m/s (into last frame)"
					)
					else
					(
						txtSpeedZ.text = "--"
					)
				)
			)
			
			lblCurrentFrame.text = "Current Frame: " + (currentF as string) + " (LAST)"
		)
		else
		(
			lblCurrentFrame.text = "Current Frame: " + (currentF as string)
			if chkX.checked then txtSpeedX.text = "N/A"
			if chkY.checked then txtSpeedY.text = "N/A"
			if chkZ.checked then txtSpeedZ.text = "N/A"
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
			-- Remove old transform callback if exists
			if transformCallback != undefined then
			(
				try (deleteChangeHandler transformCallback) catch()
				transformCallback = undefined
			)
			
			selectedBone = obj
			lblSelectedBone.text = "Selected: " + obj.name
			btnPickBone.text = obj.name
			
			-- Register transform callback if auto-update is enabled
			if chkAutoUpdate.checked then
			(
				try
				(
					transformCallback = when transform selectedBone changes do
					(
						boneSpeedRollout.calculateSpeed()
					)
				)
				catch()
			)
			
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
	
	-- Smooth Root Function
	function smoothRootToTarget =
	(
		if selectedBone == undefined or not isValidNode selectedBone then
		(
			messageBox "Please select a bone first!" title:"Root Smoothing"
			return false
		)
		
		-- Check which axes are selected
		if not chkX.checked and not chkY.checked and not chkZ.checked then
		(
			messageBox "Please select at least one axis (X, Y, or Z) to smooth!" title:"Root Smoothing"
			return false
		)
		
		local targetSpeedMS = spnTargetSpeed.value
		local blendFrames = spnBlendFrames.value as integer
		local endFrame = animationRange.end.frame as integer
		local targetFrame = endFrame - 1  -- We adjust up to the frame BEFORE last
		local startFrame = endFrame - blendFrames  -- Count back N frames from last frame
		
		if startFrame < animationRange.start.frame then
		(
			messageBox "Not enough frames for blending! Reduce blend frames or extend timeline." title:"Root Smoothing"
			return false
		)
		
		local fps = frameRate as float
		local conversionFactor = 100.0
		local targetDistancePerFrame = (targetSpeedMS * conversionFactor) / fps
		
		-- Get the FIXED last frame position (this won't change)
		local lastFramePos = at time endFrame (in coordsys world selectedBone.pos)
		
		-- Get the current target frame position
		local currentTargetPos = at time targetFrame (in coordsys world selectedBone.pos)
		
		-- Calculate where targetFrame should be based on selected axes
		-- We move BACK from lastFrame by targetDistance in the selected axes
		local targetFramePos = copy currentTargetPos
		
		-- For each selected axis, calculate where it should be
		if chkX.checked then
		(
			-- Calculate direction in X (positive or negative)
			local deltaX = lastFramePos.x - currentTargetPos.x
			local directionX = 0
			if deltaX != 0 then
				directionX = deltaX / abs deltaX
			-- Move back by target distance
			targetFramePos.x = lastFramePos.x - (directionX * targetDistancePerFrame)
		)
		else
		(
			-- Keep original X
			targetFramePos.x = currentTargetPos.x
		)
		
		if chkY.checked then
		(
			local deltaY = lastFramePos.y - currentTargetPos.y
			local directionY = 0
			if deltaY != 0 then
				directionY = deltaY / abs deltaY
			targetFramePos.y = lastFramePos.y - (directionY * targetDistancePerFrame)
		)
		else
		(
			targetFramePos.y = currentTargetPos.y
		)
		
		if chkZ.checked then
		(
			local deltaZ = lastFramePos.z - currentTargetPos.z
			local directionZ = 0
			if deltaZ != 0 then
				directionZ = deltaZ / abs deltaZ
			targetFramePos.z = lastFramePos.z - (directionZ * targetDistancePerFrame)
		)
		else
		(
			targetFramePos.z = currentTargetPos.z
		)
		
		-- Store the start position
		local startPos = at time startFrame (in coordsys world selectedBone.pos)
		
		-- Debug output
		format "\n=== Root Smoothing ===\n"
		format "Selected Axes: X=% Y=% Z=%\n" chkX.checked chkY.checked chkZ.checked
		format "Start Frame: %\n" startFrame
		format "Target Frame: %\n" targetFrame
		format "Last Frame: % [FIXED]\n" endFrame
		format "Start Pos: %\n" startPos
		format "Target Pos: %\n" targetFramePos
		format "Last Pos: % [UNCHANGED]\n" lastFramePos
		format "Target Speed: % m/s (% cm/frame)\n" targetSpeedMS targetDistancePerFrame
		format "Blend Frames: %\n" blendFrames
		
		with undo on
		(
			-- Apply smoothed positions
			for f = startFrame to targetFrame do
			(
				-- Calculate blend factor (0 to 1)
				local t = (f - startFrame) as float / blendFrames as float
				
				-- Get current position at this frame
				local currentPos = at time f (in coordsys world selectedBone.pos)
				
				-- Interpolate only the selected axes
				local newPos = copy currentPos
				
				if chkX.checked then
					newPos.x = startPos.x + ((targetFramePos.x - startPos.x) * t)
				
				if chkY.checked then
					newPos.y = startPos.y + ((targetFramePos.y - startPos.y) * t)
				
				if chkZ.checked then
					newPos.z = startPos.z + ((targetFramePos.z - startPos.z) * t)
				
				-- Set position at this frame
				at time f
				(
					animate on
					(
						in coordsys world selectedBone.pos = newPos
					)
				)
			)
			
			format "Smoothing complete!\n"
			messageBox ("Root smoothed to " + (targetSpeedMS as string) + " m/s in selected axes over " + (blendFrames as string) + " frames.") title:"Root Smoothing Complete"
		)
		
		-- Recalculate speeds to show updated values
		calculateSpeed()
		
		return true
	)
		
		local targetSpeedMS = spnTargetSpeed.value
		local blendFrames = spnBlendFrames.value as integer
		local endFrame = animationRange.end.frame as integer
		local targetFrame = endFrame - 1  -- We adjust up to the frame BEFORE last
		local startFrame = targetFrame - blendFrames
		
		if startFrame < animationRange.start.frame then
		(
			messageBox "Not enough frames for blending! Reduce blend frames or extend timeline." title:"Root Smoothing"
			return false
		)
		
		-- Check if bone has position controller
		if selectedBone.transform.controller == undefined then
		(
			messageBox "Selected bone has no transform controller!" title:"Root Smoothing"
			return false
		)
		
		local fps = frameRate as float
		local conversionFactor = 100.0
		
		-- Calculate target distance per frame in scene units (cm)
		local targetDistancePerFrame = (targetSpeedMS * conversionFactor) / fps
		
		-- Get the FIXED last frame position (this won't change)
		local lastFramePos = at time endFrame (in coordsys world selectedBone.pos)
		
		-- Calculate where targetFrame (N-1) needs to be to achieve target speed into lastFrame
		local targetDistancePerFrame = (targetSpeedMS * conversionFactor) / fps
		
		-- Get current direction of travel
		local currentTargetPos = at time targetFrame (in coordsys world selectedBone.pos)
		local currentDirection = normalize (lastFramePos - currentTargetPos)
		
		-- Where should targetFrame be? (distance back from lastFrame)
		local targetFramePos = lastFramePos - (currentDirection * targetDistancePerFrame)
		
		-- Store the start position
		local startPos = at time startFrame (in coordsys world selectedBone.pos)
		
		-- Debug output
		format "Start Frame: %, Target Frame: %, Last Frame: %\n" startFrame targetFrame endFrame
		format "Last Frame (%) Pos: % [FIXED]\n" endFrame lastFramePos
		format "Target Frame (%) Pos: %\n" targetFrame targetFramePos
		format "Start Frame (%) Pos: %\n" startFrame startPos
		format "Target Speed: % m/s (% cm/frame)\n" targetSpeedMS targetDistancePerFrame
		
		with undo on
		(
			-- Enable animation mode
			setCommandPanelTaskMode mode:#modify
			
			-- Apply smoothed positions (from startFrame to targetFrame, NOT including endFrame)
			for f = startFrame to targetFrame do
			(
				-- Calculate blend factor (0 to 1)
				local t = (f - startFrame) as float / blendFrames as float
				
				-- Linear interpolation from startPos to targetFramePos
				local newPos = startPos + ((targetFramePos - startPos) * t)
				
				-- Set position at this frame with animate on
				at time f
				(
					animate on
					(
						in coordsys world selectedBone.pos = newPos
					)
				)
				
				format "Frame %: t=%, newPos=%\n" f t newPos
			)
			
			format "Last frame (%) left unchanged at: %\n" endFrame lastFramePos
			
			format "Smoothing complete!\n"
			messageBox ("Root smoothed to " + (targetSpeedMS as string) + " m/s over " + (blendFrames as string) + " frames.\n\nCheck MAXScript Listener for details.") title:"Root Smoothing Complete"
		)
		
		-- Recalculate speeds to show updated values
		calculateSpeed()
		
		return true
	)
	
	-- Smooth Root Button
	on btnSmoothRoot pressed do
	(
		smoothRootToTarget()
	)
	
	-- Auto-Update Toggle
	on chkAutoUpdate changed state do
	(
		if state then
		(
			-- Enable auto-update for timeline scrubbing
			if not isCallbackActive then
			(
				try
				(
					registerRedrawViewsCallback updateCallback
					isCallbackActive = true
				)
				catch()
			)
			
			-- Enable auto-update for bone transforms
			if selectedBone != undefined and transformCallback == undefined then
			(
				try
				(
					transformCallback = when transform selectedBone changes do
					(
						boneSpeedRollout.calculateSpeed()
					)
				)
				catch()
			)
			
			calculateSpeed()
		)
		else
		(
			-- Disable auto-update for timeline scrubbing
			if isCallbackActive then
			(
				try
				(
					unregisterRedrawViewsCallback updateCallback
					isCallbackActive = false
				)
				catch()
			)
			
			-- Disable auto-update for bone transforms
			if transformCallback != undefined then
			(
				try
				(
					deleteChangeHandler transformCallback
					transformCallback = undefined
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
			
			-- Also enable transform callback if bone is selected
			if selectedBone != undefined then
			(
				try
				(
					transformCallback = when transform selectedBone changes do
					(
						boneSpeedRollout.calculateSpeed()
					)
				)
				catch()
			)
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
		
		if transformCallback != undefined then
		(
			try
			(
				deleteChangeHandler transformCallback
				transformCallback = undefined
			)
			catch()
		)
	)
)

-- Create Dialog and store reference
global boneSpeedDialog = createDialog boneSpeedRollout 200 480
