<div align="center">

<img src="media/meoware-launch.gif" alt="Meoware animated banner featuring a desktop cat" width="100%" />

Meoware
A little company for your desktop.

A Windows desktop cat that wanders, chases your cursor, jumps, and finds a seat on your open windows.

Features · Getting started · Controls · Roadmap · Asset licensing

</div>

Meet your new desktop roommate
Meoware brings a small animated cat to your Windows desktop. Pick it up, give it a window to perch on, or let it explore while you work.

Built by Hameem Bhai. Occasionally supervised by a cat.

This early build focuses on movement, interaction, and window perching. More personality, polish, and customization are planned. The banner is a stylized illustration, not a recording of the application.

Features
Animated character — separate idle, run, jump, and fall states.

Desktop wandering — alternates between resting and short runs.

Cursor chase — follows your cursor's horizontal position in short bursts without controlling your mouse.

Pick up and release — drag the cat, see its held reaction, and let gravity take over when released.

Window perching — lands on eligible window tops and follows its supporting window as it moves.

Support-aware falling — falls when its supporting window is maximized, minimized, closed, covered at the support point, or no longer supports it.

Manual and automatic jumps — trigger a hop or enable occasional automatic hops.

Quick controls — a right-click menu for behavior settings and quitting.

Getting started
Requirements
Windows 10 or 11 as the intended target. Compatibility varies by window type and display configuration.

Python 3.10 or newer, with a compatible PySide6 release.

The four required sprite sheets, obtained separately under their applicable license.

1. Open the project
Clone this repository using GitHub's Code button, or download and extract its source ZIP. Open PowerShell in the project folder.

2. Create a local environment
powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install pyside6
3. Add the character assets
Place your original transparent PNG sprite sheets in assets/. The character artwork is not included in this repository.

text
meoware/
├── main.py
├── README.md
├── .gitignore
├── media/
│   └── meoware-launch.gif
└── assets/                         # Local only; excluded from Git
    ├── 1_Cat_Idle-Sheet.png
    ├── 2_Cat_Run-Sheet.png
    ├── 3_Cat_Jump-Sheet.png
    └── 4_Cat_Fall-Sheet.png
The current loader expects a single horizontal row of equal-width frames, with no spacing between cells:

Sheet	Frame count
1_Cat_Idle-Sheet.png	8
2_Cat_Run-Sheet.png	10
3_Cat_Jump-Sheet.png	4
4_Cat_Fall-Sheet.png	4
The build was developed with the free demo of the Cat Character Asset Pack by OboroPixel. Check the creator's current download and license terms before use. Alternative artwork must match the expected filenames, frame counts, and layout, or the loader must be adapted.

4. Launch Meoware
powershell
.\.venv\Scripts\python.exe main.py
There is no activation step required when invoking the environment's Python directly. Quit the running cat and restart it after saving code changes; this build does not hot-reload.

Controls
Action	Result
Left-click and drag	Pick up and reposition the cat
Release the mouse	Drop the cat onto a surface below
Double-click	Toggle cursor chase
Right-click → Jump!	Trigger a jump when grounded
Right-click → Chase cursor	Toggle cursor chasing
Right-click → Occasional automatic hops	Toggle autonomous hops
Right-click → Perch on windows	Toggle window-top landing
Right-click → Pause wandering	Pause wandering and automatic hops; gravity remains active
Right-click → Resume wandering	Resume autonomous movement
Right-click → Quit Sidekick / Quit Meoware	Close the app; wording depends on the source revision
Some early source revisions retain the internal name Sidekick. This does not change the controls or behavior.

How window perching works
Meoware reads visible top-level window geometry through Windows APIs and treats eligible top edges as one-way landing surfaces. It does not move, resize, or modify other application windows.

Drop the cat from above a normal window to land on its top edge.

Leave enough room above the window for the cat to remain visible.

Moving a supporting window moves the perched cat with it.

Walking off an edge removes the cat's support.

