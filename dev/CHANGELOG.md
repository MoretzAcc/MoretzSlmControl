
# Changelog

---


### 26-09-15

Version Bump: 0.3.3.post3

##### Added
- If you click a window multiple times, a small cross appears in the top right corner, to close the window
  - This was added in case one accidentally opens a window on the primary screen

##### Changed
- Window name is now "{Display Name} - {Screen UID}"


### 26-09-14

Version Bump: 0.3.3

##### Added:
- Changing Zernike Coefficients is now accessible via Heros
- CHANGELOG.md
- Added host_id into UID generation
- Added monitor serial numbers into UID generation

##### Changed:
- Added Date to console timestamp
- Console is now resizable
- more exhaustive logging on exiting the app

---

### 26-09-09

Version Bump: 0.3.1 -> 0.3.2

##### Breaking Changes:

- getPatternInclusion now returns dict instead of tuple of bools

##### Added:

- Toggling of SLM windows is now exposed into api
- log that session initialized
- log that heros activated

##### Changed:

- Moved Total Hologram to top left
- Crossing out inactive holograms instead of making them gray
- Total sum is also crossed out when SLM window is deactivated
- when screen is disabled, cross out the preview of the sums of the holograms
- Changing a Pattern will set it to active

##### Fixed:

- add timestamps to the logs
- Error message is green (Windows) "Error importing base aberration: cannot identify image file 'C:\\Users\\morit\\Downloads\\SteelSeriesGG112.0.0Setup.exe.bmp'"
- Refresh Button now actually refreshes the screen list
- using scroll wheel to change slider value now actually works

##### Rejected:

- Default Hologram that displays 0, 255 with a text printed on top, and in the center is a phase vortex to generate donut