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
	group "Object Selection"
	(
		pickbutton btnPickBone "Pick Object" width:160 height:30
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
		spinner spnBlendFrames "Blend Frames:" range:[1,200,30] type:#integer fieldwidth:60 offset:[0,5]
		button btnCalcBlend "Auto" width:40 height:16 offset:[0,-3] across:2 align:#right tooltip:"Calculate optimal blend frames"
		label lblBlendInfo "" align:#left offset:[0,-3]
		button btnPreview "Preview" width:160 height:30 offset:[0,5]
		button btnApply "Apply" width:75 height:30 offset:[0,5] across:2 enabled:false
		button btnCancel "Cancel" width:75 height:30 offset:[0,5] enabled:false
	)
	
	-- Variables
	local selectedBone = undefined
	local lastFrame = -1
	local isCallbackActive = false
	local transformCallback = undefined
	local previewHelper = undefined  -- Point helper for preview
	local previewData = #()  -- Stored calculated positions for apply
	local previewStartFrame = 0
	local previewEndFrame = 0
	
	-- Check if an object is a Biped node
	function isBipedObject obj =
	(
		try
		(
			return (classof obj.controller == BipSlave_Control or \
					classof obj.controller == Vertical_Horizontal_Turn or \
					classof obj.controller == Bip_Float or \
					(classof obj.controller == subAnim and classof obj == Biped_Object))
		)
		catch
		(
			return false
		)
	)
	
	-- Set world position on a standard (non-Biped) object
	function setWorldPos obj f pos =
	(
		at time f
		(
			animate on
			(
				in coordsys world obj.pos = pos
			)
		)
	)
	
	-- Format speed value: round near-zero, limit decimal places
	function formatSpeed val =
	(
		if abs val < 0.001 then
			return "0.0 m/s"
		
		-- Round to 4 decimal places
		local rounded = (floor (val * 10000 + 0.5)) / 10000.0
		return (rounded as string) + " m/s"
	)
	
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
					txtSpeedX.text = formatSpeed speedXMS
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
					txtSpeedY.text = formatSpeed speedYMS
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
					txtSpeedZ.text = formatSpeed speedZMS
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
						txtSpeedX.text = (formatSpeed speedXMS) + " (into last)"
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
						txtSpeedY.text = (formatSpeed speedYMS) + " (into last)"
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
						txtSpeedZ.text = (formatSpeed speedZMS) + " (into last)"
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
	
	-- Calculate optimal blend frames based on speed difference
	function calcOptimalBlendFrames =
	(
		if selectedBone == undefined or not isValidNode selectedBone then return 30
		
		local targetSpeedMS = spnTargetSpeed.value
		local fps = frameRate as float
		local targetCmPerFrame = (targetSpeedMS * 100.0) / fps
		local endFrame = animationRange.end.frame as integer
		
		-- Get current speed at end of animation (last few frames)
		local posEnd = at time endFrame (in coordsys world selectedBone.transform.pos)
		local posPrev = at time (endFrame - 1) (in coordsys world selectedBone.transform.pos)
		
		-- Find max speed difference across selected axes
		local maxDiff = 0.0
		if chkX.checked then
		(
			local diff = abs (targetCmPerFrame - (posEnd.x - posPrev.x))
			if diff > maxDiff then maxDiff = diff
		)
		if chkY.checked then
		(
			local diff = abs (targetCmPerFrame - (posEnd.y - posPrev.y))
			if diff > maxDiff then maxDiff = diff
		)
		if chkZ.checked then
		(
			local diff = abs (targetCmPerFrame - (posEnd.z - posPrev.z))
			if diff > maxDiff then maxDiff = diff
		)
		
		-- Maximum acceleration = 5% of target speed per frame
		-- This keeps the curve gentle
		local maxAccel = abs (targetCmPerFrame * 0.05)
		if maxAccel < 0.01 then maxAccel = 0.01  -- safety floor
		
		-- Minimum frames needed = speedDifference / maxAcceleration
		local minFrames = (ceil (maxDiff / maxAccel)) as integer
		
		-- Clamp to available range
		local maxAvailable = endFrame - animationRange.start.frame - 1
		if minFrames < 5 then minFrames = 5
		if minFrames > maxAvailable then minFrames = maxAvailable
		if minFrames > 200 then minFrames = 200
		
		return minFrames
	)
	
	-- Clean up preview helper
	function cleanupPreview =
	(
		if previewHelper != undefined then
		(
			try
			(
				-- Disable motion trail before deleting
				previewHelper.showTrajectory = false
				delete previewHelper
			)
			catch()
			previewHelper = undefined
		)
		previewData = #()
		btnApply.enabled = false
		btnCancel.enabled = false
		btnPreview.text = "Preview"
	)
	
	-- Calculate smoothed positions (shared between preview and apply)
	function calculateSmoothedPositions =
	(
		if selectedBone == undefined or not isValidNode selectedBone then
		(
			format "ERROR: No valid object selected\n"
			return #()
		)
		if not chkX.checked and not chkY.checked and not chkZ.checked then
		(
			format "ERROR: No axes selected\n"
			return #()
		)
		
		local targetSpeedMS = spnTargetSpeed.value
		local blendFrames = spnBlendFrames.value as integer
		local endFrame = animationRange.end.frame as integer
		local startFrame = endFrame - blendFrames
		
		format "Calculating: startFrame=% endFrame=% blendFrames=% animStart=%\n" startFrame endFrame blendFrames animationRange.start.frame
		
		if startFrame < (animationRange.start.frame + 1) then
		(
			format "ERROR: Not enough frames (startFrame % < animStart+1 %)\n" startFrame (animationRange.start.frame + 1)
			return #()
		)
		
		local fps = frameRate as float
		local targetCmPerFrame = (targetSpeedMS * 100.0) / fps
		
		-- Get current speed at start of blend range (speed INTO startFrame)
		local posBeforeStart = at time (startFrame - 1) (in coordsys world selectedBone.transform.pos)
		local posAtStart = at time startFrame (in coordsys world selectedBone.transform.pos)
		local origSpeedX = posAtStart.x - posBeforeStart.x
		local origSpeedY = posAtStart.y - posBeforeStart.y
		local origSpeedZ = posAtStart.z - posBeforeStart.z
		
		-- FIXED last frame position
		local lastFramePos = at time endFrame (in coordsys world selectedBone.transform.pos)
		
		-- Debug
		local origMsX = origSpeedX / 100.0 * fps
		local origMsY = origSpeedY / 100.0 * fps
		local origMsZ = origSpeedZ / 100.0 * fps
		format "\n=== Root Smoothing Calculation ===\n"
		format "End frame: % [FIXED pos: %]\n" endFrame lastFramePos
		format "Blend: frame % to frame % (% frames)\n" startFrame (endFrame - 1) blendFrames
		format "Current speed at blend start: X=% Y=% Z=% m/s\n" origMsX origMsY origMsZ
		format "Target speed: % m/s = % cm/frame\n" targetSpeedMS targetCmPerFrame
		
		-- Pure backward extrapolation from fixed endFrame
		-- Speed ramps linearly from origSpeed (step 1) to targetSpeed (step N)
		local numSteps = blendFrames
		local results = #()
		
		local curX = lastFramePos.x
		local curY = lastFramePos.y
		local curZ = lastFramePos.z
		
		-- Walk backward from endFrame
		local backwardPositions = #()
		for step = numSteps to 1 by -1 do
		(
			local t = step as float / numSteps as float
			
			-- Lerp speed: at step 1 (earliest) use origSpeed, at step N (latest) use targetSpeed
			local speedX = origSpeedX + (targetCmPerFrame - origSpeedX) * t
			local speedY = origSpeedY + (targetCmPerFrame - origSpeedY) * t
			local speedZ = origSpeedZ + (targetCmPerFrame - origSpeedZ) * t
			
			-- Step backward
			curX = curX - speedX
			curY = curY - speedY
			curZ = curZ - speedZ
			
			local f = startFrame + step - 1
			
			-- For unselected axes, keep original position
			local origPos = at time f (in coordsys world selectedBone.transform.pos)
			local finalX = origPos.x
			local finalY = origPos.y
			local finalZ = origPos.z
			
			if chkX.checked then finalX = curX
			if chkY.checked then finalY = curY
			if chkZ.checked then finalZ = curZ
			
			append backwardPositions #(f, finalX, finalY, finalZ)
		)
		
		-- Reverse to ascending frame order
		for i = backwardPositions.count to 1 by -1 do
			append results backwardPositions[i]
		
		-- Add the fixed last frame
		append results #(endFrame, lastFramePos.x, lastFramePos.y, lastFramePos.z)
		
		-- Store frame range for apply
		previewStartFrame = startFrame
		previewEndFrame = endFrame
		
		return results
	)
	
	-- Create or update preview helper with motion trail
	function createPreview =
	(
		if selectedBone == undefined or not isValidNode selectedBone then
		(
			messageBox "Please select an object first!" title:"Root Smoothing"
			return false
		)
		
		if (isBipedObject selectedBone) then
		(
			messageBox "Smoothing is not supported for Biped objects.\nYou can still use the speed display to check Biped speeds." title:"Root Smoothing"
			return false
		)
		
		if not chkX.checked and not chkY.checked and not chkZ.checked then
		(
			messageBox "Please select at least one axis (X, Y, or Z) to smooth!" title:"Root Smoothing"
			return false
		)
		
		local blendFrames = spnBlendFrames.value as integer
		local endFrame = animationRange.end.frame as integer
		local startFrame = endFrame - blendFrames
		
		if startFrame < (animationRange.start.frame + 1) then
		(
			messageBox "Not enough frames for blending! Reduce blend frames or extend timeline." title:"Root Smoothing"
			return false
		)
		
		-- Calculate positions
		format "Creating preview for: % (class: %)\n" selectedBone.name (classof selectedBone)
		format "isBiped: %\n" (isBipedObject selectedBone)
		previewData = calculateSmoothedPositions()
		format "Preview data count: %\n" previewData.count
		if previewData.count == 0 then
		(
			messageBox "Failed to calculate positions. Check MAXScript Listener for details." title:"Root Smoothing"
			return false
		)
		
		-- Clean up old preview if exists
		if previewHelper != undefined then
		(
			try (delete previewHelper) catch()
			previewHelper = undefined
		)
		
		-- Create Point helper
		previewHelper = Point()
		previewHelper.name = "_RootSmooth_Preview"
		previewHelper.wirecolor = color 0 255 0  -- green
		previewHelper.size = 5
		previewHelper.centermarker = true
		previewHelper.axistripod = false
		previewHelper.cross = true
		previewHelper.box = false
		
		-- Key the preview helper at every frame
		-- First, key frames BEFORE the blend range to match bone position
		for f = animationRange.start.frame to (startFrame - 1) do
		(
			local bonePos = at time f (in coordsys world selectedBone.transform.pos)
			at time f
			(
				animate on
				(
					in coordsys world previewHelper.pos = bonePos
				)
			)
		)
		
		-- Key the blended frames
		for i = 1 to previewData.count do
		(
			local f = previewData[i][1]
			local px = previewData[i][2]
			local py = previewData[i][3]
			local pz = previewData[i][4]
			
			at time f
			(
				animate on
				(
					in coordsys world previewHelper.pos = [px, py, pz]
				)
			)
		)
		
		-- Enable motion trail on the preview helper
		previewHelper.showTrajectory = true
		
		-- Also enable trajectory on bone for comparison
		selectedBone.showTrajectory = true
		
		-- Select the preview helper so user can see it
		select previewHelper
		
		-- Enable Apply/Cancel buttons
		btnApply.enabled = true
		btnCancel.enabled = true
		btnPreview.text = "Update Preview"
		
		format "Preview created: %\n" previewHelper.name
		format "Green = preview path, adjust settings and click Update Preview.\n"
		format "Click Apply to transfer to bone, or Cancel to discard.\n"
		
		return true
	)
	
	-- Apply preview positions to the actual object
	function applyPreview =
	(
		if selectedBone == undefined or not isValidNode selectedBone then return false
		if previewData.count == 0 then return false
		if (isBipedObject selectedBone) then
		(
			messageBox "Smoothing is not supported for Biped objects." title:"Root Smoothing"
			return false
		)
		
		format "Applying % frames to: % (class: %)\n" (previewData.count - 1) selectedBone.name (classof selectedBone)
		
		with undo on
		(
			-- Apply all calculated positions (skip last frame - it's fixed)
			for i = 1 to (previewData.count - 1) do
			(
				local f = previewData[i][1]
				local px = previewData[i][2]
				local py = previewData[i][3]
				local pz = previewData[i][4]
				
				setWorldPos selectedBone f [px, py, pz]
				
				if i == 1 or i == (previewData.count - 1) then
					format "  Applied frame %: [%, %, %]\n" f px py pz
			)
		)
		
		-- Clean up preview
		selectedBone.showTrajectory = false
		cleanupPreview()
		
		-- Re-select the bone
		select selectedBone
		
		-- Recalculate speed display
		calculateSpeed()
		
		local targetSpeedMS = spnTargetSpeed.value
		local blendFrames = spnBlendFrames.value as integer
		format "Applied! Root smoothed to % m/s over % frames.\n" targetSpeedMS blendFrames
		messageBox ("Root smoothed to " + (targetSpeedMS as string) + " m/s over " + (blendFrames as string) + " frames.\nLast frame position preserved.") title:"Root Smoothing Applied"
		
		return true
	)
	
	-- Auto-calculate blend frames button
	on btnCalcBlend pressed do
	(
		local optimal = calcOptimalBlendFrames()
		spnBlendFrames.value = optimal
		lblBlendInfo.text = "(recommended: " + (optimal as string) + ")"
	)
	
	-- Update recommendation when target speed changes
	on spnTargetSpeed changed val do
	(
		if selectedBone != undefined then
		(
			local optimal = calcOptimalBlendFrames()
			lblBlendInfo.text = "(recommended: " + (optimal as string) + ")"
		)
	)
	
	-- Preview Button
	on btnPreview pressed do
	(
		-- Warn if blend frames is too low
		local optimal = calcOptimalBlendFrames()
		if spnBlendFrames.value < optimal then
		(
			local msg = "Blend frames (" + (spnBlendFrames.value as string) + ") is below recommended (" + (optimal as string) + ").\nThis may cause erratic positions.\n\nContinue anyway?"
			if not (queryBox msg title:"Root Smoothing Warning") then return()
		)
		createPreview()
	)
	
	-- Apply Button
	on btnApply pressed do
	(
		applyPreview()
	)
	
	-- Cancel Button
	on btnCancel pressed do
	(
		selectedBone.showTrajectory = false
		cleanupPreview()
		if selectedBone != undefined then select selectedBone
		format "Preview cancelled.\n"
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
		-- Clean up preview if active
		cleanupPreview()
		
		if selectedBone != undefined then
		(
			try (selectedBone.showTrajectory = false) catch()
		)
		
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
global boneSpeedDialog = createDialog boneSpeedRollout 200 530
