"""FF7 field-script opcode and map tables, transcribed from Makou Reactor.

OPCODE_LENGTH: fixed byte length per opcode (KAWAI, SPECIAL and 0x1C are
variable; see ff7_field.op_size). OPCODE_NAMES: mnemonic per opcode.
MAPLIST: field id -> map stem (Makou Data::_mapList).
"""

OPCODE_LENGTH = [1, 3, 3, 3, 3, 3, 3, 2, 2, 15, 6, 6, 1, 1, 2, 2, 2, 3, 2, 3, 6, 7, 8, 9, 8, 9, 10, 3, 6, 1, 1, 1, 11, 2, 5, 3, 3, 9, 2, 2, 3, 1, 2, 2, 5, 7, 2, 10, 4, 4, 4, 2, 2, 4, 5, 8, 6, 6, 6, 4, 1, 1, 1, 1, 3, 5, 6, 2, 1, 5, 1, 5, 7, 4, 2, 2, 1, 5, 1, 5, 10, 6, 4, 2, 2, 3, 7, 7, 5, 5, 5, 7, 8, 10, 8, 1, 10, 2, 5, 6, 6, 1, 9, 1, 9, 2, 7, 9, 1, 4, 3, 6, 4, 2, 3, 4, 4, 8, 4, 5, 4, 5, 3, 3, 3, 3, 2, 3, 4, 5, 4, 4, 4, 4, 5, 4, 5, 4, 5, 4, 5, 4, 5, 4, 5, 4, 5, 4, 5, 3, 3, 3, 3, 3, 4, 5, 6, 7, 7, 11, 2, 2, 3, 3, 2, 11, 9, 9, 6, 6, 2, 4, 1, 6, 3, 3, 5, 5, 4, 3, 6, 6, 2, 4, 5, 4, 3, 5, 5, 4, 1, 2, 11, 8, 15, 12, 1, 3, 3, 2, 2, 2, 4, 3, 3, 3, 2, 2, 13, 2, 2, 16, 10, 10, 4, 4, 3, 1, 15, 2, 4, 1, 1, 11, 4, 4, 3, 3, 3, 5, 5, 5, 7, 10, 10, 5, 5, 8, 8, 11, 2, 5, 14, 2, 2, 2, 2, 4, 2, 1, 3, 2, 2, 8, 3, 1]

OPCODE_NAMES = """
    RET REQ REQSW REQEW PREQ PRQSW PRQEW RETTO JOIN SPLIT SPTYE GTPYE Unknown1 Unknown2
    DSKCG SPECIAL JMPF JMPFL JMPB JMPBL IFUB IFUBL IFSW IFSWL IFUW IFUWL Unknown3 Unknown4
    Unknown5 Unknown6 Unknown7 Unknown8 MINIGAME TUTOR BTMD2 BTRLD WAIT NFADE BLINK BGMOVIE
    KAWAI KAWIW PMOVA SLIP BGPDH BGSCR WCLS WSIZW IFKEY IFKEYON IFKEYOFF UC PDIRA PTURA
    WSPCL WNUMB STTIM GOLDu GOLDd CHGLD HMPMAX1 HMPMAX2 MHMMX HMPMAX3 MESSAGE MPARA MPRA2
    MPNAM Unknown9 MPu Unknown10 MPd ASK MENU MENU2 BTLTB Unknown11 HPu Unknown12 HPd WINDOW
    WMOVE WMODE WREST WCLSE WROW GWCOL SWCOL STITM DLITM CKITM SMTRA DMTRA CMTRA SHAKE NOP
    MAPJUMP SCRLO SCRLC SCRLA SCR2D SCRCC SCR2DC SCRLW SCR2DL MPDSP VWOFT FADE FADEW IDLCK
    LSTMP SCRLP BATTLE BTLON BTLMD PGTDR GETPC PXYZI PLUS! PLUS2! MINUS! MINUS2! INC! INC2!
    DEC! DEC2! TLKON RDMSD SETBYTE SETWORD BITON BITOFF BITXOR PLUS PLUS2 MINUS MINUS2 MUL
    MUL2 DIV DIV2 MOD MOD2 AND AND2 OR OR2 XOR XOR2 INC INC2 DEC DEC2 RANDOM LBYTE HBYTE
    2BYTE SETX GETX SEARCHX PC CHAR DFANM ANIME1 VISI XYZI XYI XYZ MOVE CMOVE MOVA TURA
    ANIMW FMOVE ANIME2 ANIM!1 CANIM1 CANM!1 MSPED DIR TURNGEN TURN DIRA GETDIR GETAXY GETAI
    ANIM!2 CANIM2 CANM!2 ASPED Unknown13 CC JUMP AXYZI LADER OFST OFSTW TALKR SLIDR SOLID
    PRTYP PRTYM PRTYE IFPRTYQ IFMEMBQ MMBud MMBLK MMBUK LINE LINON MPJPO SLINE SIN COS TLKR2
    SLDR2 PMJMP PMJMP2 AKAO2 FCFIX CCANM ANIMB TURNW MPPAL BGON BGOFF BGROL BGROL2 BGCLR
    STPAL LDPAL CPPAL RTPAL ADPAL MPPAL2 STPLS LDPLS CPPAL2 RTPAL2 ADPAL2 MUSIC SOUND AKAO
    MUSVT MUSVM MULCK BMUSC CHMPH PMVIE MOVIE MVIEF MVCAM FMUSC CMUSC CHMST GAMEOVER
""".split()

