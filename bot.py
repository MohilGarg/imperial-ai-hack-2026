"""Imperial AI Hack 2026 poker bot.

Equity-driven no-limit hold'em agent:
  * preflop: precomputed equity table (169 hand classes x 1..7 opponents),
    position-aware opening ranges, range-aware Monte Carlo when facing raises;
  * postflop: time-budgeted Monte Carlo equity against opponents' estimated
    ranges (preflop percentile cut-offs plus filtering on postflop aggression);
  * opponent modelling per seat over the round: VPIP, PFR, postflop aggression
    and fold-to-bet, used both for range estimates and bluff frequency.
Standard library only. Keeps well inside 10 ms per decision and 10 s per round.
"""
import random
import time

RANKS = "23456789TJQKA"
SUITS = "cdhs"

_PRE = 'AA:845,734,631,552,497,439,386;AKs:677,508,423,361,311,272,249;AKo:646,482,375,330,273,236,220;AQs:672,505,394,331,291,251,242;AQo:645,477,364,295,257,208,196;AJs:652,484,392,331,290,248,231;AJo:640,444,348,298,238,206,185;ATs:643,485,364,309,260,247,223;ATo:626,437,336,276,233,193,171;A9s:625,443,360,286,248,205,183;A9o:614,414,320,247,197,168,157;A8s:629,434,331,274,223,209,188;A8o:598,405,306,215,191,157,144;A7s:609,432,325,268,216,192,178;A7o:585,392,289,218,175,162,132;A6s:605,419,307,251,226,190,163;A6o:572,382,273,214,182,142,120;A5s:594,414,321,271,223,187,170;A5o:571,390,278,220,177,159,131;A4s:591,405,319,254,221,189,170;A4o:579,366,264,214,171,151,126;A3s:584,402,316,231,216,178,171;A3o:557,356,260,203,169,149,131;A2s:580,391,292,233,205,187,163;A2o:558,357,265,199,159,131,121;KK:814,680,598,496,427,370,329;KQs:648,472,390,308,276,248,225;KQo:620,448,348,302,250,211,182;KJs:621,469,370,313,252,249,205;KJo:611,426,325,272,242,198,168;KTs:625,440,364,292,251,227,207;KTo:597,418,321,266,233,191,160;K9s:591,414,328,276,233,207,166;K9o:587,396,297,238,199,165,147;K8s:584,398,295,264,222,185,170;K8o:561,372,290,211,166,146,115;K7s:576,383,292,244,194,196,159;K7o:558,366,262,215,161,149,122;K6s:582,395,302,227,201,171,151;K6o:548,351,249,203,161,129,112;K5s:558,370,291,221,196,171,149;K5o:534,336,244,208,150,118,112;K4s:556,372,268,231,187,174,160;K4o:511,338,251,195,147,127,112;K3s:534,360,264,221,191,163,154;K3o:510,317,229,183,145,125,107;K2s:536,360,266,221,189,157,145;K2o:497,309,227,174,140,112,96;QQ:800,648,526,450,364,311,276;QJs:593,439,350,301,270,237,203;QJo:583,415,324,267,243,192,163;QTs:596,433,342,274,251,223,191;QTo:571,401,317,255,216,199,160;Q9s:580,409,322,253,239,196,172;Q9o:569,376,290,235,192,168,153;Q8s:564,374,298,245,209,187,163;Q8o:536,352,250,213,175,144,130;Q7s:535,373,264,211,204,173,147;Q7o:520,332,246,180,161,132,97;Q6s:534,362,259,222,171,157,141;Q6o:500,313,231,183,134,118,108;Q5s:534,355,259,222,192,160,141;Q5o:501,316,214,176,150,120,99;Q4s:527,337,257,201,180,155,135;Q4o:501,311,220,159,130,110,101;Q3s:510,334,249,197,176,161,132;Q3o:496,296,202,155,135,105,89;Q2s:493,324,245,196,150,153,134;Q2o:451,287,183,153,128,107,83;JJ:775,612,494,402,350,276,242;JTs:560,435,321,296,241,220,195;JTo:544,395,323,242,218,184,169;J9s:564,393,317,256,222,192,173;J9o:524,372,286,223,190,158,144;J8s:539,385,294,241,208,178,170;J8o:509,343,267,194,176,138,115;J7s:526,356,286,218,177,165,151;J7o:489,324,235,187,158,127,109;J6s:510,338,255,213,168,148,145;J6o:484,296,213,165,128,105,90;J5s:502,336,259,201,165,141,128;J5o:482,293,197,145,128,115,92;J4s:486,323,251,183,159,139,128;J4o:466,289,194,148,126,91,85;J3s:477,313,231,197,169,137,133;J3o:459,277,197,147,117,96,77;J2s:474,302,237,192,157,149,114;J2o:442,257,172,137,110,102,84;TT:754,568,449,359,300,252,221;T9s:535,387,320,251,225,212,181;T9o:519,361,277,232,185,159,136;T8s:523,363,285,224,193,175,165;T8o:503,327,255,212,164,139,116;T7s:506,345,266,240,186,164,152;T7o:477,314,232,187,154,128,114;T6s:483,334,259,206,174,149,139;T6o:447,285,210,164,137,106,95;T5s:462,304,230,189,156,139,116;T5o:436,266,194,150,114,96,78;T4s:469,308,230,186,146,134,113;T4o:453,270,186,137,105,99,85;T3s:459,294,240,183,159,144,126;T3o:426,245,179,136,104,87,77;T2s:446,281,216,181,146,138,115;T2o:417,246,165,136,102,85,73;99:723,522,415,337,272,222,183;98s:498,365,289,244,200,171,160;98o:474,328,266,202,175,134,123;97s:498,346,251,213,191,150,154;97o:461,296,228,190,152,132,106;96s:476,325,237,197,168,169,133;96o:443,284,213,174,128,103,93;95s:457,307,227,188,156,136,116;95o:432,260,183,146,115,96,81;94s:433,283,206,164,143,124,107;94o:404,249,171,138,114,79,73;93s:436,278,213,160,147,116,117;93o:401,226,183,131,102,89,74;92s:444,267,201,164,147,132,110;92o:388,231,157,133,105,77,65;88:691,493,388,297,244,199,170;87s:475,335,265,210,197,178,152;87o:451,308,226,185,168,138,109;86s:469,327,251,203,191,150,145;86o:435,287,202,162,138,116,102;85s:454,303,212,198,165,159,118;85o:423,261,183,150,118,98,95;84s:433,283,223,166,157,130,119;84o:391,243,163,135,108,89,77;83s:410,258,187,166,132,137,102;83o:374,224,153,115,97,69,67;82s:410,252,198,156,133,116,113;82o:370,220,156,114,90,79,69;77:661,457,343,266,225,187,169;76s:447,317,252,201,188,156,152;76o:434,285,215,162,137,114,110;75s:444,290,236,183,178,147,132;75o:402,264,200,161,136,107,100;74s:412,286,218,174,147,135,118;74o:383,239,166,139,119,96,86;73s:397,258,212,171,135,120,107;73o:365,219,152,124,96,91,74;72s:381,245,179,153,133,115,97;72o:347,189,135,108,87,72,63;66:636,437,315,255,196,177,144;65s:432,313,240,200,176,154,142;65o:404,256,196,164,132,117,101;64s:424,290,226,181,157,137,131;64o:387,257,176,140,121,106,95;63s:397,269,202,160,148,119,112;63o:370,225,152,125,103,102,85;62s:380,254,194,160,118,119,108;62o:350,210,152,108,93,77,63;55:590,396,291,221,187,159,147;54s:413,278,227,189,161,149,130;54o:374,255,204,154,128,103,106;53s:397,258,211,172,151,137,131;53o:363,238,163,130,109,93,91;52s:374,253,195,154,148,137,113;52o:349,215,148,118,103,83,72;44:571,369,267,204,168,154,138;43s:383,274,200,172,142,134,118;43o:350,222,164,124,108,99,75;42s:369,243,183,152,141,118,121;42o:323,220,150,123,94,83,77;33:534,332,238,198,162,145,129;32s:359,235,181,146,125,119,114;32o:322,193,141,95,94,87,70;22:505,295,226,172,145,148,142'


