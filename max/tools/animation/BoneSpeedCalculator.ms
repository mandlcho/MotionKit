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

	group "Curve Preview"
	(
		-- Animator-friendly names, engine curve family in parentheses
		dropdownlist ddlPreviewMode "" \
			items:#( \
				"Movement Path  (Root Loc)", \
				"Turning / Rotation  (Root Rot)", \
				"Movement Speed  (Root Vec)" \
			) \
			width:168 offset:[-5,5]
		button btnGeneratePreview "Generate Curve Preview" width:160 height:28 offset:[0,5]
		button btnClearPreview "Clear Preview" width:160 height:22 offset:[0,5] enabled:false
		label lblPreviewStatus "" align:#left offset:[5,3]
	)

	-- Variables
	local selectedBone      = undefined
	local lastFrame         = -1
	local isCallbackActive  = false
	local transformCallback = undefined
	local curvePreviewHelper = undefined

	-- Format speed value
	function formatSpeed val =
	(
		if abs val < 0.001 then return "0.0 m/s"
		local rounded = (floor (val * 10000 + 0.5)) / 10000.0
		return (rounded as string) + " m/s"
	)

	-- Calculate Speed
	function calculateSpeed =
	(
		if selectedBone == undefined or not isValidNode selectedBone then return()

		local currentF         = sliderTime.frame as integer
		local fps              = frameRate as float
		local timeDelta        = 1.0 / fps
		local conversionFactor = 100.0

		if currentF < animationRange.end.frame then
		(
			local pos1 = in coordsys world selectedBone.transform.pos
			at time (currentF + 1)
			(
				local pos2 = in coordsys world selectedBone.transform.pos
				if chkX.checked then txtSpeedX.text = formatSpeed ((pos2.x - pos1.x) / timeDelta / conversionFactor)
				else txtSpeedX.text = "--"
				if chkY.checked then txtSpeedY.text = formatSpeed ((pos2.y - pos1.y) / timeDelta / conversionFactor)
				else txtSpeedY.text = "--"
				if chkZ.checked then txtSpeedZ.text = formatSpeed ((pos2.z - pos1.z) / timeDelta / conversionFactor)
				else txtSpeedZ.text = "--"
			)
			lblCurrentFrame.text = "Current Frame: " + (currentF as string)
		)
		else if currentF == animationRange.end.frame and currentF > animationRange.start.frame then
		(
			at time (currentF - 1)
			(
				local pos1 = in coordsys world selectedBone.transform.pos
				at time currentF
				(
					local pos2 = in coordsys world selectedBone.transform.pos
					if chkX.checked then txtSpeedX.text = (formatSpeed ((pos2.x - pos1.x) / timeDelta / conversionFactor)) + " (into last)"
					else txtSpeedX.text = "--"
					if chkY.checked then txtSpeedY.text = (formatSpeed ((pos2.y - pos1.y) / timeDelta / conversionFactor)) + " (into last)"
					else txtSpeedY.text = "--"
					if chkZ.checked then txtSpeedZ.text = (formatSpeed ((pos2.z - pos1.z) / timeDelta / conversionFactor)) + " (into last)"
					else txtSpeedZ.text = "--"
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

	-- Redraw callback
	function updateCallback =
	(
		local currentF = sliderTime.frame as integer
		if currentF != lastFrame then
		(
			lastFrame = currentF
			boneSpeedRollout.calculateSpeed()
		)
	)

	-- Clear curve preview helper
	function clearCurvePreview =
	(
		if curvePreviewHelper != undefined then
		(
			try
			(
				curvePreviewHelper.showTrajectory = false
				delete curvePreviewHelper
			)
			catch()
			curvePreviewHelper = undefined
		)
		btnClearPreview.enabled = false
		btnGeneratePreview.text = "Generate Curve Preview"
		lblPreviewStatus.text = ""
	)

	-- Generate curve preview helper
	function generateCurvePreview =
	(
		if selectedBone == undefined or not isValidNode selectedBone then
		(
			messageBox "Please pick an object first!" title:"Curve Preview"
			return()
		)

		-- Clean up existing
		if curvePreviewHelper != undefined then
		(
			try (delete curvePreviewHelper) catch()
			curvePreviewHelper = undefined
		)

		local startF    = animationRange.start.frame as integer
		local endF      = animationRange.end.frame as integer
		local fps       = frameRate as float
		local modeIndex = ddlPreviewMode.selection

		-- Graph origin = bone's world position at first frame
		local graphOrigin = at time startF (in coordsys world selectedBone.transform.pos)

		-- Graph time axis: runs along the character's direction of travel
		-- so the curve always lies beside the path, never across it.
		-- For rotation-only clips (minimal displacement) fall back to the
		-- bone's local facing direction at startF.
		local posEnd    = at time endF (in coordsys world selectedBone.transform.pos)
		local moveDelta = posEnd - graphOrigin
		local graphForward

		if (length moveDelta) > 0.1 then
			graphForward = normalize moveDelta
		else
			-- No meaningful translation — use the bone's local X axis (facing dir)
			graphForward = at time startF (normalize selectedBone.transform.row1)

		-- Value axis is always world Z (up), so the graph always reads
		-- upright regardless of which direction the character faces.
		local graphUp = [0, 0, 1]

		-- Each frame advances 5cm along graphForward (time axis)
		local frameSpacing = 5.0

		-- Create Point helper (orange = preview)
		curvePreviewHelper = Point()
		curvePreviewHelper.size = 3
		curvePreviewHelper.centermarker = true
		curvePreviewHelper.axistripod   = false
		curvePreviewHelper.cross        = true
		curvePreviewHelper.box          = false
		curvePreviewHelper.wirecolor    = color 255 180 0

		-- ----------------------------------------------------------------
		-- MODE 1: Movement Path  (Root Loc)
		-- Keys the helper at the bone's exact world position each frame.
		-- The trajectory draws the 3D path the character travels through
		-- space — directly equivalent to the _RootLoc curve in-engine.
		-- ----------------------------------------------------------------
		if modeIndex == 1 then
		(
			curvePreviewHelper.name = "_CurvePreview_RootLoc"

			for f = startF to endF do
			(
				local bonePos = at time f (in coordsys world selectedBone.transform.pos)
				at time f animate on (in coordsys world curvePreviewHelper.pos = bonePos)
			)

			lblPreviewStatus.text = "Path: " + ((endF - startF + 1) as string) + " frames keyed"
		)

		-- ----------------------------------------------------------------
		-- MODE 2: Turning / Rotation  (Root Rot)
		-- Plots accumulated yaw (rotation around world Z) as a 2D graph.
		--   graphForward axis = time (frame index × spacing)
		--   world Z axis      = total degrees turned since frame 0
		-- Yaw is unwrapped so a continuous spin plots as a smooth slope,
		-- not a sawtooth. Equivalent to the _RootRot curve in-engine.
		-- ----------------------------------------------------------------
		else if modeIndex == 2 then
		(
			curvePreviewHelper.name = "_CurvePreview_RootRot"

			-- 1 degree = 1 cm on the value axis
			local rotScale = 1.0

			local prevYaw        = 0.0
			local accumulatedYaw = 0.0

			for f = startF to endF do
			(
				local q          = at time f (in coordsys world selectedBone.transform.rotation)
				local eu         = quatToEuler q
				local currentYaw = eu.z  -- Z Euler = yaw in Max's Z-up world

				if f == startF then
				(
					prevYaw        = currentYaw
					accumulatedYaw = 0.0
				)
				else
				(
					local delta = currentYaw - prevYaw
					if delta >  180 then delta -= 360
					if delta < -180 then delta += 360
					accumulatedYaw += delta
					prevYaw = currentYaw
				)

				local fwdComp = ((f - startF) as float * frameSpacing) * graphForward
				local upComp  = (accumulatedYaw * rotScale) * graphUp
				local gPos    = graphOrigin + fwdComp + upComp
				at time f animate on (in coordsys world curvePreviewHelper.pos = gPos)
			)

			lblPreviewStatus.text = "Rotation: forward=time  up=yaw (deg)"
		)

		-- ----------------------------------------------------------------
		-- MODE 3: Movement Speed  (Root Vec)
		-- Plots per-frame speed as a 2D graph.
		--   graphForward axis = time (frame index × spacing)
		--   world Z axis      = speed (always positive, reads upward)
		-- Single axis checked → that axis's speed magnitude.
		-- Multiple axes checked → XYZ magnitude (total speed).
		-- Equivalent to the _Vec velocity curve in-engine.
		-- ----------------------------------------------------------------
		else
		(
			curvePreviewHelper.name = "_CurvePreview_RootVec"

			-- 30 cm per m/s keeps the graph roughly square for a typical
			-- 5 m/s run over 30 frames, readable without zooming
			local speedScale = 30.0

			local axisCount = 0
			if chkX.checked then axisCount += 1
			if chkY.checked then axisCount += 1
			if chkZ.checked then axisCount += 1

			for f = startF to endF do
			(
				local speedVal = 0.0

				if f < endF then
				(
					local pos1 = at time f     (in coordsys world selectedBone.transform.pos)
					local pos2 = at time (f+1) (in coordsys world selectedBone.transform.pos)
					local inv  = fps / 100.0  -- cm/frame → m/s

					local vx = (pos2.x - pos1.x) * inv
					local vy = (pos2.y - pos1.y) * inv
					local vz = (pos2.z - pos1.z) * inv

					if axisCount == 1 then
					(
						-- abs: speed is always positive so the graph reads
						-- upward regardless of which world direction the
						-- character moves in
						if      chkX.checked then speedVal = abs vx
						else if chkY.checked then speedVal = abs vy
						else                      speedVal = abs vz
					)
					else
					(
						local sumSq = 0.0
						if chkX.checked then sumSq += vx * vx
						if chkY.checked then sumSq += vy * vy
						if chkZ.checked then sumSq += vz * vz
						speedVal = sqrt sumSq
					)
				)

				local fwdComp = ((f - startF) as float * frameSpacing) * graphForward
				local upComp  = (speedVal * speedScale) * graphUp
				local gPos    = graphOrigin + fwdComp + upComp
				at time f animate on (in coordsys world curvePreviewHelper.pos = gPos)
			)

			lblPreviewStatus.text = "Speed: forward=time  up=m/s"
		)

		curvePreviewHelper.showTrajectory = true
		select curvePreviewHelper

		btnClearPreview.enabled = true
		btnGeneratePreview.text = "Regenerate"

		format "Curve preview created: %\n" curvePreviewHelper.name
	)

	-- Pick Bone Handler
	on btnPickBone picked obj do
	(
		if isValidNode obj then
		(
			if transformCallback != undefined then
			(
				try (deleteChangeHandler transformCallback) catch()
				transformCallback = undefined
			)

			selectedBone = obj
			lblSelectedBone.text = "Selected: " + obj.name
			btnPickBone.text = obj.name

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

			calculateSpeed()
		)
		else
		(
			messageBox "Please select a valid object!"
		)
	)

	-- Axis checkbox handlers
	on chkX changed state do ( if selectedBone != undefined then calculateSpeed() )
	on chkY changed state do ( if selectedBone != undefined then calculateSpeed() )
	on chkZ changed state do ( if selectedBone != undefined then calculateSpeed() )

	-- Curve Preview handlers
	on btnGeneratePreview pressed do ( generateCurvePreview() )
	on btnClearPreview pressed do
	(
		clearCurvePreview()
		if selectedBone != undefined then select selectedBone
	)

	-- Auto-Update Toggle
	on chkAutoUpdate changed state do
	(
		if state then
		(
			if not isCallbackActive then
			(
				try ( registerRedrawViewsCallback updateCallback; isCallbackActive = true ) catch()
			)
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
			if isCallbackActive then
			(
				try ( unregisterRedrawViewsCallback updateCallback; isCallbackActive = false ) catch()
			)
			if transformCallback != undefined then
			(
				try ( deleteChangeHandler transformCallback; transformCallback = undefined ) catch()
			)
		)
	)

	-- Initialize on open
	on boneSpeedRollout open do
	(
		if chkAutoUpdate.checked then
		(
			try ( registerRedrawViewsCallback updateCallback; isCallbackActive = true ) catch()
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
		clearCurvePreview()
		if isCallbackActive then
		(
			try ( unregisterRedrawViewsCallback updateCallback; isCallbackActive = false ) catch()
		)
		if transformCallback != undefined then
		(
			try ( deleteChangeHandler transformCallback; transformCallback = undefined ) catch()
		)
	)
)

-- Create Dialog and store reference
global boneSpeedDialog = createDialog boneSpeedRollout 200 510
