# Final Fantasy 7 PS1 Disc CSR Patches (IndividualContributor)

Apply the patches to your FF7 NTSC/US PS1 .bin files.

## Steps

1. Go to https://www.romhacking.net/patch/
2. Select your original .bin file, ignore the "file too big" warning
3. Select the patch .ppf file
4. Click the "Apply patch" button

Your browser should download a new patched version of the disc.

You can burn the patched version to disc or load it up in an emulator (I used duckstation version 0.1-7371-gb2577ef8b (dev) for testing). I used ImgBurn with write speed 16x on Verbatim CD-R 700MB discs.

Make sure to choose the correct patch .ppf file for the correct disc you are trying to patch.

## Details

These patches remove most if not all FMVs, shortens some in-game cutscenes, and reduces some mashing sequences. All skips and scenarios where a player is required to provide input such as movement or making a choice has been untouched. The idea with this CSR is to provide a stable practice version of the game so I've avoided removing anything that requires the player to interact with the controls, other than the long mashing scenarios as mentioned.

## Troubleshooting

Make sure your FF7 .bin and .cue files for all discs are in the same directory, and the .bin and .cue for each disc are named exactly the same. e.g.  

- FF7 Disc1 (patched).bin  
- FF7 Disc1 (patched).cue  
- FF7 Disc2 (patched).bin  
- FF7 Disc2 (patched).cue  
- FF7 Disc3.bin  
- FF7 Disc3.cue  

And if you use a .m3u file like I do in DuckStation make sure to update this file to point to the correct patched version of the discs. e.g.

```text
C:\Users\Deez\FF7\FF7 Disc1 (patched).cue
C:\Users\Deez\FF7\FF7 Disc2 (patched).cue
C:\Users\Deez\FF7\FF7 Disc3.cue
```
