      ************************************************************      
      *                                                          *      
      *  PDCBVC: BROWSE VOCI CONTABILI                           *      
      *                                                          *      
      *                                                          *      
      ************************************************************      
           SKIP2                                                        
      ************************************************************      
      *   IDENTIFICATION DIVISION                                *      
       IDENTIFICATION DIVISION.                                         
       PROGRAM-ID. PDCBVC.                                              
       AUTHOR. CONSONI.                                                 
           SKIP1                                                        
      ************************************************************      
      *   ENVIRONMENT DIVISION                                   *      
      ************************************************************      
       ENVIRONMENT DIVISION.                                            
       CONFIGURATION SECTION.                                           
       SPECIAL-NAMES.                                                   
           DECIMAL-POINT IS COMMA.                                      
           EJECT                                                        
      ************************************************************      
      *   DATA DIVISION                                          *      
      ************************************************************      
       DATA DIVISION.                                                   
           SKIP1                                                        
      ************************************************************      
      *   WORKING-STORAGE SECTION                                *      
      ************************************************************      
       WORKING-STORAGE SECTION.                                         
      ************************************************************      
      *                     COSTANTI                             *      
      ************************************************************      
       01  FILLER  PIC X(34)                                            
                  VALUE 'PDCBVC - INIZIO WORKING STORAGE'.              
       01  FILLER.                                                      
      *                                                                 
           05   WABEND-CODE    PIC X(4).                                
           05   PROG-LIV0      PIC X(8) VALUE 'PDALIV0'.                
           05   PROG-LIV1      PIC X(8) VALUE 'PDCLIV1'.                
           05   PROG-LIV2      PIC X(8) VALUE 'PDCLV2'.                 
           05   PROG-LIV3      PIC X(8) VALUE 'PDCLIV3'.                
           05   PROG-LIV4      PIC X(8) VALUE 'PDCVC4'.                 
           05   PROG-LIV5      PIC X(8) VALUE 'PDCGVC'.                 
           05   WKMSG          PIC X(70).                               
           SKIP1                                                        
           05   KFINE-DATI     PIC X(25)                                
                  VALUE '** FINE DATI'.                                 
           05   KBROWSE        PIC X(25)                                
                  VALUE 'BROWSE NOMINATIVO'.                            
           05   WTASTOER       PIC X(70)                                
                  VALUE '** Tasto funzionale non gestito'.              
           05   WMSGNOREC      PIC X(70)                                
                  VALUE '** Non esistono voci contabili attive nella ses
      -        'sione specificata'.                                     
           SKIP1                                                        
           SKIP1                                                        
           05   WKERR1         PIC X(70)                                
                  VALUE '** Non esistono variazioni nella sessione speci
      -        'ficata'.                                                
           SKIP1                                                        
           SKIP1                                                        
           05   WKERR2         PIC X(70)                                
                  VALUE '** Non esistono variazioni della sessione corre
      -        'nte da correggere'.                                     
           SKIP1                                                        
           05   WMNOSEL        PIC X(70)                                
                  VALUE '** Nessuna scelta effettuata'.                 
           EJECT                                                        
      ************************************************************      
      *                     VARIABILI                            *      
      ************************************************************      
       01  FILLER.                                                      
           SKIP1                                                        
      *    03   LUNG               PIC S9(4) COMP VALUE +32000.         
           03   WCTRIG             PIC S9(3) COMP-3 VALUE +0.           
           03   WCTPAG             PIC S9(3) COMP-3 VALUE +0.           
           03   NPAGT              PIC S9(3) COMP-3 VALUE +0.           
           03   N-RIGHE            PIC S9(3) COMP-3 VALUE +0.           
           03   RESTO              PIC S9(3) COMP-3 VALUE +0.           
           03   COM11              PIC ZZZ.ZZZ.ZZ9.                     
           03   COM3               PIC ZZ9.                             
           03   COM2               PIC Z9.                              
           03   ASKIP-DRK          PIC X VALUE '%'.                     
           03   IND-RIGA           PIC 99.                              
           03   SW-FINE            PIC X.                               
           03   PD1VOCI-IND        PIC S9(3) COMP-3.                    
           03   MAX-RIGHE          PIC S9(3) COMP-3  VALUE +15.         
           03   WKOST              PIC S9(3) COMP-3  VALUE +0.          
           03   WW-DATE            PIC S9(18) COMP.                     
           EJECT                                                        
           03   NPAGINA.                                                
                05   NPG          PIC X(03).                            
                05   FILLER       PIC X VALUE '/'.                      
                05   NPGT         PIC X(02).                            
           SKIP1                                                        
           03   TESTATA.                                                
                05   TESTATA1     PIC X(22).                            
                05   FILLER       PIC X.                                
                05   TESTATA2     PIC X(25).                            
           SKIP1                                                        
           03   WDATA.                                                  
                05   WDATA-GG     PIC 99.                               
                05   FILLER       PIC X   VALUE '/'.                    
                05   WDATA-MM     PIC 99.                               
                05   FILLER       PIC X   VALUE '/'.                    
                05   WDATA-AA     PIC 99.                               
           SKIP1                                                        
           03   WANNO.                                                  
                05   WANNO12      PIC 99.                               
                05   WANNO34      PIC 99.                               
           SKIP1                                                        
           03   MATRICOLA.                                              
                05   CODICE       PIC X(5).                             
                05   PAD          PIC X.                                
           SKIP1                                                        
           03   WVOCE.                                                  
                05   FUNZ         PIC X.                                
                05   VOCE         PIC X(4).                             
           SKIP1                                                        
           05   ANNO-SESS.                                              
                10 ANNO-SESS12        PIC 99.                           
                10 ANNO-SESS34        PIC 99.                           
           SKIP1                                                        
           05   SESSIONE.                                               
                10 SESSIONE-ANNO      PIC 99.                           
                10 FILLER             PIC X  VALUE '/'.                 
                10 SESSIONE-MESE      PIC 99.                           
                10 FILLER             PIC X  VALUE ' '.                 
                10 SESSIONE-TMENS     PIC 9.                            
           SKIP1                                                        
           03   WDATE.                                                  
                05   WDATE-GG     PIC 99.                               
                05   FILLER       PIC X.                                
                05   WDATE-MM     PIC 99.                               
                05   FILLER       PIC X.                                
                05   WDATE-AA     PIC 99.                               
           SKIP1                                                        
           03   WDATE2.                                                 
                05   WDATE2-GG    PIC 99.                               
                05   WDATE2-MM    PIC 99.                               
                05   WDATE2-AAAA.                                       
                    07   WDATE2-AA12  PIC 99.                           
                    07   WDATE2-AA34  PIC 99.                           
           EJECT                                                        
       01  PDRTIP01-RECORD.                                             
           COPY PDRTIP01.                                               
           EJECT                                                        
       01  PDRVC-RECORD.                                                
           COPY PDRVC.                                                  
           EJECT                                                        
       01  WPD1VOCI.                                                    
           COPY PD1VOCI.                                                
           EJECT                                                        
       01  WPD1FS00.                                                    
           COPY PD1FS00.                                                
           EJECT                                                        
      *----------------------------------------------------------*      
      *   AREA COMUNICAZIONE ROUTINE CONTROLLI FORMALI                  
      *----------------------------------------------------------*      
       01  WPDRUTI01.                                                   
           COPY PDRUTI01.                                               
      *----------------------------------------------------------------*
      *    AREA DI COMUNICAZIONE PXRSEMAF: Gestione Semafori         
      *----------------------------------------------------------------*
           COPY PXCSEMAF.
       01  PXRSEMAF         PIC X(08) VALUE 'PXRSEMAF'.
      ****************************************************              
      *     AREA DI LAVORO PER PREPARAZIONE MAPPA        *              
      *               (LUNGHEZZA = 79)                   *              
      ****************************************************              
           SKIP1                                                        
       01  RIGA-MAPPA.                                                  
           05  WPROGR               PIC 9(2).                           
           05  FILLER               PIC X.                              
           05  WCODVO               PIC 9(5).                           
           05  FILLER               PIC X.                              
           05  WDESCVO              PIC X(37).                          
           SKIP1                                                        
           05  FILLER               PIC X.                              
           05  DATA-IMPIANTO        PIC X(8).                           
           05  FILLER               PIC X.                              
           05  DATA-CESSAZIONE      PIC X(8).                           
           05  FILLER               PIC X.                              
           05  IMPORTO-RATA         PIC X(11).                          
           05  FILLER               PIC X.                              
           05  WPROGREC             PIC 9(2).                           
           EJECT                                                        
      ************************************************************      
      *                       M A P P E                          *      
      ************************************************************      
           COPY PDCBVCM SUPPRESS.                                       
           COPY DFHBMSCA SUPPRESS.                                      
           COPY DFHAID SUPPRESS.                                        
           EJECT           
      *-----------------------------------------------------------*     
      *                   S Q L  A R E A
      *-----------------------------------------------------------*
           EXEC SQL INCLUDE SQLCA END-EXEC.
           EXEC SQL BEGIN DECLARE SECTION END-EXEC.
           EXEC SQL INCLUDE PDWSQLER END-EXEC
           EXEC SQL END DECLARE SECTION END-EXEC.             
      ************************************************************      
      *                    LINKAGE SECTION                       *      
      ************************************************************      
       LINKAGE SECTION.                                                 
      *01  DFHBLLDS.                                                    
      *    03   RESERVED-BLL      PIC S9(8) COMP.                       
      **   03   TWA-BLL           PIC S9(8) COMP.                       
           COPY PDRTWA2.                                                
           EJECT                                                        
      ************************************************************      
      *                   PROCEDURE DIVISION                     *      
      ************************************************************      
       PROCEDURE DIVISION.                                              
           PERFORM ADDRESS-TWA.   
           EXEC SQL WHENEVER SQLERROR GO TO ERRORE-SQL END-EXEC
           EXEC SQL SELECT SYSDATE INTO :HSQL-DATE FROM DUAL END-EXEC. 
           SKIP1                                                        
      **                                                                
           IF  TWCOB-FASE = '1' THEN                                    
               GO TO BROWSE-FASE1.                                      
           IF  TWCOB-FASE = '2' THEN                                    
               GO TO BROWSE-FASE2.                                      
      **                                                                
           MOVE  'BR00'  TO  WABEND-CODE                                
           GO  TO ABEND00.                                              
      **                                                                
           EJECT                                                        
      ************************************************************      
      *       INIZIO DEL BROWSE    FASE = 1                      *      
      ************************************************************      
       BROWSE-FASE1.                                                    
           MOVE LOW-VALUE TO PDCBVC1I.                                  
   
