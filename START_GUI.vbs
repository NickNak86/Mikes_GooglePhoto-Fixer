' Google Photos Manager - Silent GUI Launcher
' Launches the PhotoManager.py GUI without showing a console window

Set objShell = CreateObject("WScript.Shell")
Set objFSO = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
strScriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)

' Change to the script directory
objShell.CurrentDirectory = strScriptDir

' Launch Python GUI without console window
' Using pythonw.exe to avoid console window
objShell.Run "pythonw PhotoManager.py", 0, False

' Alternative if pythonw is not available:
' objShell.Run "python PhotoManager.py", 0, False

Set objShell = Nothing
Set objFSO = Nothing
