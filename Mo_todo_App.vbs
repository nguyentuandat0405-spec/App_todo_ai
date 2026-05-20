Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c streamlit run app.py", 1, False