mar23 * Le funzioni di INSERIMENTO E AGGIORNAMENTO sulle voci contabili
      * non sono permesse se il semaforo "PDAGGVIP" � chiuso
      * (viene chiuso dall'elaborazione dei Collaboratori)
           IF (TWCOB-FUNZIONE =  'I' OR 'A' OR 'C' OR 'D' OR 'P')
           AND TWCOB-ID-SISTEMA = 'IP'
           THEN 
              PERFORM READ-TAB-SEMAF
      * Stati semaforo:
      * 1 = Chiuso 
      * 2 = Aperto 
              IF PXCSEMAF-STATUS = 1
              THEN                                                      
                  MOVE 'INSERIMENTO/AGGIORNAMENTO NON PERMESSI (ELAB. CO
      -               'LLABORATORI IN CORSO)'
                      TO TWCOB-AREA-MSG
                 GO  TO  XCTL-LIV4                  
              END-IF
           END-IF
                      
           PERFORM PREP-LINK-PD1FS00 THRU PREP-LINK-PD1FS00-EXIT.       
           PERFORM INIZ-PARAM        THRU INIZ-PARAM-EXIT.              
           PERFORM LINK-PD1VOCI      THRU LINK-PD1VOCI-EXIT.            
           PERFORM CALCOLA-NPAG      THRU CALCOLA-NPAG-EXIT.            
           SKIP1                                                        
           IF PD1VOCI-TABVOX-NUMERO  =  0    AND                        
               TWCOB-XCTL-PGM        =  'PDCGVC'  THEN                  
               MOVE  SPACES      TO  TWCOB-AREA-MSG                     
               GO  TO  XCTL-LIV4.                                       
      *------------------------------------------------------           
           MOVE WMSGNOREC   TO WKMSG.                                   
           IF TWCOB-VARCONT-NUMFUNZ = '1'                               
              THEN MOVE WKERR1  TO WKMSG.                               
           SKIP1                                                        
           IF TWCOB-FUNZIONE  = 'A'                                     
              THEN MOVE WKERR2  TO WKMSG.                               
           SKIP1                                                        
           IF PD1VOCI-TABVOX-NUMERO  =  0    THEN                       
               MOVE  WKMSG     TO  TWCOB-AREA-MSG                       
               GO  TO  XCTL-LIV4.                                       
      *                                                                 
           MOVE SPACE    TO WKMSG.                                      
                                                                        
           PERFORM  PREPARA-MAP   THRU PREPARA-MAP-EXIT.                
           MOVE     WCTPAG        TO   TWCOB-VARCONT-NPAGINA.           
           IF   WCTPAG     =      1  THEN                               
               MOVE  ASKIP-DRK     TO  M1PF7A                           
               MOVE  ASKIP-DRK     TO  M1PF8A.                          
           SKIP1                                                        
           IF    NPAGT     NOT GREATER    1  THEN                       
               MOVE  KFINE-DATI    TO  M1MSGO.                          
           SKIP1                                                        
           PERFORM  SEND-PDCBVC1.                                       
           MOVE  '2' TO  TWCOB-FASE.                                    
           MOVE SPACE  TO  TWCOB-XCTL.                                  
           GO TO RETURN-MAIN.                                           
           EJECT                                                        
      ************************************************************      
      *     VISUALIZZAZIONE BROWSE                               *      
      ************************************************************      
       BROWSE-FASE2.                                                    
           PERFORM  RECEIVE-PDCBVC1.                                    
           MOVE     TWCOB-VARCONT-NPAGINA  TO  WCTPAG.                  
           IF  EIBAID = DFHENTER THEN                                   
               GO TO BROWSE-FASE2-ENTER.                                
           IF  EIBAID = DFHPF1   THEN                                   
               GO TO XCTL-LIV1.                                         
           IF  EIBAID = DFHPF2   THEN                                   
               GO TO XCTL-LIV2.                                         
           IF  EIBAID = DFHPF3   THEN                                   
               GO TO XCTL-LIV3.                                         
           IF  EIBAID = DFHPF4   THEN                                   
               GO TO XCTL-LIV4.                                         
           IF  EIBAID = DFHPF9   THEN                                   
               GO TO XCTL-LIV0.                                         
           IF  EIBAID = DFHPF7   THEN                                   
               GO TO BROWSE-FASE2-PF7.                                  
           IF  EIBAID = DFHPF8   THEN                                   
               GO TO BROWSE-FASE2-PF8.                                  
           GO TO BROWSE-FASE2-TASTOER.                                  
           SKIP1                                                        
       BROWSE-FASE2-ENTER.                                              
           IF SCELTAI   NOT  =  '__'   AND                              
              SCELTAI   NOT  =  SPACES                                  
              THEN GO TO BROWSE-FASE2-SEL.                              
           SKIP1                                                        
           PERFORM PREP-LINK-PD1FS00 THRU PREP-LINK-PD1FS00-EXIT.       
           PERFORM INIZ-PARAM        THRU INIZ-PARAM-EXIT.              
           PERFORM LINK-PD1VOCI      THRU LINK-PD1VOCI-EXIT.            
           PERFORM CALCOLA-NPAG      THRU CALCOLA-NPAG-EXIT.            
           IF  WCTPAG NOT LESS  NPAGT  THEN                             
              GO TO XCTL-LIV4.                                          
           SKIP1                                                        
           GO TO BROWSE-FASE2-VISUAL.                                   
           EJECT                                                        
       BROWSE-FASE2-PF7.                                                
           IF    WCTPAG   NOT GREATER  1  THEN                          
               GO TO BROWSE-FASE2-TASTOER.                              
           SUBTRACT   2  FROM  WCTPAG.                                  
           GO TO BROWSE-FASE2-ENTER.                                    
           SKIP1                                                        
       BROWSE-FASE2-PF8.                                                
           IF    WCTPAG   =   1  THEN                                   
               GO TO BROWSE-FASE2-TASTOER.                              
           MOVE  ZERO  TO  WCTPAG.                                      
           GO TO BROWSE-FASE2-ENTER.                                    
           SKIP1                                                        
       BROWSE-FASE2-TASTOER.                                            
           MOVE  -1  TO M1MSGL.                                         
           MOVE  WTASTOER     TO M1MSGO.                                
           PERFORM  SEND-PDCBVC1-DO.                                    
           GO TO RETURN-MAIN.                                           
           SKIP1                                                        
       BROWSE-FASE2-NOSEL.                                              
           MOVE  -1  TO SCELTAL.                                        
           MOVE  WMNOSEL      TO M1MSGO.                                
           PERFORM  SEND-PDCBVC1-DO.                                    
           GO TO RETURN-MAIN.                                           
           EJECT                                                        
       BROWSE-FASE2-SEL.                                                
           MOVE  1   TO  WCTRIG.                                        
           SKIP1                                                        
       BROWSE-FASE2-SEL-10.                                             
           IF WCTRIG  GREATER  15  THEN                                 
              GO TO BROWSE-FASE2-NOTFND.                                
           MOVE  MRIGAO(WCTRIG)  TO  RIGA-MAPPA.                        
           SKIP1                                                        
           IF SCELTAI  =  WPROGR   THEN                                 
              MOVE  WCODVO      TO   WVOCE                              
              MOVE  VOCE        TO   TWCOB-VARCONT-VOCE                 
              MOVE  WPROGREC    TO   TWCOB-VARCONT-PROGVOCE             
              GO TO BROWSE-FASE2-SEL-20.                                
           SKIP1                                                        
           ADD   1   TO  WCTRIG.                                        
           GO TO BROWSE-FASE2-SEL-10.                                   
           SKIP1                                                        
       BROWSE-FASE2-SEL-20.                                             
           GO  TO  XCTL-LIV5.                                           
           SKIP1                                                        
       BROWSE-FASE2-NOTFND.                                             
           MOVE  -1  TO  SCELTAL.                                       
           MOVE  'Progressivo digitato non presente'  TO M1MSGO.        
           PERFORM  SEND-PDCBVC1-DO.                                    
           GO TO RETURN-MAIN.                                           
           SKIP1                                                        
       BROWSE-FASE2-VISUAL.                                             
           PERFORM  PREPARA-MAP   THRU PREPARA-MAP-EXIT.                
           MOVE     WCTPAG        TO   TWCOB-VARCONT-NPAGINA.           
           IF     WCTPAG   =    1     THEN                              
               MOVE  ASKIP-DRK     TO  M1PF8A                           
               MOVE  ASKIP-DRK     TO  M1PF7A.                          
           IF     SW-FINE    =    '1'        THEN                       
               MOVE  KFINE-DATI    TO  M1MSGO.                          
           PERFORM  SEND-PDCBVC1.                                       
           MOVE  '2' TO  TWCOB-FASE.                                    
           GO TO RETURN-MAIN.                                           
           EJECT                                                        
      ************************************************************      
      *   CALCOLO DEL NUMERO DI PAGINE DA VISUALIZZARE                  
      ************************************************************      
       CALCOLA-NPAG.                                                    
      *                                                                 
           DIVIDE MAX-RIGHE INTO PD1VOCI-TABVOX-NUMERO GIVING NPAGT     
           REMAINDER  RESTO.                                            
           IF  NPAGT  LESS  1   THEN  ADD +1  TO  NPAGT                 
               GO  TO  CALCOLA-NPAG-EXIT.                               
           IF  RESTO  GREATER  ZERO  THEN ADD  +1  TO  NPAGT.           
      *                                                                 
       CALCOLA-NPAG-EXIT.                                               
           EXIT.                                                        
           SKIP2                                                        
      ************************************************************      
      *   PREPARAZIONE LINK PD1FS00                                     
      ************************************************************      
       PREP-LINK-PD1FS00.                                               
           MOVE  '03'        TO   PD1FS00-FUNZIONE.                     
           MOVE  TWCOB-ID-SISTEMA TO  PD1FS00-SESS-SISTEMA.             
           PERFORM LINK-PD1FS00 THRU LINK-PD1FS00-EXIT.                 
           SKIP1                                                        
           IF PD1FS00-RETURN   = '0'                                    
              GO TO PREP-LINK-PD1FS00-EXIT.                             
           IF PD1FS00-RETURN   = '2'                                    
              GO TO PREP-LINK-PD1FS00-EXIT.                             
           MOVE 'VC04'  TO  WABEND-CODE.                                
           GO  TO ABEND00.                                              
       PREP-LINK-PD1FS00-EXIT.                                          
           EXIT.                                                        
           EJECT                                                        
      ************************************************************      
      *   PREPARAZIONE DEI PARAMETRI PER PD1VOCI                        
      ************************************************************      
       INIZ-PARAM.                                                      
           MOVE SPACE                  TO  PD1VOCI-DATI.                
           MOVE TWCOB-VARCONT-VOCE-LIV4 TO  PD1VOCI-COD-VOCE.           
           MOVE TWCOB-TIPO-DIP         TO  PD1VOCI-CODDIP-TIPO.         
           MOVE TWCOB-SP-MATR          TO  PD1VOCI-CODDIP-MATR.         
           MOVE TWCOB-SP-PAD           TO  PD1VOCI-CODDIP-PAD.          
           MOVE TWCOB-FUNZIONE         TO  PD1VOCI-TIPO-VARIAZ.         
      ***  MOVE   '20'                 TO  PD1VOCI-TIPO-GEST.           
           MOVE   '00'                 TO  PD1VOCI-TIPO-GEST.           
           SKIP1                                                        
           IF  TWCOB-VARCONT-NUMFUNZ   =   '1'   THEN                   
               MOVE  '11'         TO  PD1VOCI-FUNZIONE                  
               GO  TO  INIZ-PARAM-010.                                  
           SKIP1                                                        
           IF  TWCOB-VARCONT-NUMFUNZ   =   '6'   THEN                   
               MOVE  '12'         TO  PD1VOCI-FUNZIONE                  
               GO  TO  INIZ-PARAM-010.                                  
           SKIP1                                                        
           IF  TWCOB-FUNZIONE      =   'I'   THEN                       
               MOVE  '02'         TO  PD1VOCI-FUNZIONE                  
               MOVE   'A'         TO  PD1VOCI-TIPO-ESTRA                
               GO  TO  INIZ-PARAM-010.                                  
           SKIP1                                                        
           MOVE  '11'         TO  PD1VOCI-FUNZIONE.                     
           SKIP1                                                        
       INIZ-PARAM-010.                                                  
      *-----------------------------------------------------            
      *  IMPOSTA IL TIPO VOCE DA ESTRARRE                               
      *-----------------------------------------------------            
           IF  TWCOB-VARCONT-NUMFUNZ   =   '2'   THEN                   
               MOVE  '1'         TO  PD1VOCI-TIPO-VOCE                  
               GO  TO  INIZ-PARAM-020.                                  
           IF  TWCOB-VARCONT-NUMFUNZ   =   '3'   THEN                   
               MOVE  '3'         TO  PD1VOCI-TIPO-VOCE                  
               GO  TO  INIZ-PARAM-020.                                  
           IF  TWCOB-VARCONT-NUMFUNZ   =   '4'   THEN                   
               MOVE  '2'         TO  PD1VOCI-TIPO-VOCE                  
               GO  TO  INIZ-PARAM-020.                                  
           IF  TWCOB-VARCONT-NUMFUNZ   =   '5'   THEN                   
               MOVE  '4'         TO  PD1VOCI-TIPO-VOCE                  
               GO  TO  INIZ-PARAM-020.                                  
           MOVE  '0'         TO  PD1VOCI-TIPO-VOCE.                     
           SKIP1                                                        
       INIZ-PARAM-020.                                                  
           IF    TWCOB-VARCONT-ANNO   =      'TTTT'  THEN               
               MOVE  'TTTT'           TO  PD1VOCI-LIQUID1-ANNO          
           ELSE                                                         
               MOVE  TWCOB-VARCONT-ANNO   TO  PD1VOCI-LIQUID1-ANNO.     
           SKIP1                                                        
           MOVE  TWCOB-VARCONT-MESE   TO  PD1VOCI-LIQUID1-MESE.         
           MOVE  TWCOB-VARCONT-TMENS  TO  PD1VOCI-LIQUID1-TIPO.         
       INIZ-PARAM-EXIT.                                                 
           EXIT.                                                        
           EJECT                                                        
      ************************************************************      
      *   LINK ALLA ROUTINE VOCI CONTABILI   (PD1VOCI)                  
      ************************************************************      
       LINK-PD1VOCI.                                                    
           MOVE HIGH-VALUE TO  PD1VOCI-RETURN.                          
           SKIP1                                                        
           EXEC CICS LINK PROGRAM('PD1VOCI') COMMAREA(WPD1VOCI)         
               LENGTH(32000) END-EXEC.                                  
           SKIP1                                                        
           IF  PD1VOCI-RETURN EQUAL 'E'                                 
             THEN MOVE  'LE10'  TO  WABEND-CODE                         
                  GO TO ABEND00.                                        
           SKIP1                                                        
       LINK-PD1VOCI-EXIT.                                               
           EXIT.                                                        
           EJECT                                                        
      ************************************************************      
      *   LINK ALLA ROUTINE PER FUNZIONI DI SERVIZIO (PD1FS00)   *      
      ************************************************************      
       LINK-PD1FS00.                                                    
           EXEC CICS LINK PROGRAM('PD1FS00') COMMAREA(WPD1FS00)         
               LENGTH(PD1FS00-LUNGH) END-EXEC.                          
           SKIP1                                                        
           IF  PD1FS00-RETURN  EQUAL 'E' THEN                           
               MOVE 'FS00'  TO  WABEND-CODE                             
               GO TO ABEND00.                                           
           SKIP1                                                        
       LINK-PD1FS00-EXIT.                                               
           EXIT.                                                        
           SKIP1                                                        
      ************************************************************      
      *                PREPARAZIONE MAPPA                        *      
      ************************************************************      
       PREPARA-MAP.                                                     
           PERFORM  MUOVI-TESTATA THRU MUOVI-TESTATA-EXIT.              
           PERFORM  ABBL-RIGA  THRU  ABBL-RIGA-EXIT.                    
           PERFORM  MUOVI-DATI THRU  MUOVI-DATI-EXIT.                   
           SKIP1                                                        
      *-----------------------------------------------------------      
      *  IL CAMPO SULLA MAPPA PER LA SCELTA (SCELTAO) VIENE             
      *   IMPOSTATO A '01' NEL SEGUENTE CASO:                           
      *     - SI PROVIENE DAL LIVELLO 4 (TWCOB-XCTL = SPACE)            
      *     - ESISTE UNA SOLA RIGA VISULAIZZATA SULLA MAPPA(WCTRIG = 2) 
      *     - NEL LIVELLO 4 E' STATA SCELTA LA VOCE (VARCONT-VOCE-LIV4) 
      *-----------------------------------------------------------      
           IF WCTRIG NOT GREATER 2  AND                                 
              TWCOB-XCTL   = SPACE               AND                    
              TWCOB-VARCONT-VOCE-LIV4  NUMERIC   AND                    
              TWCOB-VARCONT-VOCE-LIV4  NOT = ZERO                       
             THEN MOVE '01'  TO SCELTAO.                                
           SKIP1                                                        
           MOVE  -1         TO  SCELTAL.                                
           SKIP1                                                        
       PREPARA-MAP-EXIT.                                                
           EXIT.                                                        
           EJECT                                                        
      ************************************************************      
      *    IMPOSTAZIONE TESTATA DELLA MAPPA                      *      
      ************************************************************      
       MUOVI-TESTATA.                                                   
           MOVE TWCOB-COGNOME      TO MCOGO.                            
           MOVE TWCOB-NOME         TO MNOMO.                            
           MOVE TWCOB-CODICE-DIP   TO MMATRO.                           
       MUOVI-TESTATA-00.                                                
           MOVE TWCOB-NOME-CICS TO M0AMBO.                              
      ***  ACCEPT  WDATE           FROM DATE.                           
      *                                                                 
           EXEC CICS ASKTIME  ABSTIME(WW-DATE)   END-EXEC.              
           EXEC CICS FORMATTIME  ABSTIME(WW-DATE)  DDMMYY(WDATE)        
                     DATESEP  END-EXEC.                                 
      *                                                                 
           MOVE  WDATE-GG          TO  WDATA-GG.                        
           MOVE  WDATE-MM          TO  WDATA-MM.                        
           MOVE  WDATE-AA          TO  WDATA-AA.                        
           MOVE  WDATA             TO  M1DATAO.                         
      *                                                                 
           MOVE  TWCOB-ID-SISTEMA  TO  M1SYSO.                          
      *                                                                 
           MOVE  PD1FS00-SESS-ANNO   TO   ANNO-SESS.                    
           MOVE  ANNO-SESS34         TO   SESSIONE-ANNO.                
           MOVE  PD1FS00-SESS-MESE   TO   SESSIONE-MESE.                
           MOVE  PD1FS00-SESS-TMENS  TO   SESSIONE-TMENS.               
           MOVE  SESSIONE            TO   MSESSIO.                      
           SKIP1                                                        
           IF    PD1FS00-SESS-FLAG  =  '1'  THEN                        
               MOVE  'Aperta'           TO   MDSESSO                    
               GO  TO  MUOVI-TESTATA-10.                                
           IF    PD1FS00-SESS-FLAG  =  '2'  THEN                        
               MOVE  'Chiusa'           TO   MDSESSO                    
               GO  TO  MUOVI-TESTATA-10.                                
           IF    PD1FS00-SESS-FLAG  =  '3'  THEN                        
               MOVE  'Liquidata'        TO   MDSESSO.                   
           SKIP1                                                        
       MUOVI-TESTATA-10.                                                
      *                                                                 
           IF    TWCOB-FUNZIONE  =  'I'  THEN                           
               MOVE  '              IMPIANTO' TO  TESTATA1              
               GO  TO  MUOVI-TESTATA-20.                                
      *                                                                 
           IF    TWCOB-FUNZIONE  =  'V'  THEN                           
               MOVE  '       VISUALIZZAZIONE' TO  TESTATA1              
               GO  TO  MUOVI-TESTATA-20.                                
      *                                                                 
           IF    TWCOB-FUNZIONE  =  'C'  THEN                           
               MOVE  '            CESSAZIONE' TO  TESTATA1              
               GO  TO  MUOVI-TESTATA-20.                                
      *                                                                 
           IF    TWCOB-FUNZIONE  =  'A'  THEN                           
               MOVE  '         AGGIORNAMENTO' TO  TESTATA1              
               GO  TO  MUOVI-TESTATA-20.                                
      *                                                                 
           IF    TWCOB-FUNZIONE  =  'D'  THEN                           
               MOVE  '   MODIFICA DECORRENZA' TO  TESTATA1              
               GO  TO  MUOVI-TESTATA-20.                                
      *                                                                 
           IF    TWCOB-FUNZIONE  =  'P'  THEN                           
               MOVE  'MODIFICA PROVVEDIMENTO' TO  TESTATA1.             
       MUOVI-TESTATA-20.                                                
           IF    TWCOB-VARCONT-NUMFUNZ  =  '1'  THEN                    
               MOVE  'COMPETENZE E RITENUTE' TO  TESTATA2               
               GO  TO  MUOVI-TESTATA-30.                                
      *                                                                 
           IF    TWCOB-VARCONT-NUMFUNZ  =  '2'  THEN                    
               MOVE  'COMPETENZE IMPONIBILI' TO  TESTATA2               
               GO  TO  MUOVI-TESTATA-30.                                
      *                                                                 
           IF    TWCOB-VARCONT-NUMFUNZ  =  '3'  THEN                    
               MOVE  'COMPETENZE NON IMPONIBILI' TO  TESTATA2           
               GO  TO  MUOVI-TESTATA-30.                                
      *                                                                 
           IF    TWCOB-VARCONT-NUMFUNZ  =  '4'  THEN                    
               MOVE  'RITENUTE PREVIDENZIALI' TO  TESTATA2              
               GO  TO  MUOVI-TESTATA-30.                                
      *                                                                 
           IF    TWCOB-VARCONT-NUMFUNZ  =  '5'  THEN                    
               MOVE  'RITENUTE VARIE' TO  TESTATA2                      
               GO  TO  MUOVI-TESTATA-30.                                
      *                                                                 
           IF    TWCOB-VARCONT-NUMFUNZ  =  '6'  THEN                    
               MOVE  'VARIAZIONI MENSILI' TO  TESTATA2.                 
      *                                                                 
       MUOVI-TESTATA-30.                                                
      *                                                                 
           MOVE  TESTATA              TO  MDESCO.                       
      *                                                                 
       MUOVI-TESTATA-EXIT.                                              
           EXIT.                                                        
           EJECT                                                        
      ************************************************************      
      *     TRASFERIMENTO DATI SULLA MAPPA                       *      
      ************************************************************      
       MUOVI-DATI.                                                      
           PERFORM ABBL-RIGA  THRU  ABBL-RIGA-EXIT.                     
           MOVE   1        TO  WCTRIG.                                  
           MOVE  '0'       TO  SW-FINE.                                 
           SKIP1                                                        
      *------------------------------------------------------------     
      *------- BROWSE CHIAMATO  DA  PDCGVC -  FASE1 E FASE2             
      *------------------------------------------------------------     
           IF  TWCOB-XCTL-PGM   =  'PDCGVC'  AND                        
               TWCOB-FASE  =  '1'            THEN                       
               MOVE TWCOB-VARCONT-NPAGINA  TO  WCTPAG                   
      ****     MOVE SPACES                 TO  TWCOB-XCTL-PGM           
               SUBTRACT   1    FROM      WCTPAG                         
               MULTIPLY MAX-RIGHE BY WCTPAG GIVING N-RIGHE              
               MULTIPLY MAX-RIGHE BY WCTPAG GIVING WKOST                
               ADD  +1  TO  N-RIGHE                                     
               ADD  +1  TO   WCTPAG                                     
               MOVE  N-RIGHE  TO  PD1VOCI-IND                           
               GO  TO  MUOVI-DATI-10.                                   
           SKIP1                                                        
           IF  TWCOB-XCTL-PGM   =  'PDCGVC'  AND                        
               TWCOB-FASE  =  '2'            THEN                       
               MOVE TWCOB-VARCONT-NPAGINA  TO  WCTPAG                   
               MULTIPLY MAX-RIGHE BY WCTPAG GIVING N-RIGHE              
               MULTIPLY MAX-RIGHE BY WCTPAG GIVING WKOST                
               ADD  +1  TO  N-RIGHE                                     
               ADD  +1  TO   WCTPAG                                     
               MOVE  N-RIGHE  TO  PD1VOCI-IND                           
               GO  TO  MUOVI-DATI-10.                                   
      *------------------------------------------------------------     
      *------- BROWSE DAL  PROGRAMMA  DI  LIVELLO (PDCVC4)              
      *------------------------------------------------------------     
           IF  TWCOB-FASE  =  '1'  THEN                                 
               MOVE +1  TO   WCTPAG                                     
               MULTIPLY MAX-RIGHE BY WCTPAG GIVING WKOST.               
           MULTIPLY MAX-RIGHE BY WCTPAG GIVING N-RIGHE.                 
           IF  TWCOB-FASE  =  '2'  THEN                                 
               ADD  +1  TO  N-RIGHE                                     
               MOVE  N-RIGHE  TO  PD1VOCI-IND                           
               ADD  +1  TO   WCTPAG                                     
               MULTIPLY MAX-RIGHE BY WCTPAG GIVING WKOST                
               GO  TO  MUOVI-DATI-10.                                   
       MUOVI-DATI-05.                                                   
           MOVE  +1  TO  PD1VOCI-IND.                                   
       MUOVI-DATI-10.                                                   
           IF  PD1VOCI-IND  GREATER  PD1VOCI-TABVOX-NUMERO THEN         
               MOVE  '1'   TO   SW-FINE                                 
               GO  TO  MUOVI-DATI-30.                                   
           IF  WCTRIG  GREATER      15   THEN                           
               GO  TO  MUOVI-DATI-30.                                   
       MUOVI-DATI-15.                                                   
           PERFORM PREP-RIGA THRU PREP-RIGA-EXIT.                       
           SKIP1                                                        
       MUOVI-DATI-20.                                                   
           ADD  +1  TO   PD1VOCI-IND.                                   
           GO    TO  MUOVI-DATI-10.                                     
           SKIP1                                                        
       MUOVI-DATI-30.                                                   
           MOVE  WCTPAG   TO  COM3.                                     
           MOVE  COM3     TO  NPG.                                      
           MOVE  NPAGT    TO  COM2.                                     
           MOVE  COM2     TO  NPGT.                                     
           MOVE  NPAGINA  TO  MNPAGO.                                   
       MUOVI-DATI-EXIT.                                                 
           EXIT.                                                        
           EJECT                                                        
      ************************************************************      
      *    PREPARA RIGA MAPPA                                           
      ************************************************************      
       PREP-RIGA.                                                       
           MOVE SPACES                 TO  RIGA-MAPPA.                  
           MOVE WCTRIG                 TO  WPROGR.                      
           MOVE PD1VOCI-TABVOX-CODVOX(PD1VOCI-IND)  TO  VOCE.           
           IF   TWCOB-FUNZIONE     =   'I'   THEN                       
                MOVE SPACES  TO  FUNZ                                   
           ELSE                                                         
                MOVE PD1VOCI-TABVOX-TIPVAR(PD1VOCI-IND)  TO  FUNZ.      
           MOVE WVOCE                               TO  WCODVO.         
           MOVE PD1VOCI-TABVOX-DESCRIZ(PD1VOCI-IND) TO  WDESCVO.        
           IF   TWCOB-FUNZIONE     =   'I'   THEN                       
                GO  TO   PREP-RIGA-010.                                 
           MOVE PD1VOCI-TABVOX-INIZ(PD1VOCI-IND)    TO  WDATE2.         
           MOVE WDATE2-AA34            TO  WDATA-AA.                    
           MOVE WDATE2-MM              TO  WDATA-MM.                    
           MOVE WDATE2-GG              TO  WDATA-GG.                    
           MOVE WDATA                  TO  DATA-IMPIANTO.               
           SKIP1                                                        
      **   MOVE PD1VOCI-TABVOX-AA34(PD1VOCI-IND)                        
      **                      TO SESSIONE-VARIAZ-AA34.                  
      **   MOVE '/'        TO SESSIONE-VARIAZ-B1.                       
      **   MOVE PD1VOCI-TABVOX-MESE(PD1VOCI-IND)                        
      **                      TO SESSIONE-VARIAZ-MM.                    
           SKIP1                                                        
           IF   PD1VOCI-TABVOX-FINE(PD1VOCI-IND)  =  SPACES THEN        
                MOVE     '   -    '    TO  DATA-CESSAZIONE              
           ELSE                                                         
               MOVE PD1VOCI-TABVOX-FINE(PD1VOCI-IND)    TO  WDATE2      
               MOVE WDATE2-AA34            TO  WDATA-AA                 
               MOVE WDATE2-MM              TO  WDATA-MM                 
               MOVE WDATE2-GG              TO  WDATA-GG                 
               MOVE WDATA                  TO  DATA-CESSAZIONE.         
           MOVE '05'       TO  PDRUTI01-FUNZIONE.                       
           MOVE PD1VOCI-TABVOX-IRATA(PD1VOCI-IND)                       
                                           TO  PDRUTI01-F05-VALORE.     
           PERFORM  LINK-PD0UTI01  THRU LINK-PD0UTI01-EXIT.             
           MOVE  PDRUTI01-F05-IMPOX11      TO  IMPORTO-RATA.            
           MOVE PD1VOCI-TABVOX-PROGVOX(PD1VOCI-IND) TO  WPROGREC.       
       PREP-RIGA-010.                                                   
           MOVE RIGA-MAPPA             TO  MRIGAO(WCTRIG).              
           ADD   +1  TO     WCTRIG.                                     
       PREP-RIGA-EXIT.                                                  
           EXIT.                                                        
           EJECT                    

      ************************************************************      
mar23 *  LETTURA STATO SEMAFORO SU TABELLA ORACLE ORAMF.SEMAFORO
      ************************************************************ 
       READ-TAB-SEMAF.

           INITIALIZE PXCSEMAF-AREA
           
           MOVE 'GET'            TO PXCSEMAF-REQ
           MOVE 'PDAGGVIP'       TO PXCSEMAF-NAME           
      * in realt� questi a seguire non servono per la lettura     
           MOVE 'SEMAFORO'       TO PXCSEMAF-AGENT
           MOVE 'PDCBVC'         TO PXCSEMAF-CALLER
           MOVE 'CICS'           TO PXCSEMAF-CALLER-TYPE
           MOVE TWCOB-OPER-SIGLA TO PXCSEMAF-USER-REQ

           CALL PXRSEMAF USING PXCSEMAF-AREA

           IF PXCSEMAF-OUTCOME NOT = SPACE
           THEN
              MOVE 'GET1'   TO WABEND-CODE
              PERFORM ABEND00  
           END-IF.
           .                                            
           EXIT.
      ************************************************************      
      *   LINK ALLA ROUTINE CONTROLLO IMPORTO                           
      ************************************************************      
       LINK-PD0UTI01.                                                   
           MOVE HIGH-VALUE TO  PDRUTI01-RETURN.                         
                                                                        
           EXEC CICS LINK PROGRAM('PD0UTI01') COMMAREA(WPDRUTI01)       
               LENGTH(400) END-EXEC.                                    
                                                                        
           IF  PDRUTI01-RETURN EQUAL 'E'                                
             THEN  MOVE 'UT01'   TO WABEND-CODE
                   GO TO ABEND00.             
                                                                        
           IF  PDRUTI01-FUNZIONE = '04' OR '05'                         
             INSPECT PDRUTI01-F04-IMPOX11 CONVERTING ' ' TO '_'         
           END-IF.                                                      
                                                                        
       LINK-PD0UTI01-EXIT.                                              
           EXIT.                                                        
                                                                        
      ************************************************************      
      *     ABBLENCAMENTO DELLA RIGA DELLA MAPPA                 *      
      ************************************************************      
       ABBL-RIGA.                                                       
           MOVE   1    TO  WCTRIG.                                      
       ABBL-RIGA-10.                                                    
           MOVE  SPACE  TO   MRIGAO(WCTRIG).                            
           ADD    1     TO  WCTRIG.                                     
           IF  WCTRIG NOT  GREATER MAX-RIGHE GO TO ABBL-RIGA-10.        
       ABBL-RIGA-EXIT.                                                  
           SKIP2                                                        
      ************************************************************      
      *                  INDIRIZZA TWA                           *      
      ************************************************************      
       ADDRESS-TWA.                                                     
      ***  EXEC CICS ADDRESS TWA(TWA-BLL) END-EXEC.                     
           EXEC CICS ADDRESS TWA(ADDRESS OF PDRTWA2) END-EXEC.          
           EJECT                                                        
      ************************************************************      
      *              INVIO MAPPA  PDCBVC1                        *      
      ************************************************************      
       SEND-PDCBVC1.                                                    
           EXEC CICS SEND MAP('PDCBVC1') MAPSET('PDCBVCM') ERASE        
               CURSOR END-EXEC.                                         
       SEND-PDCBVC1-EXIT.                                               
           EXIT.                                                        
           SKIP2                                                        
      ************************************************************      
      *          INVIO MAPPA  PDCBVC1 (DATA ONLY)                *      
      ************************************************************      
       SEND-PDCBVC1-DO.                                                 
           EXEC CICS SEND MAP('PDCBVC1') MAPSET('PDCBVCM') CURSOR       
               DATAONLY END-EXEC.                                       
       SEND-PDCBVC1-DO-EXIT.                                            
           EXIT.                                                        
           SKIP2                                                        
      ************************************************************      
      *              LETTURA MAPPA PDCBVC1                       *      
      ************************************************************      
       RECEIVE-PDCBVC1.                                                 
           EXEC CICS RECEIVE MAP('PDCBVC1') MAPSET('PDCBVCM')  END-EXEC.
       RECEIVE-PDCBVC1-EXIT.                                            
           EXIT.                                                        
           EJECT                                                        
      ************************************************************      
      *              RESET  DELLA  TWA                           *      
      ************************************************************      
       RESET-TWA.                                                       
           MOVE  SPACES  TO  TWCOB-BROWSE.                              
           MOVE  '0'     TO  TWCOB-BRO-STATO.                           
       RESET-TWA-EXIT.                                                  
           EXIT.                                                        
           SKIP2                                                        
       XCTL-MAIN.                                                       
      *    PERFORM DELETE-TS THRU DELETE-TS-EXIT.                       
           SKIP1                                                        
           EXEC CICS XCTL PROGRAM('PDPRED') END-EXEC.                   
           SKIP1                                                        
       XCTL-LIV1.                                                       
           MOVE '1' TO TWCOB-FASE.                                      
           MOVE '1' TO TWCOB-FUNZIONE.                                  
           MOVE PROG-LIV1  TO  TWCOB-NOME-PGM.                          
           PERFORM RESET-TWA  THRU  RESET-TWA-EXIT.                     
           GO TO XCTL-MAIN.                                             
           SKIP1                                                        
       XCTL-LIV2.                                                       
           MOVE '1' TO TWCOB-FASE.                                      
           MOVE '1' TO TWCOB-FUNZIONE.                                  
           MOVE PROG-LIV2  TO  TWCOB-NOME-PGM.  
LUG25      MOVE SPACES      TO TWCOB-VARCONT-VOCE
           PERFORM RESET-TWA  THRU  RESET-TWA-EXIT.                     
           GO TO XCTL-MAIN.                                             
           SKIP1                                                        
       XCTL-LIV3.                                                       
           MOVE '1' TO TWCOB-FASE.                                      
           MOVE '1' TO TWCOB-FUNZIONE.                                  
           MOVE PROG-LIV3  TO  TWCOB-NOME-PGM.                          
           PERFORM RESET-TWA  THRU  RESET-TWA-EXIT.                     
           GO TO XCTL-MAIN.                                             
           SKIP1                                                        
       XCTL-LIV4.                                                       
           MOVE '1' TO TWCOB-FASE.                                      
           MOVE '1' TO TWCOB-FUNZIONE.                                  
           MOVE PROG-LIV4  TO  TWCOB-NOME-PGM.
LUG25      MOVE SPACES     TO TWCOB-VARCONT-VOCE
           PERFORM RESET-TWA  THRU  RESET-TWA-EXIT.                     
           GO TO XCTL-MAIN.                                             
           SKIP1                                                        
       XCTL-LIV5.                                                       
           MOVE '1' TO TWCOB-FASE.                                      
      *    MOVE 'P' TO TWCOB-FUNZIONE.                                  
           MOVE PROG-LIV5  TO  TWCOB-NOME-PGM.                          
           PERFORM RESET-TWA  THRU  RESET-TWA-EXIT.                     
           GO TO XCTL-MAIN.                                             
           SKIP1                                                        
       XCTL-LIV0.                                                       
           MOVE '1' TO TWCOB-FASE.                                      
           MOVE '1' TO TWCOB-FUNZIONE.                                  
           MOVE PROG-LIV0  TO  TWCOB-NOME-PGM.                          
           PERFORM RESET-TWA  THRU  RESET-TWA-EXIT.                     
           GO TO XCTL-MAIN.                                             
           SKIP1                                                        
           EJECT                                                        
       RETURN-MAIN.                                                     
           PERFORM SAVE-TWA.  
           EXEC CICS SYNCPOINT END-EXEC             
           EXEC CICS RETURN TRANSID ('PRED') END-EXEC.                  
           SKIP1                                                        
       RETURN-CICS.     
           EXEC CICS SYNCPOINT END-EXEC         
           EXEC CICS RETURN  END-EXEC.                                  
           SKIP1                                                        
       ABEND00.                                                         
           COPY PDIABEND.
           EXEC SQL INCLUDE PDPSQLER END-EXEC.            
           SKIP1                                                        
      ************************************************************      
      *             SALVATAGGIO TWA COMUNE                       *      
      ************************************************************      
       SAVE-TWA.                                                        
           COPY PDSAVTW2.                                               
           SKIP2                                                        
       FINE-ELABORAZIONE.                                               
           STOP RUN.                                                    
