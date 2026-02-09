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
		spinner spnTargetSpeed "Target Speed (m/s):" range:[-100,100,10] type:#float fieldwidth:60 offset:[0,5]
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
		local startFrame = endFrame - blendFrames
		
		if startFrame < (animationRange.start.frame + 1) then
		(
			messageBox "Not enough frames for blending! Reduce blend frames or extend timeline." title:"Root Smoothing"
			return false
		)
		
		local fps = frameRate as float
		-- Target speed in cm/frame (the unit Max works in)
		local targetCmPerFrame = (targetSpeedMS * 100.0) / fps
		
		-- Get original speed at the start of blend range (speed INTO startFrame)
		local posBeforeStart = at time (startFrame - 1) (in coordsys world selectedBone.pos)
		local posAtStart = at time startFrame (in coordsys world selectedBone.pos)
		local origSpeedX = posAtStart.x - posBeforeStart.x
		local origSpeedY = posAtStart.y - posBeforeStart.y
		local origSpeedZ = posAtStart.z - posBeforeStart.z
		
		-- FIXED last frame position - never changes
		local lastFramePos = at time endFrame (in coordsys world selectedBone.pos)
		
		-- Convert original speeds to m/s for debug display
		local origMsX = origSpeedX / 100.0 * fps
		local origMsY = origSpeedY / 100.0 * fps
		local origMsZ = origSpeedZ / 100.0 * fps
		
		format "\n=== Root Smoothing (Backward Extrapolation) ===\n"
		format "End frame: % [FIXED pos: %]\n" endFrame lastFramePos
		format "Blend: frame % to frame % (% frames)\n" startFrame (endFrame - 1) blendFrames
		format "Original speed at start: X=% Y=% Z=% cm/frame\n" origSpeedX origSpeedY origSpeedZ
		format "Original speed at start: X=% Y=% Z=% m/s\n" origMsX origMsY origMsZ
		format "Target speed: % m/s = % cm/frame\n" targetSpeedMS targetCmPerFrame
		
		-- ============================================================
		-- Algorithm:
		-- We have N = blendFrames steps from startFrame to endFrame.
		-- Step i (1-based) goes from frame (startFrame + i - 1) to (startFrame + i).
		-- Step N is the LAST step, going into endFrame.
		--
		-- Speed at step i = lerp(origSpeed, targetSpeed, i / N)
		--   step 1: mostly original speed
		--   step N: exactly target speed
		--
		-- We build positions BACKWARDS from the fixed endFrame:
		--   pos[endFrame] = lastFramePos  (fixed)
		--   pos[endFrame - 1] = pos[endFrame] - speed_at_step_N
		--   pos[endFrame - 2] = pos[endFrame - 1] - speed_at_step_(N-1)
		--   ...
		--   pos[startFrame] = pos[startFrame + 1] - speed_at_step_1
		-- ============================================================
		
		-- Build positions array backward (index 1 = endFrame, last = startFrame)
		local numSteps = blendFrames  -- N steps
		local framePositions = #()  -- array of #(frameNum, x, y, z)
		
		-- Start from fixed end
		local curX = lastFramePos.x
		local curY = lastFramePos.y
		local curZ = lastFramePos.z
		
		-- endFrame itself (fixed, we store it but won't key it)
		append framePositions #(endFrame, curX, curY, curZ)
		
		-- Walk backward: step N, N-1, ..., 1
		for step = numSteps to 1 by -1 do
		(
			local t = step as float / numSteps as float
			
			-- Speed for this step (lerp between original and target)
			local speedX = origSpeedX + (targetCmPerFrame - origSpeedX) * t
			local speedY = origSpeedY + (targetCmPerFrame - origSpeedY) * t
			local speedZ = origSpeedZ + (targetCmPerFrame - origSpeedZ) * t
			
			-- Subtract to go backward
			curX = curX - speedX
			curY = curY - speedY
			curZ = curZ - speedZ
			
			local f = startFrame + step - 1
			append framePositions #(f, curX, curY, curZ)
			
			local speedMS = speedX / 100.0 * fps
			local speedMSY = speedY / 100.0 * fps
			local speedMSZ = speedZ / 100.0 * fps
			format "  Step %: frame % -> speed X=% Y=% Z=% m/s\n" step f speedMS speedMSY speedMSZ
		)
		
		with undo on
		(
			-- Apply positions (skip endFrame - it's fixed)
			for i = 2 to framePositions.count do
			(
				local f = framePositions[i][1]
				local currentPos = at time f (in coordsys world selectedBone.pos)
				local newPos = copy currentPos
				
				if chkX.checked then newPos.x = framePositions[i][2]
				if chkY.checked then newPos.y = framePositions[i][3]
				if chkZ.checked then newPos.z = framePositions[i][4]
				
				at time f
				(
					animate on
					(
						in coordsys world selectedBone.pos = newPos
					)
				)
			)
		)
		
		format "Done! Last frame % position unchanged.\n" endFrame
		messageBox ("Root smoothed to " + (targetSpeedMS as string) + " m/s over " + (blendFrames as string) + " frames.\nLast frame position preserved.") title:"Root Smoothing Complete"
		
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
