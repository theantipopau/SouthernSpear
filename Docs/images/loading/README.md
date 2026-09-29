# Loading-screen art, one image per operation

Drop an image here named for the operation's art key, then run `Tools/Unreal/setup_ui.py` with
`SS_UI_LOADING_ONLY=1`. It is imported as `/SouthernSpearUI/Textures/T_SS_Load_<key>`, and the loading
screen shows it whenever that map loads. An operation without an image shows the key art.

| File | Operation |
|---|---|
| `RedGum.png` | Red Gum Station |
| `DryRiver.png` | Dry River |
| `Saltbush.png` | Saltbush Flats |
| `SelatCanal.png` | Selat Canal |
| `Bluestone.png` | Bluestone Quarry |

`.jpg` works too. 16:9 at 1920×1080 or larger; the screen crops to fill, and the bottom third sits under the
text band, so keep the subject in the upper two thirds. The keys come from `SSOperations.h`, the one list the front
end and the loading screen share: a new operation is added there first.
