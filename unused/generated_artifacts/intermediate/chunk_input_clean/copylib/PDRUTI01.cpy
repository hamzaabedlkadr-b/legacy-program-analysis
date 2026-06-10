      *******************************************************
      *       PREVIDENZA DEPUTATI - SCHEDA PERSONALE        *
      *  AREA COMUNICAZIONE PER ROUTINE CONTROLLO CAMPI     *
      *******************************************************
           03  PDRUTI01-LUNG-COMMA          PIC S9(4) COMP
                     VALUE +500.
           03  FILLER                       PIC X.
           03  PDRUTI01-FUNZIONE            PIC XX.
           03  PDRUTI01-RETURN              PIC X.
           03  FILLER                       PIC X(10).
           03  PDRUTI01-DATIVAR             PIC X(484).
      *-------------------------------------
      *   FUNZIONE: 01  (IMPORTO ASSOLUTO)
      *-------------------------------------
           03  PDRUTI01-F01 REDEFINES PDRUTI01-DATIVAR.
               05  PDRUTI01-F01-VALORE          PIC X(16).
               05  PDRUTI01-F01-LUNGH           PIC 99.
               05  PDRUTI01-F01-IMPOX           PIC X(16).
               05  PDRUTI01-F01-IMPON REDEFINES
                        PDRUTI01-F01-IMPOX      PIC 9(16).
               SKIP1
      *-------------------------------------
      *   FUNZIONE: 02 (PERCENTUALE 3INT+2DEC)
      *-------------------------------------
           03  PDRUTI01-F02 REDEFINES PDRUTI01-DATIVAR.
               05  PDRUTI01-F02-VALORE          PIC X(16).
               05  PDRUTI01-F02-LUNGH           PIC 99.
               05  PDRUTI01-F02-PERCX           PIC X(6).
               05  PDRUTI01-F02-PERCN           PIC 999V99 COMP-3.
               SKIP1
      *-------------------------------------
      *   FUNZIONE: 22 (PERCENTUALE 2INT+3DEC)
      *-------------------------------------
           03  PDRUTI01-F22 REDEFINES PDRUTI01-DATIVAR.
               05  PDRUTI01-F22-VALORE          PIC X(16).
               05  PDRUTI01-F22-LUNGH           PIC 99.
               05  PDRUTI01-F22-PERCX           PIC X(6).
               05  PDRUTI01-F22-PERCN           PIC 99V999 COMP-3.
               SKIP1
      *------------------------------------------------------------
      *   FUNZIONE: 03  (IMPORTO IN EURO: VIRGOLA E DUE DECIMALI)
      *                 SE L'AMBIENTE NON E' EURO USA LA F01
      *------------------------------------------------------------
           03  PDRUTI01-F03 REDEFINES PDRUTI01-DATIVAR.
               05  PDRUTI01-F03-VALORE          PIC X(16).
               05  PDRUTI01-F03-LUNGH           PIC 99.
               05  PDRUTI01-F03-IMPOX-E         PIC X(16).
               05  PDRUTI01-F03-IMPON-E         PIC 9(14)V99.
               05  PDRUTI01-F03-IMPON           REDEFINES
                   PDRUTI01-F03-IMPON-E         PIC 9(16).
               SKIP1
      *------------------------------------------------------------
      *   FUNZIONE: 23  (IMPORTO IN EURO: VIRGOLA E DUE DECIMALI)
      *                 ACCETTA NUMERI NEGATIVI
      *------------------------------------------------------------
           03  PDRUTI01-F23 REDEFINES PDRUTI01-DATIVAR.
               05  PDRUTI01-F23-VALORE          PIC X(16).
               05  PDRUTI01-F23-LUNGH           PIC 99.
               05  PDRUTI01-F23-IMPOX-E         PIC X(16).
               05  PDRUTI01-F23-IMPON-E         PIC S9(14)V99.
               05  PDRUTI01-F23-IMPON           REDEFINES
                   PDRUTI01-F23-IMPON-E         PIC S9(16).
               SKIP1
      *------------------------------------------------------------
      *   FUNZIONE: 04  (FORMATTAZIONE IMPORTI DA INTERO ALFAN.
      *                 RESTITUISCE EURO O LIRE
      *   SONO DISPONIBILI I CAMPI CON SEGNO LEADING O TRAILING
      *------------------------------------------------------------
           03  PDRUTI01-F04 REDEFINES PDRUTI01-DATIVAR.
               05  PDRUTI01-F04-VALORE          PIC X(16).
      *        05  PDRUTI01-F04-IMPOF           PIC -.---.---.--9,99.
      *        05  PDRUTI01-F04-IMPOF           PIC ----.---.---.--9.
               05  PDRUTI01-F04-IMPOF           PIC X(16).
               05  PDRUTI01-F04-IMPOX16         REDEFINES
                   PDRUTI01-F04-IMPOF           PIC X(16).
               05  FILLER                       REDEFINES
                   PDRUTI01-F04-IMPOF.
                   10  FILLER                   PIC X(1).
                   10  PDRUTI01-F04-IMPOX15     PIC X(15).
               05  FILLER                       REDEFINES
                   PDRUTI01-F04-IMPOF.
                   10  FILLER                   PIC X(2).
                   10  PDRUTI01-F04-IMPOX14     PIC X(14).
               05  FILLER                       REDEFINES
                   PDRUTI01-F04-IMPOF.
                   10  FILLER                   PIC X(3).
                   10  PDRUTI01-F04-IMPOX13     PIC X(13).
               05  FILLER                       REDEFINES
                   PDRUTI01-F04-IMPOF.
                   10  FILLER                   PIC X(4).
                   10  PDRUTI01-F04-IMPOX12     PIC X(12).
               05  FILLER                       REDEFINES
                   PDRUTI01-F04-IMPOF.
                   10  FILLER                   PIC X(5).
                   10  PDRUTI01-F04-IMPOX11     PIC X(11).
               05  FILLER                       REDEFINES
                   PDRUTI01-F04-IMPOF.
                   10  FILLER                   PIC X(6).
                   10  PDRUTI01-F04-IMPOX10     PIC X(10).
               05  FILLER                       REDEFINES
                   PDRUTI01-F04-IMPOF.
                   10  FILLER                   PIC X(7).
                   10  PDRUTI01-F04-IMPOX09     PIC X(09).
               SKIP1
      *        CAMPO DI OUTPUT CON TRAILING SIGN
      *        05  PDRUTI01-F04-TS-IMPOF        PIC ZZZZ.ZZZ.ZZ9,99-.
      *        05  PDRUTI01-F04-TS-IMPOF        PIC ZZZ.ZZZ.ZZZ.ZZ9-.
               05  PDRUTI01-F04-TS-IMPOF        PIC X(16).
               05  PDRUTI01-F04-TS-IMPOX16      REDEFINES
                   PDRUTI01-F04-TS-IMPOF        PIC X(16).
               05  FILLER                       REDEFINES
                   PDRUTI01-F04-TS-IMPOF.
                   10  FILLER                   PIC X(1).
                   10  PDRUTI01-F04-TS-IMPOX15  PIC X(15).
               05  FILLER                       REDEFINES
                   PDRUTI01-F04-TS-IMPOF.
                   10  FILLER                   PIC X(2).
                   10  PDRUTI01-F04-TS-IMPOX14  PIC X(14).
               05  FILLER                       REDEFINES
                   PDRUTI01-F04-TS-IMPOF.
                   10  FILLER                   PIC X(3).
                   10  PDRUTI01-F04-TS-IMPOX13  PIC X(13).
               05  FILLER                       REDEFINES
                   PDRUTI01-F04-TS-IMPOF.
                   10  FILLER                   PIC X(4).
                   10  PDRUTI01-F04-TS-IMPOX12  PIC X(12).
               05  FILLER                       REDEFINES
                   PDRUTI01-F04-TS-IMPOF.
                   10  FILLER                   PIC X(5).
                   10  PDRUTI01-F04-TS-IMPOX11  PIC X(11).
               05  FILLER                       REDEFINES
                   PDRUTI01-F04-TS-IMPOF.
                   10  FILLER                   PIC X(6).
                   10  PDRUTI01-F04-TS-IMPOX10  PIC X(10).
               05  FILLER                       REDEFINES
                   PDRUTI01-F04-TS-IMPOF.
                   10  FILLER                   PIC X(7).
                   10  PDRUTI01-F04-TS-IMPOX09  PIC X(09).
               SKIP1
      *------------------------------------------------------------
      *   FUNZIONE: 05  (FORMATTAZIONE IMPORTI DA INTERO NUM.
      *                 RESTITUISCE EURO O LIRE
      *   SONO DISPONIBILI I CAMPI CON SEGNO LEADING O TRAILING
      *------------------------------------------------------------
           03  PDRUTI01-F05 REDEFINES PDRUTI01-DATIVAR.
               05  PDRUTI01-F05-VALORE          PIC S9(16).
      *        05  PDRUTI01-F05-IMPOF           PIC -.---.---.--9,99.
      *        05  PDRUTI01-F05-IMPOF           PIC ----.---.---.--9.
               05  PDRUTI01-F05-IMPOF           PIC X(16).
               05  PDRUTI01-F05-IMPOX16         REDEFINES
                   PDRUTI01-F05-IMPOF           PIC X(16).
               05  FILLER                       REDEFINES
                   PDRUTI01-F05-IMPOF.
                   10  FILLER                   PIC X(1).
                   10  PDRUTI01-F05-IMPOX15     PIC X(15).
               05  FILLER                       REDEFINES
                   PDRUTI01-F05-IMPOF.
                   10  FILLER                   PIC X(2).
                   10  PDRUTI01-F05-IMPOX14     PIC X(14).
               05  FILLER                       REDEFINES
                   PDRUTI01-F05-IMPOF.
                   10  FILLER                   PIC X(3).
                   10  PDRUTI01-F05-IMPOX13     PIC X(13).
               05  FILLER                       REDEFINES
                   PDRUTI01-F05-IMPOF.
                   10  FILLER                   PIC X(4).
                   10  PDRUTI01-F05-IMPOX12     PIC X(12).
               05  FILLER                       REDEFINES
                   PDRUTI01-F05-IMPOF.
                   10  FILLER                   PIC X(5).
                   10  PDRUTI01-F05-IMPOX11     PIC X(11).
               05  FILLER                       REDEFINES
                   PDRUTI01-F05-IMPOF.
                   10  FILLER                   PIC X(6).
                   10  PDRUTI01-F05-IMPOX10     PIC X(10).
               05  FILLER                       REDEFINES
                   PDRUTI01-F05-IMPOF.
                   10  FILLER                   PIC X(7).
                   10  PDRUTI01-F05-IMPOX09     PIC X(09).
               SKIP1
      *        CAMPO DI OUTPUT CON TRAILING SIGN
      *        05  PDRUTI01-F05-TS-IMPOF        PIC ZZZZ.ZZZ.ZZ9,99-.
      *        05  PDRUTI01-F05-TS-IMPOF        PIC ZZZ.ZZZ.ZZZ.ZZ9-.
               05  PDRUTI01-F05-TS-IMPOF        PIC X(16).
               05  PDRUTI01-F05-TS-IMPOX16      REDEFINES
                   PDRUTI01-F05-TS-IMPOF        PIC X(16).
               05  FILLER                       REDEFINES
                   PDRUTI01-F05-TS-IMPOF.
                   10  FILLER                   PIC X(1).
                   10  PDRUTI01-F05-TS-IMPOX15  PIC X(15).
               05  FILLER                       REDEFINES
                   PDRUTI01-F05-TS-IMPOF.
                   10  FILLER                   PIC X(2).
                   10  PDRUTI01-F05-TS-IMPOX14  PIC X(14).
               05  FILLER                       REDEFINES
                   PDRUTI01-F05-TS-IMPOF.
                   10  FILLER                   PIC X(3).
                   10  PDRUTI01-F05-TS-IMPOX13  PIC X(13).
               05  FILLER                       REDEFINES
                   PDRUTI01-F05-TS-IMPOF.
                   10  FILLER                   PIC X(4).
                   10  PDRUTI01-F05-TS-IMPOX12  PIC X(12).
               05  FILLER                       REDEFINES
                   PDRUTI01-F05-TS-IMPOF.
                   10  FILLER                   PIC X(5).
                   10  PDRUTI01-F05-TS-IMPOX11  PIC X(11).
               05  FILLER                       REDEFINES
                   PDRUTI01-F05-TS-IMPOF.
                   10  FILLER                   PIC X(6).
                   10  PDRUTI01-F05-TS-IMPOX10  PIC X(10).
               05  FILLER                       REDEFINES
                   PDRUTI01-F05-TS-IMPOF.
                   10  FILLER                   PIC X(7).
                   10  PDRUTI01-F05-TS-IMPOX09  PIC X(09).
               SKIP1
      *------------------------------------------------------------
      *   FUNZIONE: 06   SIMBOLI DELLA VALUTA ATTIVA
      *------------------------------------------------------------
           03  PDRUTI01-F06 REDEFINES PDRUTI01-DATIVAR.
               05  PDRUTI01-F06-VALUTA          PIC X(4).
               05  PDRUTI01-F06-VALUTA-MINUS    PIC X(4).
               05  PDRUTI01-F06-VALUTA-DESCR    PIC X(20).
               05  PDRUTI01-F06-VALUTA-SIGLA    PIC X(1).
               SKIP1
      *-------------------------------------
      *      FUNZIONI: 10/11/12/13/14  GESTIONE DATE
      *
      *  FUNZIONE: 10    CONTROLLO FORMALE DATA
      *  FUNZIONE: 11    CONFRONTO FRA 2 DATE
      *  FUNZIONE: 12    TROVA LA DATA PRECEDENTE
      *  FUNZIONE: 13    TROVA LA DATA SUCCESSIVA
      *  FUNZIONE: 14    CALCOLA NUMERO GIORNI FRA 2 DATE
      *                    (ESTREMI COMPRESI)
      *  FUNZIONE: 15    CALCOLA NUMERO GIORNI DI UN MESE
      *-------------------------------------
           03  PDRUTI01-F10 REDEFINES PDRUTI01-DATIVAR.
               05  PDRUTI01-F10-DATA1.
                   07  PDRUTI01-F10-DATA1-GG     PIC XX.
                   07  PDRUTI01-F10-DATA1-MM     PIC XX.
                   07  PDRUTI01-F10-DATA1-AAAA.
                       09 PDRUTI01-F10-DATA1-AA12   PIC XX.
                       09 PDRUTI01-F10-DATA1-AA34   PIC XX.
               SKIP1
               05  PDRUTI01-F10-DATA2.
                   07  PDRUTI01-F10-DATA2-GG     PIC XX.
                   07  PDRUTI01-F10-DATA2-MM     PIC XX.
                   07  PDRUTI01-F10-DATA2-AAAA.
                       09 PDRUTI01-F10-DATA2-AA12   PIC XX.
                       09 PDRUTI01-F10-DATA2-AA34   PIC XX.
               05  PDRUTI01-F10-SWCONTIGUE          PIC X.
               05  PDRUTI01-F14-NUMGG               PIC S9(7) COMP-3.
               SKIP1
      *-------------------------------------
      *   FUNZIONE: 20  COMPATTA CAMPI
      *-------------------------------------
           03  PDRUTI01-F20 REDEFINES PDRUTI01-DATIVAR.
               05  PDRUTI01-F20-CAMPO1           PIC X(120).
               05  PDRUTI01-F20-CAMPO2           PIC X(120).
               05  PDRUTI01-F20-COMPATTATO       PIC X(240).
               05  PDRUTI01-F20-CAR-SEPARA       PIC X.
               05  PDRUTI01-F20-NUM-CAR          PIC S9(3) COMP-3.
               SKIP1
      *******************************************************
      *  1)  PDRUTI01-FUNZIONE
      *        '01'  -->  CONTROLLO IMPORTO INTERO
      *        '02'  -->  CONTROLLO PERCENTUALE
      *        '03'  -->  CONTROLLO IMPORTO EURO
      *        '04'  -->  FORMATTAZIONE IMPORTI DA STRINGA
      *        '05'  -->  FORMATTAZIONE IMPORTI DA NUMERO
      *        '06'  -->  COSTANTI RELATIVE ALLA VALUTA
      *        '10'  -->  CONTROLLO DATA
      *        '11'  -->  CONFRONTO DATE
      *        '12'  -->  DETERMINA LA DATA PRECEDENTE
      *        '13'  -->  DETERMINA LA DATA SUCCESSIVA
      *        '14'  -->  CALCOLA NUMERO GIORNI FRA 2 DATE
      *        '15'  -->  CALCOLA NUMERO GIORNI DEL MESE
      *        '20'  -->  COMPATTA 2 CAMPI
      *        '22'  -->  CONTROLLO PERCENTUALE 2INT+3DEC
      *        '23'  -->  CONTROLLO IMPORTI EURO CON NEGATIVI
      *
      *  2)  PDRUTI01-RETURN
      *        'E'   -->  PARAMETRI PASSATI NON VALIDI
      *---------------------------------------------------------
      *
      *                  FUNZIONE 01
      *                  -----------
      *
      *  I)  PDRUTI01-F01-VALORE         CAMPO DA CONTROLLARE
      *      PDRUTI01-F01-LUNGH          LUNGHEZZA DEL CAMPO
      *
      *  O)  PDRUTI01-F01-IMPOX          VALORE NORMALIZZATO
      *      PDRUTI01-F01-IMPON             "     "     "
      *
      *      PDRUTI01-RETURN
      *
      *         '0'  -->  TUTTO OK
      *         '1'  -->  IMPORTO ERRATO
      *
      *---------------------------------------------------------
      *                   FUNZIONE 02
      *                   -----------
      *
      *  I)  PDRUTI01-F02-VALORE         CAMPO DA CONTROLLARE
      *      PDRUTI01-F02-LUNGH          LUNGHEZZA DEL CAMPO
      *
      *  O)  PDRUTI01-F02-PERCX          PERC. NORMALIZZATA(XXX,XX)
      *      PDRUTI01-F02-PERCN          PERC. NUMERICA  (999V99)
      *
      *      PDRUTI01-RETURN
      *
      *         '0'  -->  TUTTO OK
      *         '1'  -->  PERCENTUALE ERRATA
      *
      *---------------------------------------------------------
      *                   FUNZIONE 22
      *                   -----------
      *
      *  I)  PDRUTI01-F22-VALORE         CAMPO DA CONTROLLARE
      *      PDRUTI01-F22-LUNGH          LUNGHEZZA DEL CAMPO
      *
      *  O)  PDRUTI01-F22-PERCX          PERC. NORMALIZZATA(XX,XXX)
      *      PDRUTI01-F22-PERCN          PERC. NUMERICA  (99V999)
      *
      *      PDRUTI01-RETURN
      *
      *         '0'  -->  TUTTO OK
      *         '1'  -->  PERCENTUALE ERRATA
      *
      *---------------------------------------------------------
      *
      *                  FUNZIONE 03
      *                  -----------
      *
      *  I)  PDRUTI01-F03-VALORE         CAMPO DA CONTROLLARE
      *      PDRUTI01-F03-LUNGH          LUNGHEZZA DEL CAMPO
      *
      *  O)  PDRUTI01-F03-IMPOX-E        VALORE NORMALIZZATO IN EURO
      *      PDRUTI01-F03-IMPON-E           "     "     "     "  "
      *      PDRUTI01-F03-IMPON             "     "     "    INTERO
      *                                           (IN CENTESIMI DI EURO)
      *  SE L'AREA PDWUTI01 CONTIENE "LIRE" ALLORA USA LA FUNZIONE F01
      *
      *      PDRUTI01-RETURN
      *
      *         '0'  -->  TUTTO OK
      *         '1'  -->  IMPORTO ERRATO
      *
      *---------------------------------------------------------
      *
      *                  FUNZIONE 23
      *                  -----------
      *
      *  I)  PDRUTI01-F23-VALORE         CAMPO DA CONTROLLARE CON NEGAT.
      *      PDRUTI01-F23-LUNGH          LUNGHEZZA DEL CAMPO
      *
      *  O)  PDRUTI01-F23-IMPOX-E        VALORE NORMALIZZATO IN EURO
      *      PDRUTI01-F23-IMPON-E           "     "     "     "  "
      *      PDRUTI01-F23-IMPON             "     "     "    INTERO
      *                                           (IN CENTESIMI DI EURO)
      *
      *      PDRUTI01-RETURN
      *
      *         '0'  -->  TUTTO OK
      *         '1'  -->  IMPORTO ERRATO
      *
      *---------------------------------------------------------
      *
      *                  FUNZIONE 04
      *                  -----------
      *
      *  I)  PDRUTI01-F04-VALORE         CAMPO ALFANUMERICO INTERO
      *
      *  O)  PDRUTI01-F04-IMPOF          VALORE NORMALIZZATO IN VALUTA
      *      PDRUTI01-F04-IMPOXNN        SOTTOINSIEMI ALLINEATI A DX
      *      PDRUTI01-F04-TS-IMPOXNN     SOTTOINSIEMI ALLINEATI A DX
      *                                    CON SEGNO TRAILING
      *  LA VALUTA DI USCITA DIPENDE DA PDWUTI01
      *
      *      PDRUTI01-RETURN
      *
      *         '0'  -->  TUTTO OK
      *         '1'  -->  IMPORTO ERRATO
      *
      *---------------------------------------------------------
      *
      *                  FUNZIONE 05
      *                  -----------
      *
      *  I)  PDRUTI01-F05-VALORE         CAMPO NUMERICO INTERO
      *
      *  O)  PDRUTI01-F05-IMPOF          VALORE NORMALIZZATO IN VALUTA
      *      PDRUTI01-F05-IMPOXNN        SOTTOINSIEMI ALLINEATI A DX
      *      PDRUTI01-F05-TS-IMPOXNN     SOTTOINSIEMI ALLINEATI A DX
      *                                     CON SEGNO TRAILING
      *  LA VALUTA DI USCITA DIPENDE DA PDWUTI01
      *
      *      PDRUTI01-RETURN
      *
      *         '0'  -->  TUTTO OK
      *         '1'  -->  IMPORTO ERRATO
      *
      *---------------------------------------------------------
      *
      *                  FUNZIONE 06
      *                  -----------
      *
      *  O)  PDRUTI01-F05-VALUTA         "LIRE" O "EURO"
      *      PDRUTI01-F05-VALUTA-MINUS   "Lire" O "Euro"
      *      PDRUTI01-F05-VALUTA-DESCR   "LIRE ITALIANE" O "EURO"
      *      PDRUTI01-F05-VALUTA-SIGLA   "L" O "E"
      *
      *  LA VALUTA DI USCITA DIPENDE DA PDWUTI01
      *
      *      PDRUTI01-RETURN
      *
      *         '0'  -->  TUTTO OK
      *         '1'  -->  IMPORTO ERRATO
      *
      *---------------------------------------------------------
      *                   FUNZIONE 10
      *                   -----------
      *
      *  I)  PDRUTI01-F10-DATA1          DATA DA CONTROLLARE
      *
      *
      *  O)  PDRUTI01-RETURN
      *
      *         '0'  -->  TUTTO OK
      *         '1'  -->  DATA  ERRATA
      *
      *---------------------------------------------------------
      *                   FUNZIONE 11
      *                   -----------
      *
      *  I)  PDRUTI01-F10-DATA1          PRIMA DATA
      *      PDRUTI01-F10-DATA2          SECONDA DATA
      *
      *  O)  PDRUTI01-F10-SWCONTIGUE     (S/N)
      *
      *      PDRUTI01-RETURN
      *
      *         '0'  -->  DATE UGUALI
      *         '1'  -->  DATA1 MINORE DI DATA2
      *         '2'  -->  DATA1 MAGGIORE DI DATA2
      *
      *---------------------------------------------------------
      *                   FUNZIONE 12
      *                   -----------
      *  I)   -F10-DATA1
      *
      *  O)   -F10-DATA2     DATA PRECEDENTE
      *
      *---------------------------------------------------------
      *                   FUNZIONE 13
      *                   -----------
      *  I)   -F10-DATA1
      *
      *  O)   -F10-DATA2     DATA SUCCESSIVA
      *
      *---------------------------------------------------------
      *                   FUNZIONE 14
      *                   -----------
      *  I)   -F10-DATA1     DATA INIZIALE
      *       -F10-DATA2     DATA FINALE
      *
      *  O)   -F14-NUMGG     NUMERO GIORNI FRA LE 2 DATE
      *                       (ESTREMI COMPRESI)
      *---------------------------------------------------------
      *                   FUNZIONE 15
      *                   -----------
      *  I)   -F10-DATA1-AAAA      ANNO
      *       -F10-DATA1-MM        MESE
      *
      *  O)   -F10-DATA1-GG  NUMERO GIORNI DELE MESE
      *---------------------------------------------------------
      *                   FUNZIONE 20
      *                   -----------
      *  I)   -F20-CAMPO1
      *       -F20-CAMPO2
      *       -F20-CAR-SEPARA
      *
      *  O)   -F20-COMPATTATO
      *
      *---------------------------------------------------------
      *
      *******************************************************
              SKIP1