def _parse_pre():
    table = {}
    for item in _PRE.split(";"):
        name, vals = item.split(":")
        table[name] = [int(v) / 1000.0 for v in vals.split(",")]
    return table


PRE = _parse_pre()

_EQR = 'AA:781,818,816,843,841,844,844,871,859,850,844,861;AKs:364,417,491,557,607,625,643,658,673,683,687,677;AKo:321,390,447,532,576,612,628,648,653,648,681,648;AQs:297,372,438,469,546,592,621,644,655,649,673,669;AQo:267,335,384,442,532,575,598,620,617,646,641,645;AJs:302,354,395,427,484,556,584,628,629,640,652,639;AJo:245,313,353,390,461,548,574,596,609,613,620,643;ATs:289,316,350,383,441,517,571,605,615,618,633,646;ATo:244,280,343,329,419,474,532,563,586,595,632,613;A9s:269,294,345,375,394,461,526,554,586,584,623,644;A9o:232,264,308,329,376,445,493,534,564,576,603,607;A8s:299,301,310,360,393,452,491,534,555,588,596,622;A8o:251,280,284,321,349,415,465,513,527,575,577,592;A7s:298,312,310,349,385,453,469,489,539,569,590,600;A7o:247,268,290,300,352,399,446,484,522,550,569,586;A6s:290,302,329,338,382,418,456,525,530,553,598,600;A6o:253,260,273,292,343,388,427,468,500,523,549,566;A5s:296,333,356,362,388,424,464,514,524,542,558,596;A5o:266,278,301,319,349,396,442,456,503,523,572,578;A4s:297,309,329,349,381,426,450,499,521,544,560,567;A4o:250,268,291,308,343,401,429,464,489,518,539,573;A3s:317,307,326,339,370,419,461,471,506,554,570,585;A3o:253,257,292,307,332,400,416,452,483,515,525,566;A2s:271,303,329,346,374,401,454,488,515,528,553,552;A2o:246,267,295,324,349,392,406,466,489,521,545,560;KK:556,675,700,710,729,756,754,757,802,804,817,819;KQs:250,345,371,393,443,495,511,529,580,602,630,639;KQo:202,322,313,361,394,448,480,513,547,584,616,599;KJs:239,326,347,372,387,450,484,512,556,587,615,622;KJo:182,303,307,331,375,422,463,481,532,575,585,605;KTs:242,314,326,359,376,413,482,512,524,570,593,646;KTo:187,283,295,333,343,391,433,476,516,544,571,600;K9s:225,274,320,324,371,382,433,454,530,551,565,611;K9o:190,236,276,303,326,334,385,444,477,537,556,579;K8s:223,265,283,342,348,363,406,426,490,531,559,583;K8o:191,222,258,293,315,329,349,400,454,501,519,545;K7s:231,265,303,313,347,375,389,413,466,530,537,566;K7o:194,228,256,278,299,324,368,376,433,485,538,572;K6s:214,254,291,334,349,365,396,415,456,502,543,563;K6o:192,243,256,281,322,307,353,390,433,468,518,548;K5s:213,264,288,328,352,362,390,393,440,493,536,570;K5o:175,234,256,283,293,320,352,379,419,472,510,536;K4s:216,287,289,321,341,357,385,417,447,488,510,556;K4o:190,237,252,274,297,314,340,363,413,447,500,524;K3s:218,272,281,314,339,354,373,387,422,477,511,549;K3o:175,228,230,280,302,307,352,371,398,456,494,510;K2s:214,261,280,311,337,356,379,390,426,447,493,540;K2o:161,222,234,255,300,315,341,355,402,427,461,514;QQ:284,566,598,629,658,674,710,726,743,758,786,805;QJs:197,320,348,364,388,421,430,466,489,555,572,617;QJo:135,311,318,322,327,368,403,417,484,527,557,579;QTs:185,289,348,351,353,380,426,431,469,522,560,591;QTo:155,268,298,330,337,347,372,427,465,511,541,564;Q9s:206,271,321,341,354,352,378,427,463,515,543,574;Q9o:135,231,294,293,314,330,355,393,425,472,503,566;Q8s:168,263,295,337,331,344,361,400,450,495,512,575;Q8o:133,214,255,292,305,306,347,363,399,455,501,539;Q7s:181,258,301,299,333,353,347,373,412,479,512,541;Q7o:136,227,234,269,281,315,307,346,369,441,478,528;Q6s:191,250,300,303,328,356,353,390,406,465,498,527;Q6o:135,205,237,270,282,289,326,353,378,408,474,524;Q5s:178,256,266,303,326,338,353,365,404,438,509,533;Q5o:122,221,261,280,287,308,343,337,378,437,457,515;Q4s:166,262,280,299,341,334,362,369,381,418,469,517;Q4o:134,203,237,263,301,310,333,337,367,407,452,500;Q3s:166,244,276,305,321,316,346,362,391,420,484,510;Q3o:126,218,235,271,267,307,322,342,373,415,454,461;Q2s:169,230,287,300,310,330,375,376,384,422,461,523;Q2o:114,197,223,249,265,286,302,309,342,388,443,483;JJ:190,455,510,577,605,626,649,678,707,715,755,755;JTs:196,295,333,355,380,377,419,417,476,515,548,578;JTo:152,254,313,326,332,336,362,379,424,477,510,554;J9s:198,250,291,338,356,359,362,405,405,493,514,542;J9o:158,218,279,306,316,336,344,369,399,447,490,526;J8s:169,239,284,324,345,343,365,400,418,436,496,526;J8o:147,199,273,288,311,329,326,359,355,416,472,521;J7s:165,243,267,305,338,332,344,355,401,450,477,518;J7o:129,196,230,258,308,307,315,347,371,390,450,512;J6s:170,225,268,282,310,320,357,350,384,398,468,489;J6o:124,195,226,269,290,279,299,347,352,376,449,490;J5s:182,237,265,313,334,333,345,368,372,411,470,496;J5o:122,185,237,253,287,274,311,319,334,375,425,485;J4s:154,216,279,293,332,331,353,346,371,418,450,480;J4o:108,205,232,264,269,295,306,302,333,382,422,447;J3s:169,223,281,273,306,308,342,348,369,405,427,470;J3o:109,177,235,245,273,279,298,305,315,374,411,461;J2s:152,220,253,275,322,325,332,352,359,391,442,478;J2o:115,183,219,262,268,289,304,318,334,352,400,452;TT:200,345,445,514,571,581,599,663,659,690,701,746;T9s:217,235,302,325,360,359,381,404,421,455,500,538;T9o:183,207,273,316,307,326,346,368,383,428,457,523;T8s:200,229,285,334,342,374,362,390,403,438,484,518;T8o:156,200,256,279,323,333,318,340,363,404,446,505;T7s:181,234,278,315,321,342,353,364,395,412,466,496;T7o:155,189,244,300,304,310,315,343,350,382,447,481;T6s:180,205,271,302,314,325,357,361,383,412,434,486;T6o:137,186,230,269,286,287,292,330,348,342,404,450;T5s:171,212,267,279,310,328,336,330,363,412,422,469;T5o:119,169,214,259,274,281,291,325,310,351,380,441;T4s:175,209,255,292,305,327,335,358,365,381,404,473;T4o:128,166,234,252,258,284,307,310,334,342,380,424;T3s:164,196,262,285,302,310,349,330,344,390,408,439;T3o:131,166,221,250,261,277,293,313,324,328,376,421;T2s:154,203,260,274,282,314,304,315,347,366,411,459;T2o:120,164,213,256,248,275,285,303,308,307,370,428;99:188,244,372,473,515,548,578,604,618,646,690,725;98s:212,213,300,327,369,378,377,395,401,431,469,509;98o:170,204,242,296,321,344,342,352,367,373,446,502;97s:199,214,286,336,343,340,355,385,382,409,422,485;97o:169,190,238,275,315,337,317,351,359,365,413,461;96s:184,232,267,320,326,345,359,364,377,400,434,469;96o:148,158,235,285,306,310,326,342,330,337,367,427;95s:183,189,257,289,310,339,352,358,373,372,405,458;95o:129,160,221,270,281,280,302,319,336,354,369,437;94s:160,166,258,278,312,312,329,348,349,373,395,443;94o:125,133,215,253,276,277,294,296,317,322,372,396;93s:167,178,242,300,312,333,319,347,347,357,392,417;93o:130,138,197,261,254,282,269,297,318,316,358,411;92s:164,172,259,282,302,313,318,331,338,338,388,422;92o:119,137,207,253,266,279,293,291,303,328,362,392;88:196,237,320,423,478,515,554,565,592,621,685,690;87s:223,217,270,314,358,362,387,395,374,396,452,474;87o:184,189,250,297,326,340,336,353,348,369,405,441;86s:211,225,273,317,347,336,377,385,390,390,397,469;86o:181,189,237,274,306,323,347,351,322,359,385,437;85s:201,209,252,318,324,355,358,344,377,382,417,452;85o:149,165,234,265,283,316,328,330,325,364,347,425;84s:180,200,242,278,311,314,335,345,347,377,393,430;84o:151,158,222,255,282,275,309,316,321,328,337,392;83s:154,181,227,274,289,324,325,327,340,346,378,431;83o:113,142,179,239,275,284,294,295,305,324,317,375;82s:173,186,238,281,287,325,314,332,340,364,360,405;82o:103,144,188,242,253,290,295,287,300,320,342,371;77:186,232,306,375,457,489,520,548,572,607,626,672;76s:219,228,272,332,349,374,367,402,399,390,411,448;76o:184,206,239,293,306,327,333,345,348,377,390,429;75s:209,204,262,298,331,348,360,374,383,377,400,427;75o:167,184,233,268,296,324,321,348,344,340,379,389;74s:204,215,256,286,315,358,346,371,356,372,382,415;74o:151,173,228,259,280,307,319,317,320,328,358,393;73s:185,203,240,276,309,315,322,336,345,362,371,390;73o:134,171,212,240,270,298,288,309,315,329,337,358;72s:166,193,230,262,282,314,313,325,345,333,361,384;72o:129,138,195,224,252,266,274,298,305,295,309,355;66:177,245,317,376,424,463,497,535,551,574,578,628;65s:228,236,288,319,340,340,378,380,384,394,406,440;65o:185,196,231,280,287,319,331,329,354,362,381,406;64s:202,225,268,299,339,349,334,369,379,380,388,425;64o:159,195,233,293,288,311,318,322,350,338,338,358;63s:200,204,248,290,322,349,327,363,366,355,357,389;63o:148,159,215,258,274,290,313,312,322,327,316,362;62s:177,183,237,273,291,313,330,339,337,352,363,367;62o:133,151,202,246,264,286,294,293,307,314,329,360;55:198,234,312,378,414,443,484,512,527,561,580,610;54s:209,240,284,320,332,342,388,375,374,372,421,418;54o:185,209,265,273,309,307,346,355,338,348,351,377;53s:212,221,258,308,319,346,374,350,362,378,358,401;53o:172,190,233,252,291,313,323,322,337,338,324,373;52s:184,216,253,282,317,312,341,330,348,346,361,384;52o:150,163,220,259,273,308,327,322,332,313,304,342;44:185,211,296,369,421,437,473,494,509,540,542,561;43s:191,209,257,312,305,326,353,351,335,362,375,382;43o:158,194,229,253,297,309,317,323,324,341,349,366;42s:177,199,230,298,286,326,325,351,326,347,353,364;42o:141,173,212,254,264,285,293,298,295,297,321,324;33:183,216,308,366,404,427,442,478,478,524,531,528;32s:183,201,239,270,296,318,324,319,340,326,351,358;32o:125,155,208,234,266,294,298,301,313,301,317,325;22:188,217,299,345,379,437,446,487,469,475,497,487'
BUCKETS = (0.015, 0.03, 0.05, 0.08, 0.12, 0.17, 0.24, 0.33, 0.45, 0.60, 0.80, 1.0)


