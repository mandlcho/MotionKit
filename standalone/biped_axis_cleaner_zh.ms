-- ============================================
-- Biped 轴向清理 (Biped Axis Cleaner)
-- 独立版本 — 无需安装 MotionKit
--
-- 使用方法:
--   MAXScript > Run Script，选择此文件
--
-- 工作流程:
--   1. 选择质心骨骼（或点击自动检测）
--   2. 选择角色的前进轴向
--   3. 点击「创建辅助体」— 生成一个前向轴已线性化的辅助体
--   4. 在视口中检查效果
--   5. 点击「应用到质心」— 将修改写入质心骨骼（可用 Ctrl+Z 撤销）
-- ============================================

global BipedAxisCleanerTool

struct BipedAxisCleanerStruct
(
    pelvisNode = undefined,

    fn autoDetect =
    (
        local foundPelvis = undefined
        for obj in objects do
        (
            if classOf obj == Biped_Object then
            (
                if (findString (toLower obj.name) "pelvis") != undefined then
                (
                    foundPelvis = obj
                    exit
                )
            )
        )
        return foundPelvis
    ),

    fn samplePositions node startFrame endFrame =
    (
        local positions = #()
        local savedTime = sliderTime
        for f = startFrame to endFrame do
        (
            sliderTime = f
            append positions node.transform.pos
        )
        sliderTime = savedTime
        return positions
    ),

    fn backupNodeName = "BipedAxisCleaner_OrigBackup",

    fn findBackup pelvisName startFrame endFrame =
    (
        local node = getNodeByName (this.backupNodeName())
        if node == undefined then return undefined
        try
        (
            if node.mk_pelvisName != pelvisName then return undefined
            if node.mk_startFrame != startFrame  then return undefined
            if node.mk_endFrame   != endFrame    then return undefined
        )
        catch ( return undefined )
        return node
    ),

    fn createBackup pelvisNode startFrame endFrame =
    (
        local old = getNodeByName (this.backupNodeName())
        if old != undefined then delete old

        local origPos = this.samplePositions pelvisNode startFrame endFrame

        local backupNode = Dummy name:(this.backupNodeName()) boxsize:[1,1,1]
        backupNode.isHidden = true

        local ca = attributes "BipedAxisCleanerMeta"
        (
            parameters main
            (
                mk_pelvisName type:#string
                mk_startFrame type:#integer default:0
                mk_endFrame   type:#integer default:100
            )
        )
        custAttributes.add backupNode ca
        backupNode.mk_pelvisName = pelvisNode.name
        backupNode.mk_startFrame = startFrame
        backupNode.mk_endFrame   = endFrame

        local savedTime = sliderTime
        with animate on
        (
            for i = 1 to origPos.count do
            (
                sliderTime = startFrame + i - 1
                backupNode.pos = origPos[i]
            )
        )
        sliderTime = savedTime
        return backupNode
    ),

    fn clearBackupData =
    (
        local node = getNodeByName (this.backupNodeName())
        if node != undefined then delete node
    ),

    fn helperNodeName = "BipedAxisCleaner_Helper",

    fn createHelper pelvisNode axisIndex startFrame endFrame =
    (
        if pelvisNode == undefined then
        (
            messageBox "请先指定质心骨骼。" title:"Biped 轴向清理"
            return undefined
        )

        local old = getNodeByName (this.helperNodeName())
        if old != undefined then delete old

        local totalFrames = endFrame - startFrame + 1
        local savedTime   = sliderTime

        local backup  = this.findBackup pelvisNode.name startFrame endFrame
        local origPos = if backup != undefined then
            this.samplePositions backup     startFrame endFrame
        else
            this.samplePositions pelvisNode startFrame endFrame

        local startFwd = if axisIndex == 1 then origPos[1].x
                         else if axisIndex == 2 then origPos[1].y
                         else origPos[1].z

        local endFwd   = if axisIndex == 1 then origPos[totalFrames].x
                         else if axisIndex == 2 then origPos[totalFrames].y
                         else origPos[totalFrames].z

        local newHelper = Dummy name:(this.helperNodeName()) boxsize:[8,8,8]
        newHelper.wirecolor = (color 80 200 255)

        with animate on
        (
            for i = 1 to totalFrames do
            (
                local t = if totalFrames > 1 then
                    (i - 1) as float / (totalFrames - 1) as float
                else 0.0

                local linearFwd = startFwd + (endFwd - startFwd) * t
                local origP     = origPos[i]

                local newPos = if axisIndex == 1 then point3 linearFwd origP.y origP.z
                               else if axisIndex == 2 then point3 origP.x linearFwd origP.z
                               else point3 origP.x origP.y linearFwd

                sliderTime = startFrame + i - 1
                newHelper.pos = newPos
            )
        )
        sliderTime = savedTime

        return newHelper
    ),

    fn deleteHelper =
    (
        local node = getNodeByName (this.helperNodeName())
        if node != undefined then delete node
    ),

    fn applyHelperToPelvis pelvisNode axisIndex amount startFrame endFrame =
    (
        if pelvisNode == undefined then
        (
            messageBox "请先指定质心骨骼。" title:"Biped 轴向清理"
            return false
        )

        local helperNode = getNodeByName (this.helperNodeName())
        if helperNode == undefined then
        (
            messageBox "未找到辅助体，请先点击「创建辅助体」。" title:"Biped 轴向清理"
            return false
        )

        local totalFrames = endFrame - startFrame + 1
        local savedTime   = sliderTime

        local backup = this.findBackup pelvisNode.name startFrame endFrame
        if backup == undefined then
            backup = this.createBackup pelvisNode startFrame endFrame

        local helperPos = this.samplePositions helperNode startFrame endFrame
        local origPos   = this.samplePositions backup     startFrame endFrame

        local blendWeight = amount / 100.0
        local targetPos = #()
        for i = 1 to totalFrames do
        (
            local t = origPos[i] + (helperPos[i] - origPos[i]) * blendWeight
            append targetPos t
        )

        local currentPos = this.samplePositions pelvisNode startFrame endFrame
        sliderTime = savedTime

        with animate on
        (
            for i = 1 to totalFrames do
            (
                sliderTime = startFrame + i - 1
                local delta = targetPos[i] - currentPos[i]
                move pelvisNode delta
            )
        )

        sliderTime = savedTime
        return true
    )
)

