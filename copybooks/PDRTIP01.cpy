      ****************************************************
      *         RECORD TABELLA 01     LRECL = 350        *
      *         -----------------     CHIAVE=(1,15)      *
      ****************************************************
           05  RECORD-T01.
               10  T01-CHIAVE.
                   15  T01-CHIAVE-IDTAB     PIC XX.
                   15  T01-CHIAVE-ANNO      PIC 99.
                   15  T01-CHIAVE-ANNOX   REDEFINES
                          T01-CHIAVE-ANNO   PIC XX.
                   15  T01-CHIAVE-VOCE.
                       20  T01-CHIAVE-VOCE-NTAB  PIC 9.
                       20  T01-CHIAVE-VOCE-COD   PIC 999.
                   15  T01-CHIAVE-IDSUBTAB  PIC XX.
                   15  FILLER               PIC X(5).
            SKIP1
               10  T01-VOCE-TIPO            PIC X.
               10  T01-APPLICAB.
                   15  T01-TIPO5                PIC X.
                   15  T01-TIPO6                PIC X.
                   15  T01-TIPO7                PIC X.
               10  T01-DIPENDENZA           PIC X.
               10  T01-VOCE-DESCR           PIC X(37).
           SKIP1
               10  T01-COD-OPERAT           PIC X(4).
               10  T01-ULTAGG-DATA.
                   15  T01-ULTAGG-GG        PIC 99.
                   15  T01-ULTAGG-MM        PIC 99.
                   15  T01-ULTAGG-AA        PIC 99.
               10  FILLER                   PIC X(27).
           SKIP1
               10  T01-TABMESI.
                   15  T01-TABMESI-EL OCCURS 12
                          INDEXED BY T01-IND.
                      20  T01-MESE          PIC XX.
                      20  T01-MESE-NUM  REDEFINES
                            T01-MESE        PIC 99.
                      20  T01-IMPO1-ASS     PIC S9(9) COMP-3.
                      20  T01-IMPO1-ASS-E REDEFINES T01-IMPO1-ASS
                                            PIC S9(7)V99 COMP-3.
                      20  T01-IMPO1-PERC  REDEFINES T01-IMPO1-ASS
                                            PIC S9(7)V99 COMP-3.
                      20  T01-TIPO-FRANCH   PIC X.
                      20  T01-IMPO2-ASS     PIC S9(9)  COMP-3.
                      20  T01-IMPO2-ASS-E REDEFINES T01-IMPO2-ASS
                                            PIC S9(7)V99 COMP-3.
                      20  T01-IMPO2-PERC  REDEFINES T01-IMPO2-ASS
                                            PIC S9(7)V99 COMP-3.
           SKIP1
               10  T01-VERSAM-VINCOLO             PIC X(40).
           SKIP1
               10  T01-PERIODO-VALIDITA.
                   15  T01-PERIODO-INIZ-AAAA.
                       20  T01-PERIODO-INIZ-AA12   PIC XX.
                       20  T01-PERIODO-INIZ-AA34   PIC XX.
                   15  T01-PERIODO-INIZ-MM         PIC XX.
                   15  T01-PERIODO-FINE-AAAA.
                       20  T01-PERIODO-FINE-AA12   PIC XX.
                       20  T01-PERIODO-FINE-AA34   PIC XX.
                   15  T01-PERIODO-FINE-MM         PIC XX.
           SKIP1
               10  T01-TIPO-GESTIONE               PIC XX.
               10  T01-UNITA-MONETARIA             PIC X.
               10  T01-CENTRO-SPESA                PIC X(5).
               10  T01-CATEGORIA-VOCE              PIC X(4).
               10  T01-TIPO-CEDOLINO               PIC X(1).
               10  FILLER                          PIC X(35).
      *---------------------------------------------------------*
      *   NOTE RELATIVE AL RECORD T01.                          *
      *                                                         *
      * DIPENDENZA  ('0' IMPORTO NON AGGIORNABILE IN MODO       *
      *                  AUTOMATICO; '1' SI)                    *
      *                                                         *
      * T01-TIPO-FRANCH :  '1'   PERCENTUALE PARTE IMPONIBILE   *
      *                    '2'   VALORE PARTE ESENTE            *
      *                    '0'   NON RILEVANTE                  *
      *---------------------------------------------------------*
      * T01-PERIODO-VALIDITA:
      *            -INIZ       MESE DI CREAZIONE DELLA VOCE     *
      *            -FINE       MESE DI CESSAZIONE DELLA VOCE
      *---------------------------------------------------------*
      * T01-TIPO-GESTIONE:     MODALITA' DI GESTIONE DELLA VOCE
      *                     '10'  -->  AUTOMATICA (ES. 1001/1002/2002
      *                                 .3001/3002/3013)
      *                     '20'  -->  PROCEDURA ON-LINE IP/AV
      *                     '30'  -->  INDENNITA' UFFICIO
      *                     '40'  -->  COMPENSI MISSIONI/CONCORSI
      *                                 (2100/2101/2200/2201/2202)
      *                     '50'  -->  PROCED. CONGUAGLIO
      *                                 (4500/4501/4560/4561)
      *                     '60'  -->  PROC. DETRAZIONI FISCALI(4001)
      *                     '70'  -->  PROC. COMPENSI AGGIUNTIVI(45XX)
      *                     '80'  -->  ALTRE PROCEDURE
      *---------------------------------------------------------*
      * T01-CENTRO-SPESA:        TOTALIZZAZIONI SU PDRIASS      *
      *                          CNNNN                          *
      *---------------------------------------------------------*
      * T01-CATEGORIA-VOCE:      TOTALIZZAZIONI SU RIASSUNTI    *
      *    LA DECODIFICA SI TROVA NEL PROGRAMMA PDRIASS         *
      *    NELLA TABELLA TAB02                                  *
      *---------------------------------------------------------*
      * T01-TIPO-CEDOLINO :      BLANK --> CEDOLINO BASE        *
      *                          R     --> LETTERA RIMBORSI     *
      *---------------------------------------------------------*
           SKIP1
