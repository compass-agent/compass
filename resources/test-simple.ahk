#Requires AutoHotkey v2.0
; Ctrl+Alt+T = type the compass prompt

^!t::{
    text := "I have this 3-story steel building in SAP2000. Analyze it, optimize the design for material and cost, and show me the results. Walk me through each step and let me review before finalizing."
    Loop Parse, text {
        SendText A_LoopField
        Sleep 10
    }
}

; Ctrl+Alt+R = type UI verification question
^!r::{
    text := "Help me check number of eigenmodes were actually added"
    Loop Parse, text {
        SendText A_LoopField
        Sleep 50
    }
}