MAPLIST = """
    dummy wm0 wm1 wm2 wm3 wm4 wm5 wm6 wm7 wm8 wm9 wm10 wm11 wm12 wm13 wm14 wm15 wm16 wm17
    wm18 wm19 wm20 wm21 wm22 wm23 wm24 wm25 wm26 wm27 wm28 wm29 wm30 wm31 wm32 wm33 wm34
    wm35 wm36 wm37 wm38 wm39 wm40 wm41 wm42 wm43 wm44 wm45 wm46 wm47 wm48 wm49 wm50 wm51
    wm52 wm53 wm54 wm55 wm56 wm57 wm58 wm59 wm60 wm61 wm62 wm63 startmap fship_1 fship_12
    fship_2 fship_22 fship_23 fship_24 fship_25 fship_3 fship_4 fship_42 fship_5 hill zz1
    zz2 zz3 zz4 zz5 zz6 zz7 zz8 sea sky q_1 q_2 q_3 q_4 q_5 blackbg1 blackbg2 blackbg3
    blackbg4 blackbg5 blackbg6 blackbg7 blackbg8 blackbg9 blackbga blackbgb blackbgc
    blackbgd blackbge blackbgf blackbgg blackbgh blackbgi blackbgj blackbgk whitebg1
    whitebg2 whitebg3 md1stin md1_1 md1_2 nrthmk nmkin_1 elevtr1 nmkin_2 nmkin_3 nmkin_4
    nmkin_5 southmk1 southmk2 smkin_1 smkin_2 smkin_3 smkin_4 smkin_5 md8_1 md8_2 md8_3
    md8_4 md8brdg cargoin tin_1 tin_2 tin_3 tin_4 rootmap mds7st1 mds7st2 mds7st3 mds7st32
    mds7_w1 mds7_w2 mds7_w3 mds7 mds7_im 7min1 mds7pb_1 mds7pb_2 mds7plr1 mds7plr2 pillar_1
    pillar_2 pillar_3 tunnel_1 tunnel_2 tunnel_3 4sbwy_1 4sbwy_2 4sbwy_3 4sbwy_4 4sbwy_5
    4sbwy_6 mds5_5 mds5_4 mds5_3 mds5_2 5min1_1 5min1_2 mds5_dk mds5_1 mds5_w mds5_i mds5_m
    church chrin_1a chrin_1b chrin_2 chrin_3a chrin_3b eals_1 ealin_1 ealin_12 ealin_2
    mds6_1 mds6_2 mds6_22 mds6_3 mrkt2 mkt_w mkt_mens mkt_ia mktinn mkt_m mkt_s1 mkt_s2
    mkt_s3 mktpb mrkt1 colne_1 colne_2 colne_3 colne_4 colne_5 colne_6 colne_b1 colne_b3
    mrkt3 onna_1 onna_2 onna_3 onna_4 onna_5 onna_52 onna_6 mrkt4 wcrimb_1 wcrimb_2 md0
    roadend sinbil_1 sinbil_2 blinst_1 blinst_2 blinst_3 blinele eleout blin1 blin2 blin2_i
    blin3_1 blin59 blin60_1 blin60_2 blin61 blin62_1 blin62_2 blin62_3 blin63_1 blin63_t
    blin64 blin65_1 blin65_2 blin66_1 blin66_2 blin66_3 blin66_4 blin66_5 blin66_6 blin67_1
    blin671b blin67_2 blin67_3 blin673b blin67_4 blin68_1 blin68_2 blin69_1 blin69_2
    blin70_1 blin70_2 blin70_3 blin70_4 niv_w nvmin1_1 nvmin1_2 nivinn_1 nivinn_2 nivinn_3
    niv_cl trackin trackin2 nivgate nivgate2 nivgate3 nivl nivl_2 nivl_3 nivl_4 niv_ti1
    niv_ti2 niv_ti3 niv_ti4 nivl_b1 nivl_b12 nivl_b2 nivl_b22 nivl_e1 nivl_e2 nivl_e3
    sinin1_1 sinin1_2 sinin2_1 sinin2_2 sinin3 sininb1 sininb2 sininb31 sininb32 sininb33
    sininb41 sininb42 sininb51 sininb52 mtnvl2 mtnvl3 mtnvl4 mtnvl5 mtnvl6 mtnvl6b nvdun1
    nvdun2 nvdun3 nvdun31 nvdun4 nvmkin1 nvmkin21 nvmkin22 nvmkin23 nvmkin31 nvmkin32 elm_wa
    elm_i elmpb elminn_1 elminn_2 elmin1_1 elmin1_2 elm elmin2_1 elmin2_2 elmin3_1 elmin3_2
    elmtow elmin4_1 elmin4_2 farm frmin frcyo trap fr_e sichi psdun_1 psdun_2 psdun_3
    psdun_4 condor1 condor2 convil_1 convil_2 convil_3 convil_4 junon junonr1 junonr2
    junonr3 junonr4 jun_wa jun_i1 jun_m junmin1 junmin2 junmin3 junonl1 junonl2 junonl3
    jun_w jun_a jun_i2 juninn junpb_1 junpb_2 junpb_3 junmin4 junmin5 jundoc1a jundoc1b
    junair junair2 junin1 junin1a junele1 junin2 junin3 junele2 junin4 junin5 junin6 junin7
    junbin1 junbin12 junbin21 junbin22 junbin3 junbin4 junbin5 junmon junsbd1 subin_1a
    subin_1b subin_2a subin_2b subin_3 subin_4 junone2 junone3 junone4 junone5 junone6
    junone7 spgate spipe_1 spipe_2 semkin_1 semkin_2 semkin_8 semkin_3 semkin_4 semkin_5
    semkin_6 semkin_7 ujunon1 ujunon2 ujunon3 prisila ujun_w jumin ujunon4 ujunon5 ship_1
    ship_2 shpin_22 shpin_2 shpin_3 del1 del12 del2 delinn delpb delmin1 delmin12 delmin2
    del3 ncorel ncorel2 ncorel3 ncoin1 ncoin2 ncoin3 ncoinn ropest mtcrl_0 mtcrl_1 mtcrl_2
    mtcrl_3 mtcrl_4 mtcrl_5 mtcrl_6 mtcrl_7 mtcrl_8 mtcrl_9 corel1 corel2 corel3 jail1
    jailin1 jail2 jailpb jailin2 jailin3 jailin4 jail3 jail4 dyne desert1 desert2 corelin
    astage_a astage_b jet jetin1 bigwheel bwhlin bwhlin2 ghotel ghotin_1 ghotin_4 ghotin_2
    ghotin_3 gldst gldgate gldinfo coloss coloin1 coloin2 clsin2_1 clsin2_2 clsin2_3 games
    games_1 games_2 mogu_1 chorace chorace2 crcin_1 crcin_2 gldelev gonjun1 gonjun2 gnmkf
    gnmk gongaga gon_wa1 gon_wa2 gon_i gninn gomin goson cos_btm cos_btm2 cosmo cosmo2
    cosin1 cosin1_1 cosin2 cosin3 cosin4 cosin5 cosmin2 cosmin3 cosmin4 cosmin6 cosmin7
    cos_top bugin1a bugin1b bugin1c bugin2 bugin3 gidun_1 gidun_2 gidun_4 gidun_3 seto1
    rckt2 rckt3 rkt_w rkt_i rktinn1 rktinn2 rckt rktsid rktmin1 rktmin2 rcktbas1 rcktbas2
    rcktin1 rcktin2 rcktin3 rcktin4 rcktin5 rcktin6 rcktin7 rcktin8 pass yougan yougan2
    yougan3 uta_wa uta_im utmin1 utmin2 uutai1 utapb yufy1 yufy2 hideway1 hideway2 hideway3
    5tower uutai2 uttmpin1 uttmpin2 uttmpin3 uttmpin4 datiao_1 datiao_2 datiao_3 datiao_4
    datiao_5 datiao_6 datiao_7 datiao_8 jtempl jtemplb jtmpin1 jtmpin2 kuro_1 kuro_2 kuro_3
    kuro_4 kuro_5 kuro_6 kuro_7 kuro_8 kuro_82 kuro_9 kuro_10 kuro_11 kuro_12 bonevil
    slfrst_1 slfrst_2 anfrst_1 anfrst_2 anfrst_3 anfrst_4 anfrst_5 sango1 sango2 sango3
    sandun_1 sandun_2 lost1 losin1 losin2 losin3 lost2 lost3 losinn loslake1 loslake2
    loslake3 blue_1 blue_2 white1 white2 hekiga whitein ancnt1 ancnt2 ancnt3 ancnt4 snw_w
    sninn_1 sninn_2 sninn_b1 snow snmin1 snmin2 snmayor hyou1 hyou2 hyou3 icedun_1 icedun_2
    hyou4 hyou5_1 hyou5_2 hyou5_3 hyou5_4 hyou6 hyoumap move_s move_i move_f move_r move_u
    move_d hyou7 hyou8_1 hyou8_2 hyou9 hyou10 hyou11 hyou12 hyou13_1 hyou13_2 hyou14
    gaiafoot holu_1 holu_2 gaia_1 gaiin_1 gaiin_2 gaia_2 gaiin_3 gaia_31 gaia_32 gaiin_4
    gaiin_5 gaiin_6 gaiin_7 crater_1 crater_2 trnad_1 trnad_2 trnad_3 trnad_4 trnad_51
    trnad_52 trnad_53 woa_1 woa_2 woa_3 itown1a itown12 itown1b itown2 ithill itown_w
    itown_i itown_m ithos itmin1 itmin2 life life2 zmind1 zmind2 zmind3 zcoal_1 zcoal_2
    zcoal_3 md8_5 md8_6 md8_b1 md8_b2 4sbwy_22 tunnel_4 tunnel_5 md8brdg2 md8_32 canon_1
    canon_2 md_e1 xmvtes las0_1 las0_2 las0_3 las0_4 las0_5 las0_6 las0_7 las0_8 las1_1
    las1_2 las1_3 las1_4 las2_1 las2_2 las2_3 las2_4 las3_1 las3_2 las3_3 las4_0 las4_1
    las4_2 las4_3 las4_4 lastmap fallp m_endo hill2 bonevil2 junone22 rckt32 jtemplc
    fship_26 las4_42 tunnel_6 md8_52 sininb34 mds7st33 midgal sininb35 nivgate4 sininb36
    ztruck frcyo2
""".split()