def _parse_eqr():
    table = {}
    for item in _EQR.split(";"):
        name, vals = item.split(":")
        row = [int(v) / 1000.0 for v in vals.split(",")]
        for i in range(1, len(row)):          # equity never falls as the range widens
            if row[i] < row[i - 1]:
                row[i] = row[i - 1]
        table[name] = row
    return table


EQR = _parse_eqr()


def eqr(name, f):
    """Heads-up all-in equity of hand class `name` against the top fraction f of hands."""
    row = EQR[name]
    if f <= BUCKETS[0]:
        return row[0]
    for i in range(1, 12):
        if f <= BUCKETS[i]:
            lo = BUCKETS[i - 1]
            w = (f - lo) / (BUCKETS[i] - lo)
            return row[i - 1] * (1.0 - w) + row[i] * w
    return row[-1]


def _class_name(a, b):
    """a, b are int cards. Returns e.g. 'AKs', 'T9o', '77'."""
    ra, rb = a >> 2, b >> 2
    if ra < rb:
        ra, rb = rb, ra
        a, b = b, a
    if ra == rb:
        return RANKS[ra] + RANKS[rb]
    return RANKS[ra] + RANKS[rb] + ("s" if (a & 3) == (b & 3) else "o")


def _build_percentiles():
    combos = {}
    for name in PRE:
        combos[name] = 6 if len(name) == 2 else (4 if name[2] == "s" else 12)
    score = {n: 0.5 * PRE[n][0] + 0.5 * PRE[n][2] for n in PRE}
    order = sorted(PRE, key=lambda n: score[n])
    total = float(sum(combos.values()))
    pct, acc = {}, 0.0
    for n in order:
        acc += combos[n]
        pct[n] = acc / total  # 1.0 = best hand class
    return pct


