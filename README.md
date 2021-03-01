# LBT-2-PH
LBT-2-PH is a free toolkit for creating PHPP energy models from Ladybug Tools v1.0+ definitions. These components are updated to work with the new LBTv1.+ tools and replace the older 'IDF-2-PH' toolkit.

Folders:
- **examples:** .GH files with example workflow and components
- **ghuser:** The .ghuser files themselves. These should be copied into your Grasshopper 'UserObjects' folder. By default that is something like "C:\Users\-you-user-name-here-\AppData\Roaming\Grasshopper\UserObjects\\..."
- **ghuser_py:** The python code for each of the ghuser objects for reference. You don't acutally need this anyplace to run as its embedded in the components. It is included here purely for reference purposes.
- **rh_plugin_v6:** The Rhino-side tools for **Rhino-6**. Copy the folder "PHPPexport {82540871-2420-4c7f-8efa-78b7d078cbfe}" into your Rhino-6 'PythonPlugins' folder. By default that is sommething like "C:\Users\-you-user-name-here-\AppData\Roaming\McNeel\Rhinoceros\6.0\Plug-ins\PythonPlugins\\...".
Next, Install the custom toolbar "Rhino_Toolbar_PHPP.rui" into your Rhino instance to get access to all these tools.
--or--
- **rh_plugin_v7:**  The Rhino-side tools for **Rhino-7**. Copy the folder "PH-Tools (9c8b1271-a5e0-40bd-9685-6fd572c4a809)" into your Rhino-7 'PythonPlugins' folder. By default that is sommething like "C:\Users\-you-user-name-here-\AppData\Roaming\McNeel\Rhinoceros\7.0\Plug-ins\PythonPlugins\\...".
Next, Install the custom toolbar "PH_Tools.rui" into your Rhino instance to get access to all these tools.
- **scripts:** The external .py libraries which are used to execute the LB-2-PH. Copy the 'LBT2PH' folder into your Rhino 'scripts' folder. By default that is sommething like "C:\Users\-you-user-name-here-\AppData\Roaming\McNeel\Rhinoceros\7.0\scripts\\..."

Reboot Rhino. Should be working now.

# INSTALL
For detailed installation instructions, check out the website here: http://www.passivehousetools.com/lbt2ph.html

# HOW-TO
For more information on the use of these tools, check out the YouTube playlist here:
https://youtube.com/playlist?list=PLi6KNBJLE8H8pne3QIdlozwWENIF3VV1f

and the Passive House Tools website:
http://www.PassiveHouseTools.com
