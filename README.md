# Crest Companion GTA Tool

A tool to assist with GTA V Cayo Perico fingerprint solving, Diamond Casino fingerprint solving and the No Save Heist replay glitch.

Download from here → [v1.1.1 Release](https://github.com/Abosmra/Crest-Companion-Tool/releases/download/v1.1.1/Crest.Companion.exe)

**Setup**

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

**Compile the code yourself**
```bash
pyinstaller --onefile --uac-admin --icon=icon.ico --name "Crest Companion" --add-data "assets;assets" main.py
```

**Run the app**

- Launch GTA V and ensure the game window is visible (windowed or borderless works best).
-- Hotkeys (while the app is running):
  - **F6**: Casino fingerprint helper
  - **F7**: Cayo fingerprint helper
  - **F8**: Toggle No Save
  - **End**: Exit

- **Note:** The tool currently only works on 16:9 resolutions.
- **Important:** When running, make sure the tool's terminal window does not cover or overlap the game window.

- **Tested 16:9 resolutions:** 1600x900, 1920x1080, 2560x1440.

**How to use No Save to replay heists**

How to use the nosave to replay heists:

- Make sure you have launched the tool, you could do it during the heist, but just make sure to launch it before to be safe in case you forget.

- Now just simply play the heist like you normally do. Of course make sure you have tested the tool before you start your heist. You don't have to test it every single time you start a heist, if it works one time it should work just fine in the future unless you install antivirus software or do other changes.

- Whenever you reach the end of the heist, make sure you activate nosave with F8 at least 10-20 seconds before making it to the heist ending.

- Now simply finish the heist. Wait till all of the finishing cutscenes end and you gain control of your GTA Online character in freeroam again.

- Go to pause menu > Online > Leave GTA Online to go back to story mode.

- Once you are fully loaded into story mode (make sure there are no spinning circles or anything) then you can disable nosave with F8.

- After you've disabled nosave, you can connect back into a GTA Online session and after joining back you should have your money and your heist preps should still be active.

- DO NOT ACCEPT JOIN INVITES OR OPEN THE ROCKSTAR GAMES LAUNCHER MENU (HOME BUTTON), WHILE IN STORY MODE AFTER DISABLING NOSAVE, AS THAT WILL FORCE SAVE YOUR GAME! ONLY JOIN A LOBBY FROM THE PAUSE MENU, PREFERABLY AN INVITE ONLY LOBBY!


**Special thanks**

Special thanks to [RedHeadEmile](https://github.com/RedHeadEmile) and [JU5TDIE](https://github.com/JU5TDIE).