Maximizing, minimizing, or closing the supporting window makes the cat fall.

Maximized windows are not platforms. If no eligible window catches the cat, it lands at the bottom of the desktop's usable area.

Covering the support point with another detected window can also make the cat fall.

Window geometry is checked periodically, so movement and support changes can have a short delay. Occlusion checks are approximate rather than pixel-perfect.

Try window perching
Open a normal, non-maximized window with space above it.

Disable automatic hops and pause wandering from the cat's menu.

Drag the cat above the window's top edge and release it.

Once it lands, move the window.

Maximize the supporting window: the cat should fall, not perch inside its top edge.

Configuration
Current settings live near the top of main.py. Restart the app after changing them.

Setting	Default	Purpose
SCALE	3	Integer sprite enlargement
SPEED	110	Horizontal movement speed in screen-coordinate units per second
FRAME_SECONDS	0.10	Time between animation frames
ART_FACES_RIGHT	True	Native direction of the sprite artwork
GRAVITY	1100	Downward acceleration
JUMP_SPEED	440	Initial upward jump speed
PAW_OFFSET	0	Scaled pixels of transparent padding beneath the paws
If the cat runs backward, change ART_FACES_RIGHT. If it visibly floats above surfaces, check the sprite padding before adjusting PAW_OFFSET.

Current limitations
Windows only; macOS and Linux are not supported by the native window-perching implementation.

Standard rectangular windows are the initial target. Unusual overlays, fullscreen apps, and mixed-DPI monitor arrangements need broader testing.

Collision uses the cat's horizontal center as its support point, not pixel-perfect paw geometry.

The fall animation is reused while the cat is held; there is no dedicated pickup sprite.

Jumps are vertical; airborne horizontal chasing is not implemented.

No attack or damage behavior is included in this build.

Menu choices are not saved between sessions.

No automatic updates or packaged Windows installer is included in the current source.

Window tracking and display compatibility remain experimental; behavior is not guaranteed across all Windows configurations.

Roadmap
Planned directions, not launch features or release-date commitments:

Finish replacing legacy Sidekick labels with Meoware.

Improve window detection and multi-monitor behavior.

Add persistent settings and a dedicated settings interface.

Refine idle behavior and personality.

Support additional characters and suitably licensed character packs.

Prepare a Windows executable after resolving asset-distribution permissions.

Expand animation support, including optional play-fight interactions where artwork permits.

Reporting issues
Please include:

Your Windows and Python versions.

Display count and scaling percentages.

Steps to reproduce the problem.

The full terminal traceback, if present.

A screenshot or short recording when the issue is visual.

Do not attach third-party sprite sheets unless their license permits redistribution.

Asset licensing
Character artwork and application source are separate licensing concerns.

The license supplied with the current character pack permits personal and commercial use and modification, but prohibits redistribution or resale. The third-party sprite sheets must not be committed to this public repository. Permission to bundle them in a downloadable executable needs clarification from the creator before distributing that build.

Obtain the pack directly from its creator, or use replacement artwork with suitable permissions. Credit alone does not replace permission.

The README banner is separate from the character pack and contains original illustrative cat artwork, not the third-party sprite sheets.

Check the repository's LICENSE file for source-code terms. If no source-code license has been added, do not assume that public availability grants unrestricted reuse rights.

Keep third-party artwork out of Git
Use these exclusions in .gitignore, adjusting the extracted-pack folder name if yours differs:

text
.venv/
__pycache__/
*.py[cod]
assets/
FreeCatCharacterAnimations/
build/
dist/
.dist/
*.spec
main_backup.py
Keep the public banner in media/, outside the ignored character-assets directory. If restricted files were already committed, adding them to .gitignore does not remove them from existing commits; address that before publishing.

Built with
Python · PySide6 / Qt · Windows APIs via ctypes

<div align="center">

Made by Hameem Bhai.

Small paws. Big desktop energy.

</div>