PCT_CLASS = _build_percentiles()
PCT = [[0.0] * 52 for _ in range(52)]
for _x in range(52):
    for _y in range(52):
        if _x != _y:
            PCT[_x][_y] = PCT_CLASS[_class_name(_x, _y)]
# All 1326 combos sorted weakest to strongest, for sampling from "top X%" ranges.
COMBOS = sorted(((PCT[_x][_y], _x, _y) for _x in range(52) for _y in range(_x + 1, 52)))
COMBO_PCT = [c[0] for c in COMBOS]


def _range_start(cut):
    """Index of the first combo whose percentile is >= cut."""
    lo, hi = 0, len(COMBO_PCT)
    while lo < hi:
        mid = (lo + hi) // 2
        if COMBO_PCT[mid] < cut:
            lo = mid + 1
        else:
            hi = mid
    return min(lo, len(COMBO_PCT) - 20)


def card(s):
    return RANKS.index(s[0]) * 4 + SUITS.index(s[1])


def _straight_high(mask):
    m = (mask << 1) | (1 if mask & 4096 else 0)
    for top in range(13, 3, -1):
        if (m >> (top - 4)) & 31 == 31:
            return top - 1
    return -1


def evaluate(cards):
    """Best 5-card hand from 5-7 int cards as a comparable tuple."""
    counts = [0] * 13
    suits = [0, 0, 0, 0]
    smask = [0, 0, 0, 0]
    mask = 0
    for c in cards:
        r = c >> 2
        s = c & 3
        counts[r] += 1
        suits[s] += 1
        smask[s] |= 1 << r
        mask |= 1 << r
    flush = None
    for s in range(4):
        if suits[s] >= 5:
            sh = _straight_high(smask[s])
            if sh >= 0:
                return (8, sh)
            fm = smask[s]
            flush = tuple(r for r in range(12, -1, -1) if fm >> r & 1)[:5]
            break
    quad = trip = -1
    pairs = []
    singles = []
    for r in range(12, -1, -1):
        n = counts[r]
        if n == 4:
            quad = r
        elif n == 3:
            if trip < 0:
                trip = r
            else:
                pairs.append(r)
        elif n == 2:
            pairs.append(r)
        elif n == 1:
            singles.append(r)
    if quad >= 0:
        return (7, quad, max(r for r in range(13) if counts[r] and r != quad))
    if trip >= 0 and pairs:
        return (6, trip, pairs[0])
    if flush:
        return (5,) + flush
    sh = _straight_high(mask)
    if sh >= 0:
        return (4, sh)
    if trip >= 0:
        return (3, trip) + tuple(singles[:2])
    if len(pairs) >= 2:
        rest = [r for r in range(12, -1, -1) if counts[r] and r != pairs[0] and r != pairs[1]]
        return (2, pairs[0], pairs[1], rest[0])
    if pairs:
        return (1, pairs[0]) + tuple(singles[:3])
    return (0,) + tuple(singles[:5])


