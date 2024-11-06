
# FF7 CutScenes Removed Change log

v(Major).(Minor).(Patch)

## v0.4.7

- Moved the break scene to before the spiral hut scene to test a bug fix on PSX where D2 wouldn't load correctly after putting it into the console. Suspected issue with the music still playing from the break scene when disc is being changed. Not an issue on Emulator. 
- Trimmed Reno text box
- Trimmed Slap skip (2 frame time save if you're lucky)
- Updates to Jessie skip
- Reverted Honey Bee Inn fat guy text boxes because they felt weird

## v0.4.6

- Lots of new trimming from Start to Don's
- Trimmed Reactor 5 and Airbuster
- More trimming of JDeath to before Mideel and Cloud's Dream
- Remove version number from Disc 2 because too much effort to keep updating it

## v0.4.5

- Fixed bug with 5 minute break scene where the Game Moment was being incorrectly set after the timer ended causing an issue on Disc 2
- Added a version number to the first scene in Disc 1 and Disc 2

## v0.4.4

- Added back in the scene where Cloud is upside down and Sephiroth is in a big blue egg (after JDeath)

## v0.4.3

- Fixed bug where elevator in Reactor 5 goes down instead of up, seen in NMS
- Disc 2: Shortened after JDeath to Highwind (going to Mideel to see sick Cloud)

## v0.4.2

- 5 minute break moved to end of Disc 1

## v0.4.1

- When changing music the 4th track is actually "Stop playing music", the intention is to allow players to play their own music on YouTube or something without messing with their audio configurations. Selecting "Change music" again will play the next track.

## v0.4.0

- Added 5 minute break scene after Demon's Gate fight that is skippable if you select the "Continue run" option

## v0.3.2

- Fixed audio issue from Ultima Weapon to Cloud's dream
- Fixed audio issue at Scarlet and Tifa slap fight to Highwind
- Included "Sister Ray!" text box during CoTA FD Manip

## v0.3.1

- Fixed bug where Cloud turns into a Chocobo on the World Map after arriving to Costa Del Sol for the first time. Had to re-add the World Map cutscene from Boat to Costa

## v0.3.0

- Trimmed Gold Saucer first trip and dates alot more
- Trimmed Rocket town a bit mroe
- Trimmed Temple again
- Trimmed CoTA and JLife
- some smaller updates too

## v0.2.0

- Trimmed opening gate to reactor 
- Trimmed entering 7th heaven
- Trimmed basement of 7th heaven with B punching bag
- Trimmed Don's den a bit more
- Removed renaming Aerith opportunity
- Pillar explosion to playground and trimmed
- Broken road scenes with cloud trimmed
- Bottomswell section trimmed
- CPR game trimmed
- Getting shiva section trimmed
- Dolphin training trimmed
- Jenny from the block section trimmed a bit more

## v0.1.1

- Trimmed up to Guard Scorpion
- Trimmed after reactor explosion
- Trimmed 7th heaven
- Trimmed Wall Market
- Trimmed Don Corneo's
- Fixed a bug where the game would not start on newly patched .bin file for disc 1

## Initial changes

### Disc 1

md1stin 116 > 0 dir > S0 - Init

- removed intro

nivl_e1 294 > 1 kakehu > S0 - Main

- removed 7th heaven cutscene (Cloud's promise)

mrkt2 195 > 13 earith > S3 

- you can now rename Aerith when you get to Wall Market (check for specific game moment 108 and show menu change name of Aerith)

pillar_3 160 > 0 dir > S0 - Main

- removed pillar exploding cutscene
- shortened dialogues in this section

blin70_1 > 0 dir > S0 - Init

- removed scene between Don's hole and Aps in shinra building

md0 225 > 0 directr > S0 - Main

- removed pan of shinra building after getting batteries and climb

blin66_3 252 > 2 Untitled > S3 - Move

- removed eavesdroppping on Shinra executives meeting in the air ducts

eleout 233 > 7 lin0 > S4 - Go

- removed president shinra cutscene before prison

blin1 234 > 36 EIGA > S5 - Go 1x

- removed pre bike minigame cutscene

blin67_3 259 > 1 cl > S3

- removed booba eyeball jenova

junonr4 363 > 6 fadeOut > S1
junin1 386 > 9 border4 > S2 Move
junin1a 387 > 12 border2 > S4 Go

- removed before and after parade game cutscenes

del1 441 > 5 border1 > S2 - Move

- removed the helicopter blowing the guy away scene

ropest 457 > 4 evline2 > S2 - Move

- removed barrets hometown being burned down

gldst 496 > 0 dic > S0 - Main

- removed movie when going to gold saucer for first time

games 505 > 0 dic > S0 - Main

- reduced Cait Sith joining party cutscene

jailin2 475 > 0 dic > S0 - Main
mtrcrl_3 461 > 0 produce > S0 - Main

- removed cutscene in desert jail house

dyne 480 > 0 dic > S0 - Main

- reduced Dyne cutscene

rktsid 558 > 14 cloud > S5

- removed cid being an asshole in rocket cutscene

sky 87 > 0 dir > S0 - Main
rckt32 774 > 14 lin0 > S3 - Move

- remove tiny bronco cutscenes

bigwheel 488 > 0 dic > S0 - Main
gldst 496 > 12 ev > S5 - Go 1x

- removed date cutscene assumed to be with Aeris
- shortened diagloue after cait gives black materia to tseng

kuro_3 606 > 18 earith > S10

- removed sephiroth stabbing tseng cutscene

slfrst_1 618 > 0 dir > S0 - Main
kuro_12 616 > 16 boss > S4
jtemplc 775 > 0 produce > S0 - Main

- removed Aeris and Cait Sith temple cutscenes

ancnt4 649 > 0 dir > S0 - Main
ancnt2 647 > 0 dir > S0 - Main
blue_2 641 > 0 dir > S0 - Main

- removed some scenes where Aeris dies

### Disc 2

trnad_4 705 > 17 discver > S2 - Move

- removed scenes before Jenova fight

nivl_b22 293 > 3 tifa > S1 Talk > L7
junbin3 400 > 0 dir > S0

- removed after Jenova to Dr's Office

junbin3 400 > 4 ti > S19 > L6

- skip some dialogue in the Dr's Office

junair 384 > 16 air0 > S3 - Move
junbin4 401 > 0 dir > S0 - Main
junone2 411 > 13 lin1 > S3 - Move

- removed alot of fluff in Junon with Weapons attacking

itown1a 712 > 2 tifa > S3 > L4
itos 720 > 0 dic > S0 - Main

- removed Mideel cutscenes after weapons released
- reduced cloud being sick scenes
- skipped highwind cutscenes up to Cid being player character

itos 720 > 0 dic > S0 - Main

- removed cutscenes before Ultima weapon fight

zmind3 727 > 7 mabolo > S1 Talk > L19

- reduced Cloud's dream sequence cutscenes

rcktin7 569 > 2 init > S0 - Main
fship_25 72 > 4 direct > S2

- reduced rocket cutscenes

bugin1a 541 > 12 AD > S7

- cosmo canyon cutscenes removed

white1 642 > 1 cl > S3 
loslake1 637 > 0 dir > S0 - Main

- FD manip cutscenes removed without affecting manip

fr_e 347 > 0 dir > S0 Main

- after diamond weapon fight

canon_2 741 > 13 hojyo > S1 - Talk

- reduced dialogues and disc 3 after hojo fight
