      ************************************************************      
      *                                                          *      
      *  PDB305: BROWSE RIMBORSI TELEFONINI                             
      *                                                          *      
      *                                                          *      
      *                                                          *      
      *                                                          *      
      ************************************************************      
           SKIP2                                                        
      ************************************************************      
      *                                                          *      
      *   IDENTIFICATION DIVISION                                *      
      ************************************************************      
       IDENTIFICATION DIVISION.                                         
       PROGRAM-ID. PDB305.                                              
       AUTHOR. GIORGETTI.                                               
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
                  VALUE 'PDB305 - INIZIO WORKING STORAGE'.              
       01  FILLER.                                                      
           05   WABEND-CODE    PIC X(4).                                
           05   PROG-PF1       PIC X(8) VALUE 'PDBLIV1'.                
           05   PROG-PF2       PIC X(8) VALUE 'PDB306'.                 
           05   PROG-PF9       PIC X(8) VALUE 'PDALIV0'.                
           SKIP1                                                        
           05   WTASTOER       PIC X(70)                                
                  VALUE '** Tasto funzionale non gestito'.              
           05   WMESS01        PIC X(70)                                
                  VALUE '** Record anagrafico non trovato'.             
           05   WMESS05        PIC X(70)                                
                  VALUE '** Record afm non trovato'.                    
           05   WNOTROV        PIC X(70)                                
                  VALUE '** Coda non trovata'.                          
           05   WINES          PIC X(70)                                
                  VALUE '** Elemento inesistente o fine coda'.          
           05   WERRORE        PIC X(70)                                
                  VALUE '** Situazione di errore grave'.                
           SKIP1                                                        
           05   WLUNG-PDKTELR  PIC S9(4) COMP  VALUE +250.              
           05   WLUNG          PIC S9(4) COMP.                          
           SKIP1                                                        
      *    05   WIMPO9         PIC S9(9) COMP-3.                        
           05   WIMP11         PIC S9(11) COMP-3.                       
      *    05   WMASK11        PIC ZZZ.ZZZ.ZZ9.                         
           SKIP1                                                        
           05   NUMERO-REC     PIC S9(3) VALUE +0.                      
           SKIP1                                                        
      *  LUNGHEZZA RECORD AL01                                          
           05   WLUNG-PDRAL01  PIC S9(4) COMP  VALUE +500.              
           SKIP1                                                        
           SKIP1                                                        
           EJECT                                                        
           SKIP1                                                        
       01  WPDKTELR-KEY.                                                
           05 WPDKTELR-KEY-MATR.                                        
              10  WPDKTELR-KEY-COD       PIC X(5).                      
              10  WPDKTELR-KEY-PAD       PIC X.                         
           05 WPDKTELR-KEY-ANNO          PIC X(4).                      
           05 WPDKTELR-KEY-PROG          PIC 99.                        
           05 FILLER                     PIC X(3).                      
           SKIP1                                                        
      ************************************************************      
      *                     VARIABILI                            *      
      ************************************************************      
       01  FILLER.                                                      
           05   WCODICESP.                                              
                10   WCODICESP-MATR    PIC X(5).                        
                10   WCODICESP-PAD     PIC X.                           
           SKIP1                                                        
           05   IND-CODA           PIC 99.                              
           05   WNUMREC-CODA-INIZ  PIC S9(5) COMP-3.                    
           05   WNUMREC-CODA       PIC S9(5) COMP-3.                    
           05   WPASSO-CODA        PIC S9(3) COMP-3 VALUE +28.          
           05   WCTRIG             PIC S9(3) COMP-3.                    
           05   WCTPAG             PIC S999 VALUE +1.                   
           05   WW-DATE            PIC S9(18)  COMP.                    
           05   MAX-RIGHE          PIC S9(3) COMP-3  VALUE +14.         
           05   SAVE-RIG           PIC S9(3) COMP-3.                    
           05   ASKIP-DRK          PIC X VALUE '('.                     
           05   ASKIP-DRK-FSET     PIC X VALUE '_'.                     
           05   WKOST              PIC 9(2) VALUE 12.                   
           05   WNOME-COMPATTO     PIC X(60).                           
           05   WCHIAVE-ORDINE     PIC X(60).                           
      * DIREZIONE DEL BROWSE A (AVANTI) I (INDIETRO)                    
           05   WDIREZIONE         PIC X VALUE 'A'.                     
           SKIP1                                                        
           05   COM3               PIC 999.                             
           05   COM3X REDEFINES COM3  PIC XXX.                          
           SKIP1                                                        
      *    ANNO FINANZIARIO CORRENTE                                    
           05   ANNO-CORRENTE      PIC 99    VALUE 87.                  
           SKIP1                                                        
           05   WDATA.                                                  
                10   WDATA-GG     PIC XX.                               
                10   FILLER       PIC X   VALUE '/'.                    
                10   WDATA-MM     PIC XX.                               
                10   FILLER       PIC X   VALUE '/'.                    
                10   WDATA-AA     PIC XX.                               
           SKIP1                                                        
           05   WDATAEL.                                                
                10   WDATAEL-GG   PIC 99.                               
                10   FILLER       PIC X.                                
                10   WDATAEL-MM   PIC 99.                               
                10   FILLER       PIC X.                                
                10   WDATAEL-AA   PIC 99.                               
           SKIP1                                                        
           05   WDATA-RIGA.                                             
                10   WDATA-RIGA-GG PIC 99.                              
                10   FILLER        PIC X VALUE '/'.                     
                10   WDATA-RIGA-MM PIC 99.                              
                10   FILLER        PIC X VALUE '/'.                     
                10   WDATA-RIGA-AA PIC 9999.                            
           SKIP1                                                        
           05   WKEY.                                                   
                10   WKEY-CODDIP.                                       
                     15   WKEY-MATR    PIC 9(5).                        
                     15   WKEY-PAD     PIC 9.                           
                10   WKEY-TREC    PIC 99.                               
                10   WKEY-COD1    PIC 99.                               
                10   WKEY-COD2    PIC 99.                               
           SKIP1                                                        
           05   WKEYX.                                                  
                10   WKEY-MATRX   PIC 9(5).                             
                10   WKEY-PADX    PIC 9.                                
           EJECT                                                        
      *-----------------------------------------------------            
      *  LUNGHEZZA RECORD CODA TS(VEDI WRECTS)                          
      *-----------------------------------------------------            
       01  WLUNG-RECTS    PIC S9(4) COMP  VALUE +60.                    
           SKIP1                                                        
       01  WRECTS.                                                      
           05  WRECTS-CODICESP.                                         
                 10  WRECTS-CODICESP-MATRX      PIC  X(5).              
                 10  WRECTS-CODICESP-PADX       PIC  X.                 
           SKIP1                                                        
           05  WRECTS-ANNO                      PIC X(4).               
           05  WRECTS-PROG                      PIC X(1).               
           05  WRECTS-SESSLIQ-ANNO              PIC X(4).               
           05  WRECTS-SESSLIQ-MESE              PIC X(2).               
           05  WRECTS-BOLLETTA-ANNO             PIC X(4).               
           05  WRECTS-BOLLETTA-BIM              PIC X(2).               
           05  WRECTS-PROG-TELEF                PIC X(2).               
           05  WRECTS-IMPO1                     PIC S9(11)  COMP-3.     
           05  WRECTS-IMPO2                     PIC S9(11)  COMP-3.     
           05  WRECTS-IMPO3                     PIC S9(11)  COMP-3.     
           05  WRECTS-IMPO4                     PIC S9(11)  COMP-3.     
           05  WRECTS-IMPO5                     PIC S9(11)  COMP-3.     
           05  WRECTS-TOPZ                      PIC X(1).               
           05  FILLER                          PIC  X(4).               
           SKIP1                                                        
      ************************************************************      
      *                     R E C O R D S                        *      
      ************************************************************      
       01  PDRTELR-RECORD.                                              
           COPY PDRTELR.                                                
           EJECT                                                        
       01  PDRAL01-RECORD.                                              
           COPY PDRAL01.                                                
           EJECT                                                        
       01  WPDRGCODA.                                                   
           COPY PDRGCODA.                                               
           EJECT                                                        
       01  WPDRUTI01.                                                   
           COPY PDRUTI01.                                               
           EJECT                                                        
       01  WPDRSELE.                                                    
           COPY PDRSELE.                                                
           EJECT                                                        
      *----------------------------------------------------------*      
      *                                                                 
      *----------------------------------------------------------*      
       01  WPD1AC.                                                      
           COPY PD1AC.                                                  
           EJECT                                                        
      ****************************************************              
      *     AREA DI LAVORO PER PREPARAZIONE MAPPA        *              
      *               (LUNGHEZZA = 79)                   *              
      ****************************************************              
           SKIP1                                                        
       01  RIGA-MAPPA.                                                  
           05  RIGA-CODICE          PIC 9(6).                           
           05  FILLER               PIC X.                              
           05  RIGA-COGN-NOME       PIC X(30).                          
           05  FILLER               PIC X.                              
           05  RIGA-ANNO-PLAFOND    PIC X(4).                           
           05  FILLER               PIC X.                              
           05  RIGA-BOLLETTA-BIM    PIC X(2).                           
           05  RIGA-BOLLETTA-SEP    PIC X.                              
           05  RIGA-BOLLETTA-ANNO   PIC X(4).                           
           05  FILLER               PIC X(3).                           
           05  RIGA-PROG-TELEF      PIC X(2).                           
           05  FILLER               PIC X.                              
           05  RIGA-IMPO-RIMBORSO   PIC X(14).                          
           05  FILLER               PIC X.                              
           05  RIGA-SESSIONE-ANNO   PIC X(4).                           
           05  RIGA-SESSIONE-SEP    PIC X.                              
           05  RIGA-SESSIONE-MESE   PIC X(2).                           
           05  FILLER               PIC X(1).                           
           EJECT                                                        
      ************************************************************      
      *                       M A P P E                          *      
      ************************************************************      
           COPY PDB305M SUPPRESS.                                       
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
      ***  03   TWA-BLL           PIC S9(8) COMP.                       
           COPY PDRTWA2.                                                
           EJECT                                                        
      ************************************************************      
      *                   PROCEDURE DIVISION                     *      
      ************************************************************      
       PROCEDURE DIVISION.                                              
           PERFORM ADDRESS-TWA.                    
           EXEC SQL WHENEVER SQLERROR GO TO ERRORE-SQL END-EXEC
           EXEC SQL SELECT SYSDATE INTO :HSQL-DATE FROM DUAL END-EXEC            
           SKIP1                                                        
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
           MOVE  LOW-VALUE TO PDB3051I.                                 
      *                                                                 
      *-SE E' RICHIESTA LA PRESENTAZIONE PER CODICE VIENE               
      *-BYPASSATO IL LINK AL PROGRAMMA DI SELEZIONE ALFABETICA          
      *                                                                 
           IF  TWCOB-PRESENTA-NOMI  =  'C'  THEN                        
               GO  TO  BROWSE-FASE1-10.                                 
           SKIP1                                                        
      *-----------------------------------------------------------      
      *------LINK AL PROGRAMMA PD3SORT  PER SELEZIONE ALFABETICA        
      *-----------------------------------------------------------      
           SKIP1                                                        
           PERFORM LINK-SELE   THRU LINK-SELE-EXIT.                     
           SKIP1                                                        
       BROWSE-FASE1-10.                                                 
           MOVE  +1   TO WNUMREC-CODA-INIZ.                             
           MOVE  ZERO TO WNUMREC-CODA.                                  
           PERFORM PREPARA-MAP THRU PREPARA-MAP-EXIT.                   
           SKIP1                                                        
      ***  IF  PDRGCODA-RETURN  =  '1'  THEN                            
      *        MOVE  WINES  TO  M1MSGO                                  
      ***      GO  TO  BROWSE-FASE1-ERR.                                
           SKIP1                                                        
           IF  PDRGCODA-RETURN  =  '2'  THEN                            
               MOVE  WNOTROV TO  M1MSGO                                 
               GO  TO  BROWSE-FASE1-ERR.                                
           SKIP1                                                        
           IF  PDRGCODA-RETURN  =  'E'  THEN                            
               MOVE  WERRORE TO  M1MSGO                                 
               GO  TO  BROWSE-FASE1-ERR.                                
           SKIP1                                                        
      *                                                                 
      *------- SALVA PROGRESSIVO RECORD CODA IN TWA                     
      *                                                                 
           MOVE  WNUMREC-CODA  TO   TWCOB-ITEM-CODA.                    
           MOVE  WNUMREC-CODA-INIZ   TO   TWCOB-ITEM-CODA-INIZ.         
           MOVE  WCTPAG        TO   TWCOB-BRO-PAG-CORR.                 
           SKIP1                                                        
           MOVE  SPACES  TO  M1MSGO.                                    
           PERFORM  SEND-PDB3051.                                       
           MOVE  '2' TO  TWCOB-FASE.                                    
           GO TO RETURN-MAIN.                                           
           SKIP2                                                        
       BROWSE-FASE1-ERR.                                                
           PERFORM  MUOVI-TESTATA THRU MUOVI-TESTATA-EXIT.              
           MOVE ASKIP-DRK-FSET TO M1PF7A.                               
           MOVE ASKIP-DRK-FSET TO M1PF8A.                               
           MOVE  -1  TO M1MSGL.                                         
           PERFORM  SEND-PDB3051.                                       
           MOVE  '2' TO  TWCOB-FASE.                                    
           GO TO RETURN-MAIN.                                           
           EJECT                                                        
      ************************************************************      
      *     VISUALIZZAZIONE BROWSE                               *      
      ************************************************************      
       BROWSE-FASE2.                                                    
           MOVE  TWCOB-ITEM-CODA          TO WNUMREC-CODA.              
           MOVE  TWCOB-ITEM-CODA-INIZ     TO WNUMREC-CODA-INIZ.         
           MOVE  TWCOB-BRO-PAG-CORR TO WCTPAG.                          
           SKIP1                                                        
           PERFORM  RECEIVE-PDB3051.                                    
           IF  EIBAID = DFHENTER THEN                                   
               GO TO BROWSE-FASE2-ENTER.                                
           IF  EIBAID = DFHPF1   THEN                                   
               GO TO XCTL-PF1.                                          
           IF  EIBAID = DFHPF2   THEN                                   
               GO TO XCTL-PF2.                                          
           IF  EIBAID = DFHPF9   THEN                                   
               GO TO XCTL-PF9.                                          
           IF  EIBAID = DFHPF7   THEN                                   
               GO TO BROWSE-PF7.                                        
           IF  EIBAID = DFHPF8   THEN                                   
               GO TO BROWSE-PF8.                                        
           GO TO BROWSE-FASE2-TASTOER.                                  
           SKIP1                                                        
       BROWSE-FASE2-ENTER.                                              
      **   ADD   +1  TO  WNUMREC-CODA.                                  
           MOVE  WNUMREC-CODA  TO   WNUMREC-CODA-INIZ.                  
           ADD   +1            TO   WNUMREC-CODA-INIZ.                  
           ADD   +1  TO  WCTPAG.                                        
           SKIP1                                                        
       BROWSE-FASE2-ENTER-010.                                          
           PERFORM PREPARA-MAP THRU PREPARA-MAP-EXIT.                   
           IF  PDRGCODA-RETURN  =  '1'  AND                             
               WCTRIG NOT GREATER 1                                     
               GO  TO  XCTL-PF2.                                        
           SKIP1                                                        
           MOVE  WNUMREC-CODA        TO   TWCOB-ITEM-CODA.              
           MOVE  WNUMREC-CODA-INIZ   TO   TWCOB-ITEM-CODA-INIZ.         
           MOVE  WCTPAG  TO  TWCOB-BRO-PAG-CORR.                        
           MOVE  SPACES  TO  M1MSGO.                                    
           PERFORM  SEND-PDB3051.                                       
           MOVE  '2' TO  TWCOB-FASE.                                    
           GO TO RETURN-MAIN.                                           
           SKIP1                                                        
       BROWSE-FASE2-TASTOER.                                            
           MOVE  -1  TO M1MSGL.                                         
           MOVE  WTASTOER     TO M1MSGO.                                
           PERFORM  SEND-PDB3051-DO.                                    
           GO TO RETURN-MAIN.                                           
           SKIP1                                                        
       BROWSE-PF7.                                                      
           IF  WCTPAG  =   1    THEN                                    
               GO  TO  BROWSE-FASE2-TASTOER.                            
      ***  SUBTRACT  WPASSO-CODA  FROM  WNUMREC-CODA-INIZ.              
           SUBTRACT  WPASSO-CODA  FROM  WNUMREC-CODA.                   
      ***  MOVE   TWCOB-ITEM-CODA-INIZ  TO WNUMREC-CODA.                
      ***  SUBTRACT  1  FROM  WNUMREC-CODA.                             
           SUBTRACT  1  FROM  WCTPAG.                                   
           GO  TO  BROWSE-FASE2-ENTER-010.                              
           SKIP1                                                        
       BROWSE-PF8.                                                      
           IF  WCTPAG  =   1    THEN                                    
               GO  TO  BROWSE-FASE2-TASTOER.                            
           SKIP1                                                        
      *    MOVE    ZERO TO    WNUMREC-CODA-INIZ.                        
           MOVE    ZERO TO    WNUMREC-CODA.                             
      *    MOVE      1  TO    WNUMREC-CODA.                             
           MOVE      1  TO    WCTPAG.                                   
           GO  TO  BROWSE-FASE2-ENTER-010.                              
           EJECT                                                        
      ************************************************************      
      *            INIZIALIZZAZIONE DEI PARAMETRI                *      
      *                       PER IL READER                      *      
      ************************************************************      
       INIZ-PARAM.                                                      
           MOVE     01       TO  PDRGCODA-FUNZIONE.                     
           MOVE  EIBTRMID    TO  PDRGCODA-NOMETERM.                     
           MOVE   'PD40'     TO  PDRGCODA-KOST.                         
           MOVE WNUMREC-CODA TO  PDRGCODA-PROG-REC.                     
           SKIP1                                                        
       INIZ-PARAM-EXIT.                                                 
           EXIT.                                                        
           SKIP2                                                        
      ************************************************************      
      *   LINK ALLA ROUTINE LETTURA CODA CODICI                         
      ************************************************************      
       LINK-CODA.                                                       
           MOVE  '01'       TO  PDRGCODA-FUNZIONE.                      
           SKIP1                                                        
           EXEC CICS LINK PROGRAM('PD0GCODA') COMMAREA(WPDRGCODA)       
               LENGTH(PDRGCODA-LUNGH) END-EXEC.                         
           SKIP1                                                        
       LINK-CODA-EXIT.                                                  
           EXIT.                                                        
           EJECT                                                        
      ************************************************************      
      *   LINK ALLA ROUTINE SELEZIONE ALFABETICA                 *      
      ************************************************************      
       LINK-SELE.                                                       
           MOVE  '01'       TO  PDRSELE-FUNZIONE.                       
           MOVE  EIBTRMID   TO  PDRSELE-NOMETERM.                       
           MOVE  'PD40'     TO  PDRSELE-KOST.                           
           MOVE  '01'       TO  PDRSELE-NELEM-CODA.                     
           SKIP1                                                        
           EXEC CICS LINK PROGRAM('PD3SORT') COMMAREA(WPDRSELE)         
               LENGTH(PDRSELE-LUNG-COMMA) END-EXEC.                     
           SKIP1                                                        
       LINK-SELE-EXIT.                                                  
           EXIT.                                                        
           EJECT                                                        
      ************************************************************      
      *                PREPARAZIONE MAPPA                        *      
      ************************************************************      
       PREPARA-MAP.                                                     
           MOVE    WCTPAG        TO  COM3.                              
           PERFORM MUOVI-TESTATA THRU MUOVI-TESTATA-EXIT.               
           PERFORM ABBL-RIGA   THRU ABBL-RIGA-EXIT.                     
           MOVE      1         TO   WCTRIG.                             
           SKIP1                                                        
       PREPARA-MAP-010.                                                 
           IF  WCTRIG    GREATER  14  THEN                              
               GO TO PREPARA-MAP-020.                                   
           SKIP1                                                        
           ADD +1   TO WNUMREC-CODA.                                    
           PERFORM INIZ-PARAM  THRU INIZ-PARAM-EXIT.                    
           PERFORM LINK-CODA   THRU LINK-CODA-EXIT.                     
           SKIP1                                                        
           IF  PDRGCODA-RETURN  =  '1'  THEN                            
               GO  TO  PREPARA-MAP-EXIT.                                
           SKIP1                                                        
           IF  PDRGCODA-RETURN  =  '2'  OR 'E'                          
              THEN MOVE 'TF01'  TO WABEND-CODE                          
                   GO TO ABEND00.                                       
           SKIP1                                                        
      ***  IF  PDRGCODA-PD40-ELEM           EQUAL SPACE THEN            
      *        MOVE  ASKIP-DRK-FSET      TO  MENTERA                    
      *        MOVE  ASKIP-DRK-FSET      TO  MINVIOA                    
      **       GO TO PREPARA-MAP-030.                                   
           SKIP1                                                        
           IF  PDRGCODA-PD40-CODDIP  =  '000000'  THEN                  
               GO  TO  PREPARA-MAP-030.                                 
           SKIP1                                                        
           PERFORM LEGGI-PDRAL01 THRU LEGGI-PDRAL01-EXIT.               
           PERFORM  MUOVI-DATI THRU  MUOVI-DATI-EXIT.                   
      ***  ADD  +1   TO  IND-CODA.                                      
           GO  TO  PREPARA-MAP-010.                                     
           SKIP1                                                        
       PREPARA-MAP-020.                                                 
           PERFORM CONTR-DATI   THRU CONTR-DATI-EXIT.                   
      **** SUBTRACT  1  FROM  IND-CODA.                                 
           GO  TO  PREPARA-MAP-EXIT.                                    
           SKIP1                                                        
       PREPARA-MAP-030.                                                 
      ***  IF  WCTRIG  GREATER  10  THEN                                
      *        SUBTRACT  1  FROM  IND-CODA                              
      ***      GO  TO  PREPARA-MAP-EXIT.                                
           SKIP1                                                        
           MOVE  SPACES  TO  RIGA-MAPPA.                                
      ***  ADD  +1  TO  WCTRIG.                                         
           MOVE  'T O T A L I'   TO  RIGA-COGN-NOME.                    
           SKIP1                                                        
           MOVE  PDRGCODA-PD40-IMPO2     TO WIMP11.                     
           MOVE '04'                     TO PDRUTI01-FUNZIONE.          
           MOVE  WIMP11                  TO PDRUTI01-F04-VALORE.        
           PERFORM LINK-PD0UTI01  THRU LINK-PD0UTI01-EXIT.              
           MOVE  PDRUTI01-F04-IMPOX14    TO RIGA-IMPO-RIMBORSO.         
                                                                        
           MOVE  RIGA-MAPPA            TO MRIGAO(WCTRIG).               
           SKIP1                                                        
       PREPARA-MAP-EXIT.                                                
           EXIT.                                                        
           EJECT                                                        
      ************************************************************      
      *    IMPOSTAZIONE TESTATA DELLA MAPPA                      *      
      ************************************************************      
       MUOVI-TESTATA.                                                   
           MOVE  COM3X             TO  MPAGO.                           
      ***  MOVE  CURRENT-DATE      TO  WDATAEL.                         
           EXEC CICS ASKTIME  ABSTIME(WW-DATE)   END-EXEC.              
           EXEC CICS FORMATTIME  ABSTIME(WW-DATE)  DDMMYY(M1DATAO)      
                     DATESEP  END-EXEC.                                 
           SKIP1                                                        
      *    MOVE  WDATAEL-GG        TO  WDATA-GG.                        
      *    MOVE  WDATAEL-MM        TO  WDATA-MM.                        
      *    MOVE  WDATAEL-AA        TO  WDATA-AA.                        
      *    MOVE  WDATA             TO  M1DATAO.                         
           SKIP1                                                        
           IF TWCOB-FUNZIONE = 'T'                                      
             THEN MOVE ASKIP-DRK  TO KTEST1A                            
                  MOVE ASKIP-DRK  TO KTEST3A.                           
           SKIP1                                                        
       MUOVI-TESTATA-EXIT.                                              
           EXIT.                                                        
           EJECT                                                        
      ************************************************************      
      *        TRASFERIMENTO DATI SULLA MAPPA                    *      
      ************************************************************      
       MUOVI-DATI.                                                      
           MOVE  SPACE  TO   RIGA-MAPPA.                                
           MOVE  PDRGCODA-PD40-CODDIP TO RIGA-CODICE.                   
           SKIP1                                                        
           PERFORM COMPATTA-NOME THRU COMPATTA-NOME-EXIT.               
           MOVE  WNOME-COMPATTO       TO RIGA-COGN-NOME.                
           SKIP1                                                        
           IF TWCOB-FUNZIONE = 'T'                                      
              THEN GO TO MUOVI-DATI-010.                                
           SKIP1                                                        
           MOVE  PDRGCODA-PD40-ANNO      TO RIGA-ANNO-PLAFOND.          
           MOVE  PDRGCODA-PD40-SESSLIQ-ANNO TO RIGA-SESSIONE-ANNO.      
           MOVE  '/'                        TO RIGA-SESSIONE-SEP.       
           MOVE  PDRGCODA-PD40-SESSLIQ-MESE TO RIGA-SESSIONE-MESE.      
           SKIP1                                                        
           MOVE  PDRGCODA-PD40-BOLLETTA-ANNO TO RIGA-BOLLETTA-ANNO.     
           MOVE  '/'                        TO RIGA-BOLLETTA-SEP.       
           MOVE  PDRGCODA-PD40-BOLLETTA-BIM  TO RIGA-BOLLETTA-BIM.      
           SKIP1                                                        
           MOVE  PDRGCODA-PD40-PROG-TELEF TO RIGA-PROG-TELEF.           
           SKIP1                                                        
       MUOVI-DATI-010.                                                  
           MOVE  PDRGCODA-PD40-IMPO2     TO WIMP11.                     
           MOVE '04'                     TO PDRUTI01-FUNZIONE.          
           MOVE  WIMP11                  TO PDRUTI01-F04-VALORE.        
           PERFORM LINK-PD0UTI01  THRU LINK-PD0UTI01-EXIT.              
           MOVE  PDRUTI01-F04-IMPOX14    TO RIGA-IMPO-RIMBORSO.         
                                                                        
           SKIP1                                                        
           MOVE  RIGA-MAPPA           TO MRIGAO(WCTRIG).                
           ADD         +1             TO WCTRIG.                        
           SKIP1                                                        
       MUOVI-DATI-EXIT.                                                 
           EXIT.                                                        
           EJECT                                                        
      ************************************************************      
      *     ABBLENCAMENTO DELLA RIGA DELLA MAPPA                 *      
      ************************************************************      
       ABBL-RIGA.                                                       
           MOVE   1    TO  WCTRIG.                                      
       ABBL-RIGA-10.                                                    
           MOVE  SPACE  TO   MRIGAO(WCTRIG).                            
           ADD    1     TO   WCTRIG.                                    
           IF  WCTRIG NOT  GREATER MAX-RIGHE GO TO ABBL-RIGA-10.        
           SKIP1                                                        
       ABBL-RIGA-EXIT.                                                  
           EXIT.                                                        
           SKIP2                                                        
      ************************************************************      
      *     CONTROLLO DATI PRIMA DI INVIARE LA MAPPA             *      
      ************************************************************      
       CONTR-DATI.                                                      
           IF WCTPAG   EQUAL  1   THEN                                  
              MOVE  ASKIP-DRK-FSET      TO  M1PF7A                      
              MOVE  ASKIP-DRK-FSET      TO  M1PF8A.                     
       CONTR-DATI-EXIT.                                                 
           EXIT.                                                        
           SKIP2                                                        
      ************************************************************      
      *   COMPATTAMENTO COGNOME E NOME                                  
      *  INPUT :                                                        
      *  OUTPUT: WNOME-COMPATTO                                         
      ************************************************************      
       COMPATTA-NOME.                                                   
           MOVE  '20'   TO  PDRUTI01-FUNZIONE.                          
           MOVE  DA-COGNOME    TO  PDRUTI01-F20-CAMPO1.                 
           MOVE  DA-NOME       TO  PDRUTI01-F20-CAMPO2.                 
           MOVE  '*'              TO  PDRUTI01-F20-CAR-SEPARA.          
           PERFORM LINK-PD0UTI01  THRU LINK-PD0UTI01-EXIT.              
           MOVE PDRUTI01-F20-COMPATTATO TO WNOME-COMPATTO.              
           SKIP1                                                        
       COMPATTA-NOME-EXIT.                                              
           EXIT.                                                        
           SKIP1                                                        
      ************************************************************      
      *   LINK ALLA ROUTINE CONTROLLO IMPORTO                           
      ************************************************************      
       LINK-PD0UTI01.                                                   
           MOVE HIGH-VALUE TO  PDRUTI01-RETURN.                         
           SKIP1                                                        
           EXEC CICS LINK PROGRAM('PD0UTI01') COMMAREA(WPDRUTI01)       
               LENGTH(PDRUTI01-LUNG-COMMA) END-EXEC.                    
           SKIP1                                                        
           IF  PDRUTI01-RETURN EQUAL 'E'                                
             THEN MOVE  'UT$$'  TO  WABEND-CODE                         
                  GO TO ABEND00.                                        
           SKIP1                                                        
       LINK-PD0UTI01-EXIT.                                              
           EXIT.                                                        
           SKIP1                                                        
           EJECT                                                        
      ************************************************************      
      * BROWSE  ARCHIVIO  VERSAMENTI CONTRIBUTI VOLONTARI               
      * INPUT:                                                          
      * OUTPUT:                                                         
      ************************************************************      
      *BROWSE-PDKTELR.                                                  
      *    MOVE  SPACE TO WTABREC.                                      
      *    SKIP1                                                        
      *    MOVE ZERO TO NUMERO-REC.                                     
      *    MOVE  DA-CHIAVE-MATR    TO   WCODICESP-MATR.                 
      *    MOVE  DA-CHIAVE-PAD     TO   WCODICESP-PAD.                  
      *    SKIP1                                                        
      *--------------------------------------------------------         
      *    MOVE  ZERO       TO WPDKTELR-KEY.                            
      ***  MOVE  WCODICESP  TO WPDKTELR-KEY-MATR.                       
      *    SKIP1                                                        
      *    EXEC  CICS IGNORE  CONDITION DUPKEY END-EXEC.                
      *    SKIP1                                                        
      *    EXEC  CICS  HANDLE CONDITION NOTFND(BROWSE-PDKTELR-100)      
      *          ENDFILE(BROWSE-PDKTELR-END) END-EXEC.                  
      *    SKIP1                                                        
      *    EXEC CICS STARTBR  DATASET('PDKTELR') RIDFLD(WPDKTELR-KEY)   
      *          END-EXEC.                                              
      *    SKIP1                                                        
      *BROWSE-PDKTELR-LOOP.                                             
      *    MOVE  WLUNG-PDKTELR   TO WLUNG.                              
      *    SKIP1                                                        
      *    EXEC  CICS  READNEXT DATASET('PDKTELR') RIDFLD(WPDKTELR-KEY) 
      *          INTO(PDRTELR-RECORD) LENGTH(WLUNG) END-EXEC.           
      *    SKIP1                                                        
      *    GO  TO  BROWSE-PDKTELR-020.                                  
      *    SKIP1                                                        
      *    IF PDRTELR-CODDIP   NOT  EQUAL  WCODICESP                    
      *       THEN  GO  TO  BROWSE-PDKTELR-END.                         
      *    SKIP1                                                        
      *    SKIP1                                                        
      *    IF NUMERO-REC NOT LESS 30                                    
      *      THEN  MOVE 'TE15'  TO WABEND-CODE                          
      *            GO TO ABEND00.                                       
      *    SKIP1                                                        
      **   ADD    +1    TO   NUMERO-REC.                                
      **   MOVE  PDRTELR-RECORD    TO   WTABREC-EL(NUMERO-REC).         
      *    SKIP1                                                        
      *BROWSE-PDKTELR-020.                                              
      *    PERFORM MUOVI-DATI THRU MUOVI-DATI-EXIT.                     
      *    GO  TO  BROWSE-PDKTELR-LOOP.                                 
      *    SKIP1                                                        
      *BROWSE-PDKTELR-END.                                              
      *    EXEC  CICS  ENDBR DATASET('PDKTELR')                         
      *          END-EXEC.                                              
      *    SKIP1                                                        
      *BROWSE-PDKTELR-100.                                              
      *    SKIP1                                                        
      *BROWSE-PDKTELR-EXIT.                                             
      ***  EXIT.                                                        
      *    SKIP1                                                        
      ************************************************************      
      * LETTURA RIMBORSO                                                
      * INPUT:                                                          
      * OUTPUT:                                                         
      ************************************************************      
      *LEGGI-RIMBORSO.                                                  
      *    MOVE  PDRGCODA-PD40-KEY-PDKTELR TO WPDKTELR-KEY.             
      *    MOVE WLUNG-PDKTELR  TO WLUNG.                                
      *    SKIP1                                                        
      *    EXEC  CICS  HANDLE CONDITION NOTFND(LEGGI-RIMBORSO-NOTFND)   
      *          END-EXEC.                                              
      *    SKIP1                                                        
      *    EXEC  CICS  READ  DATASET('PDKTELR') RIDFLD(WPDKTELR-KEY)    
      *          INTO(PDRTELR-RECORD) LENGTH(WLUNG) END-EXEC.           
      *    SKIP1                                                        
      *    GO  TO  BROWSE-PDKTELR-EXIT.                                 
      *    SKIP1                                                        
      *LEGGI-RIMBORSO-NOTFND.                                           
      *    MOVE  SPACE  TO PDRTELR-RECORD.                              
      *    GO TO ABEND00.                                               
      *    SKIP1                                                        
      *LEGGI-RIMBORSO-EXIT.                                             
      ***  EXIT.                                                        
      **                                                                
      ************************************************************      
      *  LETTURA RECORD ANAGRAFICO                                      
      ************************************************************      
       LEGGI-PDRAL01.                                                   
           MOVE         '01'          TO PD1AC-FUNZIONE.                
           MOVE         '5'           TO PD1AC-CODICE-IP-TIPO.          
           MOVE PDRGCODA-PD40-CODDIP-MATR  TO PD1AC-CODICE-IP-MATR.     
           MOVE PDRGCODA-PD40-CODDIP-PAD   TO PD1AC-CODICE-IP-PAD.      
           SKIP1                                                        
           PERFORM LINK-PD1AC THRU LINK-PD1AC-EXIT.                     
           SKIP1                                                        
           IF PD1AC-PDRAL01 = SPACE                                     
             THEN MOVE 'AB69'  TO WABEND-CODE                           
                  GO TO ABEND00.                                        
           SKIP1                                                        
           MOVE PD1AC-PDRAL01  TO  PDRAL01-RECORD.                      
           SKIP1                                                        
       LEGGI-PDRAL01-EXIT.                                              
           EXIT.                                                        
           SKIP1                                                        
           SKIP1                                                        
      ************************************************************      
      *   LINK ALLA ROUTINE NOMINATIVI AV (PD1AC)                       
      ************************************************************      
       LINK-PD1AC.                                                      
           MOVE HIGH-VALUE TO  PD1AC-RETURN.                            
           SKIP1                                                        
           EXEC CICS LINK PROGRAM('PD1AC') COMMAREA(WPD1AC)             
               LENGTH(PD1AC-LUNGH) END-EXEC.                            
           SKIP1                                                        
           IF  PD1AC-RETURN EQUAL 'E'                                   
             THEN MOVE  'AV05'  TO  WABEND-CODE                         
                  GO TO ABEND00.                                        
           SKIP1                                                        
       LINK-PD1AC-EXIT.                                                 
           EXIT.                                                        
           SKIP1                                                        
           EJECT                                                        
      ************************************************************      
      *                  INDIRIZZA TWA                           *      
      ************************************************************      
       ADDRESS-TWA.                                                     
           EXEC CICS ADDRESS TWA(ADDRESS OF PDRTWA2) END-EXEC.          
           SKIP2                                                        
           EJECT                                                        
      ************************************************************      
      *              INVIO MAPPA  PDB3051                        *      
      ************************************************************      
       SEND-PDB3051.                                                    
           EXEC CICS SEND MAP('PDB3051') MAPSET('PDB305M') ERASE        
               CURSOR END-EXEC.                                         
       SEND-PDB3051-EXIT.                                               
           EXIT.                                                        
           SKIP2                                                        
      ************************************************************      
      *          INVIO MAPPA  PDB3051 (DATA ONLY)                *      
      ************************************************************      
       SEND-PDB3051-DO.                                                 
           EXEC CICS SEND MAP('PDB3051') MAPSET('PDB305M') CURSOR       
               DATAONLY END-EXEC.                                       
       SEND-PDB3051-DO-EXIT.                                            
           EXIT.                                                        
           SKIP2                                                        
      ************************************************************      
      *              LETTURA MAPPA PDB3051                       *      
      ************************************************************      
       RECEIVE-PDB3051.                                                 
           EXEC CICS RECEIVE MAP('PDB3051') MAPSET('PDB305M')  END-EXEC.
       RECEIVE-PDB3051-EXIT.                                            
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
       XCTL-PF1.                                                        
           MOVE '1' TO TWCOB-FASE.                                      
           MOVE '1' TO TWCOB-FUNZIONE.                                  
           MOVE PROG-PF1           TO TWCOB-NOME-PGM.                   
           PERFORM RESET-TWA  THRU  RESET-TWA-EXIT.                     
           GO TO XCTL-MAIN.                                             
           SKIP1                                                        
       XCTL-PF2.                                                        
           MOVE '1' TO TWCOB-FASE.                                      
           MOVE '1' TO TWCOB-FUNZIONE.                                  
           MOVE PROG-PF2           TO TWCOB-NOME-PGM.                   
           PERFORM RESET-TWA  THRU  RESET-TWA-EXIT.                     
           GO TO XCTL-MAIN.                                             
           SKIP1                                                        
           SKIP1                                                        
       XCTL-PF9.                                                        
           MOVE '1' TO TWCOB-FASE.                                      
           MOVE '1' TO TWCOB-FUNZIONE.                                  
           MOVE PROG-PF9 TO TWCOB-NOME-PGM.                             
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
      *   PREPARAZIONE CHIAVE RECORD ANAGRAFICO   (REC01)        *      
      ************************************************************      
      *PREP-KEY01.                                                      
      *    MOVE  PDRGCODA-PD40-CODDIP  TO WKEY-CODDIP.                  
      *    MOVE     01                      TO WKEY-TREC.               
      *    MOVE     00                      TO WKEY-COD1.               
      *    MOVE     00                      TO WKEY-COD2.               
      *    SKIP1                                                        
      *PREP-KEY01-EXIT.                                                 
      *    EXIT.                                                        
      ************************************************************      
      *   PREPARAZIONE LINK AL READER                            *      
      ************************************************************      
      *PREP-LINK01.                                                     
      *    SKIP1                                                        
      *    MOVE     SPACES                  TO PDRREAD2.                
      *    MOVE     WKEY                    TO IO-CHIAVE-INIZ.          
      *    MOVE     '04'                    TO IO-FUNZIONE.             
      *    MOVE     'PDSPAL'                TO IO-NOME-ARCHIVIO.        
      *    SKIP1                                                        
      *PREP-LINK01-EXIT.                                                
      ***  EXIT.                                                        
      *    EJECT                                                        
      ************************************************************      
      *   LETTURA  RECORD  ANAGRAFICO FILE PDSPAL (REC01)        *      
      ************************************************************      
      *LINK-IO.                                                         
      *    SKIP1                                                        
      *    EXEC CICS LINK PROGRAM('PDREADER') COMMAREA(PDRREAD2)        
      *        LENGTH(5090) END-EXEC.                                   
      *    SKIP1                                                        
      *LINK-IO-EXIT.                                                    
      *    EXIT.                                                        
      *    SKIP2                                                        
      ************************************************************      
      *             SALVATAGGIO TWA COMUNE                       *      
      ************************************************************      
       SAVE-TWA.                                                        
           COPY PDSAVTW2.                                               
           SKIP2                                                        
       FINE-ELABORAZIONE.                                               
           STOP RUN.                                                    
      ************************************************************      
      ************************************************************      
      ************************************************************      
      ************************************************************      