def _has_draw(hole, board):
    """Flush draw or open-ended straight draw that uses a hole card."""
    cards = hole + board
    for s in range(4):
        n = sum(1 for c in cards if c & 3 == s)
        if n == 4 and any(c & 3 == s for c in hole):
            return True
    mask = 0
    for c in cards:
        mask |= 1 << (c >> 2)
    hmask = 0
    for c in hole:
        hmask |= 1 << (c >> 2)
    m = (mask << 1) | (1 if mask & 4096 else 0)
    hm = (hmask << 1) | (1 if hmask & 4096 else 0)
    for lo in range(0, 11):
        w = (m >> lo) & 15
        if w == 15 and (hm >> lo) & 15:
            return True
    return False


def _made(hole, board):
    """Made-hand level using our hole cards: 0 nothing, 1 weak pair, 2 top pair/overpair,
    3 two pair, 4 trips, 5 straight or better."""
    t = evaluate(hole + board)
    cat = t[0]
    if cat >= 4:
        return 5
    hr = [c >> 2 for c in hole]
    br = [c >> 2 for c in board]
    bmax = max(br)
    if cat == 3:
        return 4 if t[1] in hr else 0
    if cat == 2:
        n_hole = (t[1] in hr) + (t[2] in hr)
        if n_hole == 2 or (n_hole == 1 and br.count(t[1]) + br.count(t[2]) < 3):
            return 3
        return 2 if (t[1] in hr and t[1] >= bmax) or (t[2] in hr and t[2] >= bmax) else (1 if n_hole else 0)
    if cat == 1:
        p = t[1]
        if p not in hr:
            return 0
        return 2 if p >= bmax else 1
    return 0


class _Opp:
    """Per-seat frequencies for one round, each with a prior so hand 1 is sane."""

    def __init__(self):
        self.hands = 0
        self.vpip = 0
        self.un_opp = [0, 0]      # unraised pot: early seats / late seats
        self.un_raise = [0, 0]
        self.vo_opp = 0           # facing one raise, not yet raised
        self.vo_raise = 0
        self.vo_call = 0
        self.v3_opp = 0           # raised, then faced a (non all-in) reraise
        self.v3_fold = 0
        self.v3_raise = 0
        self.vjr_opp = 0          # facing a jam-sized raise after raising
        self.vjr_call = 0
        self.vjc_opp = 0          # facing a jam-sized raise cold
        self.vjc_call = 0
        self.bigr = 0             # jam-sized preflop raises made
        self.agg = 0
        self.pas = 0
        self.faced = 0
        self.folded_to_bet = 0

    def vpip_rate(self):
        return (self.vpip + 2.5) / (self.hands + 10.0)

    def pfr(self, b):
        pri = 0.28 if b else 0.13
        return (self.un_raise[b] + pri * 8.0) / (self.un_opp[b] + 8.0)

    def three(self):
        return (self.vo_raise + 0.6) / (self.vo_opp + 12.0)

    def call_open(self):
        return (self.vo_call + 1.5) / (self.vo_opp + 10.0)

    def fold_open(self):
        return max(0.0, 1.0 - self.three() - self.call_open())

    def v3fold(self):
        return (self.v3_fold + 2.0) / (self.v3_opp + 5.0)

    def v3raise(self):
        return (self.v3_raise + 1.75) / (self.v3_opp + 5.0)

    def jam_call_raised(self):
        return (self.vjr_call + 3.3) / (self.vjr_opp + 6.0)

    def jam_call_cold(self):
        return (self.vjc_call + 0.6) / (self.vjc_opp + 10.0)

    def big_rate(self):
        return (self.bigr + 0.25) / (self.hands + 12.0)

    def agg_rate(self):
        return (self.agg + 3.0) / (self.agg + self.pas + 10.0)

    def fold_rate(self):
        return (self.folded_to_bet + 4.0) / (self.faced + 10.0)