BipedAxisCleanerTool = BipedAxisCleanerStruct()

-- ============================================================
-- 对话框
-- ============================================================
rollout BipedAxisCleanerDialog "Biped 轴向清理" width:460 height:301
(
    group "源骨骼"
    (
        button autoDetectBtn "自动检测 Biped 质心" pos:[20,22] width:410 height:24
        label pelvisLbl "质心:" pos:[20,57]  width:55 align:#left
        edittext pelvisEdit ""  pos:[78,54]  width:200 height:20 readOnly:true
        pickbutton pelvisPickBtn "拾取" pos:[285,54] width:60 height:20
        button pelvisSelBtn "选取"      pos:[352,54] width:68 height:20
    )

    group "世界前方轴向"
    (
        label axisLbl "角色的前进方向是哪个世界轴?" pos:[20,100] width:400 align:#left
        radiobuttons forwardAxisRadio labels:#("X", "Y", "Z") pos:[20,120] default:2 columns:3
    )

    group "帧范围"
    (
        checkbox useTimelineCB "使用时间轴范围" pos:[20,173] width:160 checked:true
        label startLbl "开始:" pos:[195,173] width:40 align:#left
        spinner startSpn "" pos:[238,171] width:70 height:20 type:#integer range:[-100000,100000,0] enabled:false
        label endLbl "结束:"  pos:[320,173] width:35 align:#left
        spinner endSpn ""   pos:[355,171] width:70 height:20 type:#integer range:[-100000,100000,100] enabled:false
    )

    label statusLabel "" pos:[20,214] width:420 height:16 align:#center
    progressBar damperProgress "" pos:[20,234] width:420 height:10 value:0 color:(color 80 200 120)

    button createHelperBtn "创建辅助体" pos:[20,254]  width:130 height:36
    button applyBtn        "应用到质心" pos:[160,254] width:145 height:36
    button deleteHelperBtn "删除辅助体" pos:[315,254] width:125 height:36

    on BipedAxisCleanerDialog open do
    (
        startSpn.value = animationRange.start.frame as integer
        endSpn.value   = animationRange.end.frame as integer
    )

    on useTimelineCB changed state do
    (
        startSpn.enabled = not state
        endSpn.enabled   = not state
        if state then
        (
            startSpn.value = animationRange.start.frame as integer
            endSpn.value   = animationRange.end.frame as integer
        )
    )

    on autoDetectBtn pressed do
    (
        local pelvis = BipedAxisCleanerTool.autoDetect()
        if pelvis != undefined then
        (
            BipedAxisCleanerTool.pelvisNode = pelvis
            pelvisEdit.text = pelvis.name
            statusLabel.text = "已检测: " + pelvis.name
        )
        else
            statusLabel.text = "未找到 Biped 质心，请手动拾取"
    )

    on pelvisPickBtn picked obj do
    (
        BipedAxisCleanerTool.pelvisNode = obj
        pelvisEdit.text = obj.name
    )

    on pelvisSelBtn pressed do
    (
        if selection.count != 1 then
        (
            messageBox "请先选择一个对象。" title:"Biped 轴向清理"
            return false
        )
        BipedAxisCleanerTool.pelvisNode = selection[1]
        pelvisEdit.text = selection[1].name
    )

    on createHelperBtn pressed do
    (
        if BipedAxisCleanerTool.pelvisNode == undefined then
        (
            messageBox "请先指定质心骨骼。" title:"Biped 轴向清理"
            return false
        )

        statusLabel.text = "正在创建辅助体..."
        damperProgress.value = 30
        windows.processPostedMessages()

        local result = BipedAxisCleanerTool.createHelper \
            BipedAxisCleanerTool.pelvisNode \
            forwardAxisRadio.state \
            startSpn.value \
            endSpn.value

        damperProgress.value = 100
        windows.processPostedMessages()

        if result != undefined then
        (
            select result
            statusLabel.text = result.name + "  (前向轴已线性化)"
        )
        else
            statusLabel.text = "创建辅助体失败"

        sleep 0.5
        damperProgress.value = 0
    )

    on applyBtn pressed do
    (
        if BipedAxisCleanerTool.pelvisNode == undefined then
        (
            messageBox "请先指定质心骨骼。" title:"Biped 轴向清理"
            return false
        )

        local helperCheck = getNodeByName (BipedAxisCleanerTool.helperNodeName())
        if helperCheck == undefined then
        (
            messageBox "未找到辅助体，请先点击「创建辅助体」。" title:"Biped 轴向清理"
            return false
        )

        local msg = substituteString "线性化 {0} 的前向轴?\n\n可用 Ctrl+Z 撤销。" "{0}" BipedAxisCleanerTool.pelvisNode.name
        if not (queryBox msg title:"Biped 轴向清理") then return false

        statusLabel.text = "正在应用..."
        damperProgress.value = 20
        windows.processPostedMessages()

        local ok = BipedAxisCleanerTool.applyHelperToPelvis \
            BipedAxisCleanerTool.pelvisNode \
            forwardAxisRadio.state \
            100 \
            startSpn.value \
            endSpn.value

        damperProgress.value = 100
        windows.processPostedMessages()

        if ok then
            statusLabel.text = "完成 — 前向轴已线性化"
        else
            statusLabel.text = "失败"

        sleep 0.5
        damperProgress.value = 0
    )

    on deleteHelperBtn pressed do
    (
        BipedAxisCleanerTool.deleteHelper()
        statusLabel.text = "辅助体已删除"
    )

    on BipedAxisCleanerDialog close do
    (
        -- 关闭后辅助体保留在场景中，方便检查
    )
)

try (destroyDialog BipedAxisCleanerDialog) catch()
createDialog BipedAxisCleanerDialog
