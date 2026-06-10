      *   Micro Focus COBOL 2022  9.0.00203
      *   Micro Focus BMS Screen Painter
      *   MapSet Name   PDB305M
      *   Date Created  10/23/2024
      *   Time Created  08:35:31

      *  Input Data For Map PDB3051
         01 PDB3051I.
            03 FILLER                         PIC X(12).
            03 X1DUMMYL                       PIC S9(4) COMP.
            03 X1DUMMYF                       PIC X.
            03 FILLER REDEFINES X1DUMMYF.
               05 X1DUMMYA                       PIC X.
            03 X1DUMMYI                       PIC X(1).
            03 MPAGL                          PIC S9(4) COMP.
            03 MPAGF                          PIC X.
            03 FILLER REDEFINES MPAGF.
               05 MPAGA                          PIC X.
            03 MPAGI                          PIC X(3).
            03 M1DATAL                        PIC S9(4) COMP.
            03 M1DATAF                        PIC X.
            03 FILLER REDEFINES M1DATAF.
               05 M1DATAA                        PIC X.
            03 M1DATAI                        PIC X(8).
            03 KTEST1L                        PIC S9(4) COMP.
            03 KTEST1F                        PIC X.
            03 FILLER REDEFINES KTEST1F.
               05 KTEST1A                        PIC X.
            03 KTEST1I                        PIC X(18).
            03 KTEST2L                        PIC S9(4) COMP.
            03 KTEST2F                        PIC X.
            03 FILLER REDEFINES KTEST2F.
               05 KTEST2A                        PIC X.
            03 KTEST2I                        PIC X(10).
            03 KTEST3L                        PIC S9(4) COMP.
            03 KTEST3F                        PIC X.
            03 FILLER REDEFINES KTEST3F.
               05 KTEST3A                        PIC X.
            03 KTEST3I                        PIC X(10).
            03 MRIGAD                         OCCURS 14 TIMES.
               05 MRIGAL                         PIC S9(4) COMP.
               05 MRIGAF                         PIC X.
               05 MRIGAI                         PIC X(79).
            03 M1PF7L                         PIC S9(4) COMP.
            03 M1PF7F                         PIC X.
            03 FILLER REDEFINES M1PF7F.
               05 M1PF7A                         PIC X.
            03 M1PF7I                         PIC X(22).
            03 MENTERL                        PIC S9(4) COMP.
            03 MENTERF                        PIC X.
            03 FILLER REDEFINES MENTERF.
               05 MENTERA                        PIC X.
            03 MENTERI                        PIC X(7).
            03 MINVIOL                        PIC S9(4) COMP.
            03 MINVIOF                        PIC X.
            03 FILLER REDEFINES MINVIOF.
               05 MINVIOA                        PIC X.
            03 MINVIOI                        PIC X(17).
            03 M1PF8L                         PIC S9(4) COMP.
            03 M1PF8F                         PIC X.
            03 FILLER REDEFINES M1PF8F.
               05 M1PF8A                         PIC X.
            03 M1PF8I                         PIC X(17).
            03 M1MSGL                         PIC S9(4) COMP.
            03 M1MSGF                         PIC X.
            03 FILLER REDEFINES M1MSGF.
               05 M1MSGA                         PIC X.
            03 M1MSGI                         PIC X(70).

      *  Output Data For Map PDB3051
         01 PDB3051O REDEFINES PDB3051I.
            03 FILLER                         PIC X(12).
            03 FILLER                         PIC X(3).
            03 X1DUMMYO                       PIC X(1).
            03 FILLER                         PIC X(3).
            03 MPAGO                          PIC X(3).
            03 FILLER                         PIC X(3).
            03 M1DATAO                        PIC X(8).
            03 FILLER                         PIC X(3).
            03 KTEST1O                        PIC X(18).
            03 FILLER                         PIC X(3).
            03 KTEST2O                        PIC X(10).
            03 FILLER                         PIC X(3).
            03 KTEST3O                        PIC X(10).
            03 DFHMS1 OCCURS 14.
               05 FILLER                         PIC X(2).
               05 MRIGAA                         PIC X.
               05 MRIGAO                         PIC X(79).
            03 FILLER                         PIC X(3).
            03 M1PF7O                         PIC X(22).
            03 FILLER                         PIC X(3).
            03 MENTERO                        PIC X(7).
            03 FILLER                         PIC X(3).
            03 MINVIOO                        PIC X(17).
            03 FILLER                         PIC X(3).
            03 M1PF8O                         PIC X(17).
            03 FILLER                         PIC X(3).
            03 M1MSGO                         PIC X(70).

