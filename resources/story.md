## Define the videos used in Website

### 1. Hero Video [1 min]

**Setup & Connection [15 seconds]**
- Show Compass and SAP2000 side by side [10 sec] - giving general overview of the interface
- User makes SAP connection [5 sec]

**Initial Analysis Request [25 seconds]**
- User inserts main prompt [15 sec] - Use **Ctrl+Alt+T**:
  > "I have this 3-story steel building in SAP2000. Analyze it, optimize the design for material and cost, and show me the results. Walk me through each step and let me review before finalizing."
- Compass responds with analysis plan [10 sec]

**AI Actions & Follow-up [20 seconds]**
- Compass takes automated actions [15 sec]
- User asks UI verification question [5 sec]:
  > "Help me check number of eigenmodes were actually added"
- Compass performs UI actions and returns results [10 sec] (this overlaps with previous timing)







### 2. AgentHub Video [1 min]
- *Content to be defined*

---

## AutoHotkey Script Setup

### Commands to run the typing automation script:

**To start the script:**
```
cd resources
& "C:\Program Files\AutoHotkey\v2\AutoHotkey.exe" test-simple.ahk
```

**To restart/reload the script:**
```
taskkill /f /im AutoHotkey64.exe
cd resources
& "C:\Program Files\AutoHotkey\v2\AutoHotkey.exe" test-simple.ahk
```

**Available shortcuts:**
- **Ctrl+Alt+T** = Full compass prompt with typing effect
- **Ctrl+Alt+R** = UI verification question ("Help me check number of eigenmodes were actually added")