class Agent:
    BANK_TARGET = 5.5      # seconds of the 10 s bank we plan to use
    MAX_THINK = 0.0025     # seconds per decision, hard ceiling
    FIXED_SIMS = None      # testing only: exact simulation count, ignores the clock

    def __init__(self):
        self.rng = random.Random()
        self.opps = {}
        self.used = 0.0
        self.seat = 0
        self.n = 8
        self.bb = 20
        self.hands_total = 1000

    # ------------------------------------------------------------ callbacks
    def on_table_start(self, info):
        self.seat = info.get("seat", 0)
        self.n = info.get("num_players", 8)
        self.bb = info.get("big_blind", 20)
        self.hands_total = info.get("hands", 1000)
        self.opps = {i: _Opp() for i in range(self.n)}

    def on_hand_end(self, summary):
        try:
            self._learn(summary.get("history", []))
        except Exception:
            pass

    def act(self, state):
        t0 = time.perf_counter()
        try:
            out = self._decide(state, t0)
        except Exception:
            out = None
        self.used += time.perf_counter() - t0
        legal = state["legal_actions"]
        if not out:
            return {"action": "check"} if "check" in legal else {"action": "fold"}
        return out

    # ------------------------------------------------------------- learning
    def _learn(self, history):
        if not self.opps or not history:
            return
        n = self.n
        bb = self.bb
        big = 25 * bb
        btn = (history[0]["seat"] - 1) % n if history[0]["action"] == "small_blind" else 0
        bets = {}
        current = 0
        street = "preflop"
        raises = 0
        raised = set()
        vol = set()
        for h in history:
            s = h["seat"]
            a = h["action"]
            if h["street"] != street:
                street = h["street"]
                bets = {}
                current = 0
            o = self.opps.get(s)
            if o is None:
                o = self.opps[s] = _Opp()
            mine = bets.get(s, 0)
            if a in ("small_blind", "big_blind"):
                bets[s] = h["amount"]
                current = max(current, h["amount"])
                continue
            if street == "preflop":
                if current >= big:
                    if s in raised:
                        o.vjr_opp += 1
                        o.vjr_call += a != "fold"
                    else:
                        o.vjc_opp += 1
                        o.vjc_call += a != "fold"
                elif raises == 0:
                    d = (s - btn) % n
                    b = 1 if d in (0, 1, 2, n - 1) else 0
                    o.un_opp[b] += 1
                    o.un_raise[b] += a == "raise"
                elif s in raised:
                    o.v3_opp += 1
                    o.v3_fold += a == "fold"
                    o.v3_raise += a == "raise"
                elif raises == 1:
                    o.vo_opp += 1
                    o.vo_raise += a == "raise"
                    o.vo_call += a == "call"
                if a in ("call", "raise"):
                    vol.add(s)
                if a == "raise":
                    if h["amount"] >= big:
                        o.bigr += 1
                    raises += 1
                    raised.add(s)
            else:
                if a == "raise":
                    o.agg += 1
                elif a in ("call", "check"):
                    o.pas += 1
                if current > mine:
                    o.faced += 1
                    if a == "fold":
                        o.folded_to_bet += 1
            if a == "raise":
                bets[s] = h["amount"]
                current = h["amount"]
            elif a == "call":
                bets[s] = mine + h["amount"]
        for s in range(n):
            if s in self.opps:
                self.opps[s].hands += 1
        for s in vol:
            self.opps[s].vpip += 1

    # ------------------------------------------------------------ helpers
    def _budget(self, state):
        left_bank = self.BANK_TARGET - self.used
        hands_left = max(1, self.hands_total - state.get("hand_number", 1) + 1)
        per = left_bank / float(hands_left)
        return max(0.0003, min(self.MAX_THINK, per))

    def _min_sims(self):
        # Never let a long table (the 5,000-hand final) drain the time bank.
        if self.used < self.BANK_TARGET:
            return 60
        return 24 if self.used < 7.5 else 6

    def _pre_fracs(self, state):
        """Top-fraction-of-hands range for every seat that acted voluntarily preflop."""
        n = len(state["stacks"])
        btn = state["button"]
        big = 25 * state["big_blind"]
        f = {}
        raises = 0
        raised = set()
        cur = 0
        for h in state["history"]:
            if h["street"] != "preflop":
                break
            a = h["action"]
            if a not in ("raise", "call"):
                continue
            s = h["seat"]
            o = self.opps.get(s) or _Opp()
            prev = f.get(s, 1.0)
            if a == "raise":
                amt = h["amount"]
                if s in raised:
                    x = prev * o.v3raise()
                elif raises == 0:
                    d = (s - btn) % n
                    x = o.pfr(1 if d in (0, 1, 2, n - 1) else 0)
                elif raises == 1:
                    x = o.three()
                else:
                    x = 0.03
                if amt >= big:
                    x = min(x, o.big_rate() * 1.3)
                raises += 1
                raised.add(s)
                cur = amt
            else:
                if cur >= big:
                    x = prev * o.jam_call_raised() if s in raised else o.jam_call_cold()
                elif raises == 0:
                    x = o.vpip_rate()
                elif s in raised:
                    x = prev * (1.0 - o.v3fold())
                elif raises == 1:
                    x = o.three() + o.call_open()
                else:
                    x = 0.05
            f[s] = max(0.012, min(prev, x))
        return f

    def _ranges(self, state, opps):
        """Per opponent: preflop cut-off, postflop aggression level, bluffiness."""
        fr = self._pre_fracs(state)
        bb = state["big_blind"]
        lvl = {}
        pot = 0
        bets = {}
        st = "preflop"
        cur = 0
        for h in state["history"]:
            if h["street"] != st:
                st = h["street"]
                bets = {}
                cur = 0
            a = h["action"]
            s = h["seat"]
            amt = h.get("amount", 0) or 0
            if a in ("small_blind", "big_blind"):
                pot += amt
                bets[s] = amt
                cur = max(cur, amt)
            elif a == "call":
                pot += amt
                bets[s] = bets.get(s, 0) + amt
            elif a == "raise":
                added = amt - bets.get(s, 0)
                if st != "preflop":
                    pts = 1.0
                    if cur > 0:
                        pts += 1.0             # a raise over a bet
                    if added > 0.8 * pot:
                        pts += 0.5
                    if added >= 30 * bb:
                        pts += 0.5
                    lvl[s] = lvl.get(s, 0.0) + pts
                pot += added
                bets[s] = amt
                cur = amt
        res = {}
        for s in opps:
            o = self.opps.get(s) or _Opp()
            res[s] = (max(0.0, min(1.0 - fr.get(s, 1.0), 0.985)), lvl.get(s, 0.0), o.agg_rate())
        return res

    def _equity(self, hole, board, opp_ranges, deadline, min_sims=60):
        """Monte Carlo share of the pot against opponents' estimated ranges."""
        rng = self.rng
        rand = rng.random
        base_used = set(hole + board)
        deck = [c for c in range(52) if c not in base_used]
        need = 5 - len(board)
        bcat = self._board_cat(board) if len(board) >= 3 else 0
        bmax = max(c >> 2 for c in board) if board else 0
        specs = [(_range_start(cut) if cut > 0 else 0, post_agg, aggr)
                 for cut, post_agg, aggr in opp_ranges.values()]
        ncombo = len(COMBOS)
        win = 0.0
        sims = 0
        perf = time.perf_counter
        fixed = self.FIXED_SIMS
        min_sims = min(min_sims, self._min_sims())
        hard = deadline + (0.001 if min_sims >= 60 else 0.0003)
        while True:
            if fixed:
                if sims >= fixed:
                    break
            else:
                now = perf()
                if now > hard or (sims >= min_sims and now > deadline):
                    break
                if sims >= 3000:
                    break
            taken = set(base_used)
            hands = []
            for start, post_agg, aggr in specs:
                got = None
                fallback = None
                for _try in range(16):
                    # 3% of the time allow any hand: opponents make mistakes.
                    lo = 0 if rand() < 0.03 else start
                    _, a, b = COMBOS[lo + int(rand() * (ncombo - lo))]
                    if a in taken or b in taken:
                        continue
                    if fallback is None:
                        fallback = (a, b)
                    if post_agg and board:
                        h = [a, b]
                        t = evaluate(h + board)
                        cat = t[0]
                        if cat > bcat:
                            if cat >= 3 or (cat == 2 and bcat == 0):
                                sc = 3.0
                            elif cat == 1:
                                sc = 2.0 if t[1] >= bmax else 1.0
                            else:
                                sc = 1.0
                        elif need and _has_draw(h, board):
                            sc = 1.5
                        else:
                            sc = 0.0
                        if post_agg < 2.0:
                            keep = 1.0 if sc >= 1.0 else aggr * 0.9
                        elif post_agg < 3.0:
                            keep = 1.0 if sc >= 1.5 else (max(0.4, min(1.0, aggr * 1.3)) if sc >= 1.0 else aggr * 0.5)
                        elif sc >= 3.0:
                            keep = 1.0
                        else:
                            keep = (max(0.45, min(1.0, aggr * 1.1)) if sc >= 2.0 else
                                    (0.3 if sc >= 1.5 else (max(0.1, aggr * 0.5) if sc >= 1.0 else aggr * 0.2)))
                        if keep < 1.0 and rand() > keep:
                            continue
                    got = (a, b)
                    break
                if got is None:
                    got = fallback
                if got is None:
                    for a in deck:
                        if a not in taken:
                            for b in deck:
                                if b != a and b not in taken:
                                    got = (a, b)
                                    break
                            break
                taken.add(got[0])
                taken.add(got[1])
                hands.append(got)
            runout = list(board)
            while len(runout) < 5:
                c = deck[int(rand() * len(deck))]
                if c not in taken:
                    taken.add(c)
                    runout.append(c)
            me = evaluate(hole + runout)
            ties = 1
            lost = False
            for a, b in hands:
                sc = evaluate([a, b] + runout)
                if sc > me:
                    lost = True
                    break
                if sc == me:
                    ties += 1
            if not lost:
                win += 1.0 / ties
            sims += 1
        return win / sims if sims else 0.5

    def _cat_partial(self, h, board):
        # category of best hand using available cards (5 or 6 total)
        return evaluate(h + board)[0]

    def _board_cat(self, board):
        cnt = {}
        for c in board:
            cnt[c >> 2] = cnt.get(c >> 2, 0) + 1
        m = max(cnt.values())
        if m >= 3:
            return 3
        if list(cnt.values()).count(2) >= 2:
            return 2
        if m == 2:
            return 1
        return 0

    @staticmethod
    def _raise(state, target):
        lo, hi = state["min_raise_to"], state["max_raise_to"]
        if lo is None:
            return None
        target = int(max(lo, min(hi, target)))
        if target >= hi * 0.8:
            target = hi
        return {"action": "raise", "amount": target}

    @staticmethod
    def _passive(state):
        legal = state["legal_actions"]
        return {"action": "check"} if "check" in legal else {"action": "fold"}

    # ------------------------------------------------------------ decisions
    def _decide(self, state, t0):
        hole = [card(c) for c in state["hole_cards"]]
        board = [card(c) for c in state["board"]]
        if state["street"] == "preflop":
            return self._preflop(state, hole, t0)
        return self._postflop(state, hole, board, t0)

    def _preflop(self, state, hole, t0):
        legal = state["legal_actions"]
        me = state["seat"]
        n = len(state["stacks"])
        bb = state["big_blind"]
        btn = state["button"]
        name = _class_name(hole[0], hole[1])
        top = 1.0 - PCT_CLASS[name]            # 0 = best hand
        pair = name[0] == name[1]
        suited = name.endswith("s")
        d = (me - btn) % n                     # 0 btn, 1 sb, 2 bb, 3 utg ...
        hist = [h for h in state["history"] if h["action"] in ("raise", "call")]
        raises = [h for h in hist if h["action"] == "raise"]
        to_call = state["to_call"]
        pot = state["pot"]
        cur = max(state["bets"])
        mine = state["bets"][me]
        stack = state["stacks"][me]
        can_raise = "raise" in legal
        call = {"action": "call"} if to_call > 0 else {"action": "check"}
        fold = {"action": "fold"} if to_call > 0 else {"action": "check"}

        if not raises:
            limpers = set(h["seat"] for h in hist)
            limpers.discard(me)
            nl = len(limpers)
            if d == 0:
                base = 0.40
            elif d == 1:
                base = 0.36
            elif d == 2:
                base = 0.10
            elif d == n - 1:
                base = 0.27
            elif d == n - 2 and n >= 6:
                base = 0.20
            elif d == 3:
                base = 0.13 if n >= 7 else 0.16
            else:
                base = 0.16
            if nl == 0 and d in (0, 1, n - 1):
                blinds = [self.opps.get(x) or _Opp() for x in ((btn + 1) % n, (btn + 2) % n) if x != me]
                if all(o.vo_opp >= 12 and o.fold_open() >= 0.82 for o in blinds):
                    base += 0.12
                elif any(o.vo_opp >= 12 and o.fold_open() < 0.55 for o in blinds):
                    base -= 0.08
            if nl:
                fishy = any((self.opps.get(x) or _Opp()).vpip_rate() > 0.5 for x in limpers)
                base = min(base, 0.20) + (0.06 if fishy else 0.0)
            if top < base and can_raise:
                size = (3.0 if d == 1 else 2.5) + nl
                return self._raise(state, int(size * bb))
            if to_call == 0:
                return {"action": "check"}
            if nl >= 1 and to_call <= bb and top < 0.6 and (pair or suited or d == 1):
                return {"action": "call"}
            return {"action": "fold"}

        fr = self._pre_fracs(state)
        agg = raises[-1]["seat"]
        o = self.opps.get(agg) or _Opp()
        f_agg = fr.get(agg, 0.15)
        involved = [s for s in fr if s != me and not state["folded"][s]]
        extra = max(0, len(involved) - 1)
        i_raised = any(h["seat"] == me for h in raises)
        odds = to_call / float(pot + to_call) if to_call > 0 else 0.0
        e = eqr(name, f_agg) - 0.05 * extra
        total = stack + mine

        # Facing a jam-sized raise: pure pot odds against their jamming range.
        if cur >= 25 * bb or to_call >= 0.4 * total:
            if e >= odds + 0.03:
                return call
            return fold

        idx_me = (me - btn - 1) % n
        idx_agg = (agg - btn - 1) % n
        ip = idx_me > idx_agg
        nb = sum(1 for s in range(n) if s != me and not state["folded"][s] and state["bets"][s] < cur)
        real = (0.84 if ip else 0.68) + (0.07 if (pair or suited) else 0.0) - 0.04 * min(nb, 2)

        if not i_raised:
            if len(raises) == 1:
                ncall = max(0, len(involved) - 1)
                target = int(cur * (3.0 if ip else 3.6)) + cur * ncall
                if can_raise:
                    f_cont = max(0.012, f_agg * (1.0 - o.v3fold()))
                    if eqr(name, f_cont) - 0.05 * extra >= 0.53:
                        return self._raise(state, target)
                    v3f = o.v3fold()
                    if extra == 0 and o.v3_opp >= 5 and top < 0.28 and (suited or pair or name[0] == "A"):
                        add = min(target, state["max_raise_to"]) - mine
                        ev = (v3f * pot - (1.0 - v3f) * add * 0.75) * (0.9 ** nb)
                        if ev > bb and self.rng.random() < 0.7:
                            return self._raise(state, target)
                if e * real >= odds and to_call <= 0.12 * total:
                    return call
                return fold
            if e >= 0.60:
                return {"action": "all_in"} if can_raise else call
            if e >= 0.5 and e * real >= odds and to_call <= 0.15 * total:
                return call
            return fold

        # I raised and got reraised (not jam-sized).
        c = o.jam_call_raised()
        e_call = eqr(name, max(0.012, f_agg * c))
        add_me = total - mine
        add_opp = max(0, total - cur)
        ev_jam = (1.0 - c) * pot + c * (e_call * (pot + add_me + add_opp) - add_me)
        ev_call = e * real * (pot + to_call) - to_call
        if can_raise and extra == 0 and ev_jam > max(ev_call, 0.0) + 2 * bb and (e_call >= 0.33 or e >= 0.5):
            return {"action": "all_in"}
        if e >= 0.60 and can_raise:
            return {"action": "all_in"}
        if ev_call > 0:
            return call
        return fold

    def _postflop(self, state, hole, board, t0):
        legal = state["legal_actions"]
        me = state["seat"]
        to_call = state["to_call"]
        pot = state["pot"]
        opps = [i for i in range(len(state["stacks"])) if i != me and not state["folded"][i]]
        if not opps:
            return self._passive(state)
        deadline = t0 + self._budget(state)
        ranges = self._ranges(state, opps)
        eq = self._equity(hole, board, ranges, deadline)
        nopp = len(opps)
        can_raise = "raise" in legal
        street = state["street"]
        river = street == "river"

        frs = [(self.opps.get(s) or _Opp()).fold_rate() for s in opps]
        p_all_fold = 1.0
        for f in frs:
            p_all_fold *= f
        callers = max(1.0, sum(1.0 - f for f in frs))
        avg_fr = sum(frs) / nopp
        made = _made(hole, board) if river else 9
        if to_call == 0:
            if not can_raise:
                return {"action": "check"}
            # Real tables: river bets below top pair lost about 11bb each (199 bets).
            if river and made < 2:
                return {"action": "check"}
            # Checking realises only part of our equity; the rest is lost to
            # bets we fold to later. On the river it is exact.
            real = 1.0 if river else 0.85
            ev_check = eq * pot * real
            best, best_size = ev_check, 0
            # Callers are stronger than the field when many hands fold.
            eq_c = max(0.0, eq - 0.12 * avg_fr) if eq < 0.7 else eq
            for frac in (0.5, 0.75, 1.0):
                b = pot * frac
                ev = p_all_fold * pot + (1.0 - p_all_fold) * (eq_c * (pot + b * (1.0 + callers)) - b)
                if ev > best + 0.02 * pot:
                    best, best_size = ev, b
            if best_size:
                return self._raise(state, int(best_size))
            return {"action": "check"}

        po = to_call / float(pot + to_call)
        stack = state["stacks"][me]
        bet_frac = to_call / float(max(1, pot - to_call))
        lv = max(v[1] for v in ranges.values())
        raise_thr = 0.74 if nopp == 1 else max(0.5, 1.6 / (nopp + 1) + 0.1)
        if eq >= raise_thr and can_raise:
            cur = max(state["bets"])
            target = cur * 3 + (pot - sum(state["bets"]))
            # Only put a big part of the stack in as a raise with a very strong hand.
            if target - state["bets"][me] < 0.5 * stack or eq >= 0.82:
                return self._raise(state, target)
            return {"action": "call"}
        # Semi-bluff raise against a single bettor who folds to raises a lot.
        if (can_raise and nopp == 1 and not river and lv < 2.0 and eq > 0.3 and frs[0] > 0.45
                and self.rng.random() < (frs[0] - 0.3)):
            cur = max(state["bets"])
            return self._raise(state, cur * 3)
        # Real tables: calling river bets with a weak pair or less lost about 25bb each.
        if river and made <= 1 and bet_frac > 0.3:
            return {"action": "fold"}
        margin = (0.04 if river else 0.0) + (0.03 if bet_frac >= 0.75 else 0.0)
        if eq > po + margin:
            return {"action": "call"}
        return {"action": "fold"}
