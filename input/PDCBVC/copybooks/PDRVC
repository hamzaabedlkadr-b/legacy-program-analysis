      **********************************************************        
      *  VARIAZIONI CONTABILI IP/AV:  LRECL=200;   CHIAVE=20            
      *  FILE: PDKIPVC / PDKAVVC                                        
      *********************************************************         
           05  PDRVC-CHIAVE.                                            
               10  PDRVC-CHIAVE-CODICE.                                 
                   15  PDRVC-CHIAVE-CODICE-TIPO    PIC X.               
                   15  PDRVC-CHIAVE-CODICE-MATR    PIC X(5).            
                   15  PDRVC-CHIAVE-CODICE-PAD     PIC X.               
                   15  PDRVC-CHIAVE-CODICE-PADN  REDEFINES              
                         PDRVC-CHIAVE-CODICE-PAD   PIC 9.               
           SKIP1                                                        
               10  PDRVC-CHIAVE-VOCE.                                   
                   15  PDRVC-CHIAVE-VOCE-NTAB      PIC X.               
                   15  PDRVC-CHIAVE-VOCE-COD       PIC X(3).            
           SKIP1                                                        
               10  PDRVC-CHIAVE-PROG               PIC 999.             
               10  FILLER                          PIC X(6).            
           SKIP1                                                        
      *--------------------------------------------------*              
      *  IDENTIFICATIVO ULTIMO AGGIORNAMENTO                            
      *--------------------------------------------------*              
           05  PDRVC-COD-OPERAT                    PIC X(4).            
           05  PDRVC-ULTAGG-DATA.                                       
               10  PDRVC-ULTAGG-GG                 PIC 99.              
               10  PDRVC-ULTAGG-MM                 PIC 99.              
               10  PDRVC-ULTAGG-AA                 PIC 99.              
           SKIP1                                                        
           05  PDRVC-TIPO-VOCE                     PIC X.               
      *--------------------------------------------------*              
      *    DATA DI IMPIANTO DELLA VOCE CONTABILE                        
      *--------------------------------------------------*              
           05  PDRVC-IMPI-DATA.                                         
               10  PDRVC-IMPI-GG               PIC XX.                  
               10  PDRVC-IMPI-MM               PIC XX.                  
               10  PDRVC-IMPI-AAAA.                                     
                   15  PDRVC-IMPI-AA12         PIC X(2).                
                   15  PDRVC-IMPI-AA34         PIC X(2).                
           SKIP1                                                        
           05  PDRVC-IMPI-NGG                  PIC S9(3) COMP-3.        
           SKIP1                                                        
      *--------------------------------------------------*              
      *    ESTREMI DEL PROVVEDIMENTO DI IMPIANTO                        
      *--------------------------------------------------*              
           05  PDRVC-IMPI-PROVV.                                        
               10  PDRVC-IMPI-PROVV-TIPO           PIC XX.              
               10  PDRVC-IMPI-PROVV-NUM            PIC X(20).           
               10  PDRVC-IMPI-PROVV-DATA.                               
                   15  PDRVC-IMPI-PROVV-GG         PIC XX.              
                   15  PDRVC-IMPI-PROVV-MM         PIC XX.              
                   15  PDRVC-IMPI-PROVV-AAAA.                           
                       20  PDRVC-IMPI-PROVV-AA12   PIC X(2).            
                       20  PDRVC-IMPI-PROVV-AA34   PIC X(2).            
           SKIP1                                                        
      *--------------------------------------------------*              
      *  DATA DI CESSAZIONE DELLA VOCE CONTABILE                        
      *--------------------------------------------------*              
           05  PDRVC-CESS-DATA.                                         
               10  PDRVC-CESS-GG               PIC XX.                  
               10  PDRVC-CESS-MM               PIC XX.                  
               10  PDRVC-CESS-AAAA.                                     
                   15  PDRVC-CESS-AA12         PIC X(2).                
                   15  PDRVC-CESS-AA34         PIC X(2).                
           05  PDRVC-CESS-NGG                  PIC S9(3) COMP-3.        
           SKIP1                                                        
      *--------------------------------------------------*              
      *    ESTREMI DEL PROVVEDIMENTO DI CESSAZIONE                      
      *--------------------------------------------------*              
           05  PDRVC-CESS-PROVV.                                        
               10  PDRVC-CESS-PROVV-TIPO           PIC XX.              
               10  PDRVC-CESS-PROVV-NUM            PIC X(20).           
               10  PDRVC-CESS-PROVV-DATA.                               
                   15  PDRVC-CESS-PROVV-GG         PIC XX.              
                   15  PDRVC-CESS-PROVV-MM         PIC XX.              
                   15  PDRVC-CESS-PROVV-AAAA.                           
                       20  PDRVC-CESS-PROVV-AA12 PIC X(2).              
                       20  PDRVC-CESS-PROVV-AA34 PIC X(2).              
           SKIP1                                                        
      *--------------------------------------------------*              
      *   PARTE CONTABILE                                               
      *--------------------------------------------------*              
           05  PDRVC-IMPORTO-RATA                  PIC S9(9) COMP-3.    
           05  PDRVC-IMPORTO-ULTRATA               PIC S9(9) COMP-3.    
           05  PDRVC-NUMERO-RATE                   PIC S9(5) COMP-3.    
           05  PDRVC-IMPORTO-TOTALE                PIC S9(11) COMP-3.   
           SKIP1                                                        
      *--------------------------------------------------*              
      *  TIPO VARIAZIONE + ESTREMI LIQUIDAZIONE                         
      *--------------------------------------------------*              
           05  PDRVC-TIPO-VARIAZ                   PIC X.               
           05  PDRVC-LIQUID.                                            
               10  PDRVC-LIQUID-ANNO.                                   
                   15  PDRVC-LIQUID-AA12           PIC XX.              
                   15  PDRVC-LIQUID-AA34           PIC XX.              
               10  PDRVC-LIQUID-MESE               PIC XX.              
               10  PDRVC-LIQUID-TMENS              PIC X.               
           SKIP1                                                        
           05  PDRVC-DATA-PREC.                                         
               10  PDRVC-DATA-PREC-GG              PIC XX.              
               10  PDRVC-DATA-PREC-MM              PIC XX.              
               10  PDRVC-DATA-PREC-ANNO.                                
                   15  PDRVC-DATA-PREC-AA12        PIC XX.              
                   15  PDRVC-DATA-PREC-AA34        PIC XX.              
           SKIP1                                                        
           05  PDRVC-TOTVINCO-VARIABILEX       PIC  X(6).               
           05  PDRVC-TOTVINCO-VARIABILE   REDEFINES                     
                   PDRVC-TOTVINCO-VARIABILEX    PIC S9(11) COMP-3.      
           SKIP1                                                        
           05  PDRVC-PIGNOR-DECORR.                                     
               10  PDRVC-PIGNOR-DECORR-GG          PIC XX.              
               10  PDRVC-PIGNOR-DECORR-MM          PIC XX.              
               10  PDRVC-PIGNOR-DECORR-AAAA        PIC XXXX.            
           SKIP1                                                        
           05  PDRVC-PIGNOR-FRAZ.                                       
               10  PDRVC-PIGNOR-FRAZ-NUME          PIC 999.             
               10  PDRVC-PIGNOR-FRAZ-DENOM         PIC 999.             
           SKIP1                                                        
           05  PDRVC-TOTEUROT-VERSATAX             PIC  X(6).           
           05  PDRVC-TOTEUROT-VERSATA     REDEFINES                     
                   PDRVC-TOTEUROT-VERSATAX        PIC S9(11) COMP-3.    
           SKIP1                                                        
           05  PDRVC-PIGNOR-FRANCHIGIAX            PIC  X(6).           
           05  PDRVC-PIGNOR-FRANCHIGIA    REDEFINES                     
                   PDRVC-PIGNOR-FRANCHIGIAX       PIC S9(11) COMP-3.    
           SKIP1          
      *--   NOV 2022 NUOVO CAMPO PERCENTUALE GEST COLLABORATORI
      *              VOCI 4480 E 3041
221129*      05  PDRVC-PERC-COLL                     PIC 9(03).
      *--   MAR 2023 NUOVO CAMPO IMPORTO, CALCOLATO DA ELAB.  
      *              COLLABORATORI
mar23       05  PDRVC-IMPO-CALC-COLL                PIC 9(06).  
mar23       05  PDRVC-FLAG-ELAB-VOCE                PIC X(01).     
mar23       05  FILLER                              PIC X(15).          
221129*      05  FILLER                              PIC X(19).
221129*     05  FILLER                              PIC X(22).    
      *---------------------------------------------------------        
      * NOTE.                                                           
      *                                                                 
      * -TIPO-VARIAZ      'I' -->  IMPIANTO/RIATTIVAZIONE VOCE          
      *                   'C' -->  CESSAZIONE VOCE                      
      *                   'D' -->  MODIFICA DECORRENZA                  
      *                   ' ' -->  CREATA BATCH IN FASE INIZIALE        
      *                            .A PARTIRE DAL FILE AC               
      *---------------------------------------------------------        
      *                                                                 
      * -LIQUID           MENSILITA' NELLA QUALE E' STATA               
      *                   .APPLICATA LA VARIAZIONE                      
      *---------------------------------------------------------        
      *                                                                 
      * -DATA-PREC        DATA PRESENTE NEL RECORD PRECEDENTE           
      *                   .RELATIVO ALLA STESSA VOCE.                   
      *                   E' IMPOSTATO SOLO SE TIPO-VARIAZ = C/D        
      *                                                                 
      *---------------------------------------------------------*       
      * PARTE CONTABILE.                                                
      *                                                                 
      *   NORMALMENTE VIENE IMPOSTATA SOLO PER LE VOCI DELLA TAB4.      
      *   PER LE VOCI DELLE TAB2 E TAB3 L'IMPORTO VIENE PRESO           
      *    DALLE TABELLE RETRIBUTIVE IP/AV.                             
      *                                                                 
      *   TUTTAVIA SONO POSSIBILI L ESEGUENTI ECCEZIONI:                
      *   -------------------------------------------                   
      *                                                                 
      *    A) VOCI TAB2 DI TIPO '1' CON IMPORTI PERSONALI               
      *          (ES. VOCE 2801)                                        
      *       IN QUESTO CASO GLI IMPORTI HANNO I SEGUENTI SIGNIFICATI:  
      *         IMPORTO-RATA       =  LORDO TOTALE DELLA VOCE           
      *         IMPORTO-ULTRATA    =  PARTE IMPONIBILE DELLA VOCE       
      *         NUMERO-RATE        =  ZERO                              
      *         NUMERO-TOTALE      =  ZERO                              
      *---------------------------------------------------------*       
      *                                                                 
      * -CESSANA-DATA     DATA DELLA CESSAZIONE ANAGRAFICA              
      *                   (E' LA STESSA DATA PRESENTE NEL               
      *                    RECORD PDRDP01. VIENE IMPOSTATA DAL          
      *                    PROGRAMMA PDCANA)                            
      *---------------------------------------------------------*       
      *                                                                 
      * -PIGNOR-DECORR   DECORRENZA FRAZIONE PIGNORAMENTO               
      * -PIGNOR-FRAZ     FRAZIONE PER CALCOLO PIGNORAMENTO              
      *                  (NUMERATORE E DONOMINATORE)                    
      * -PIGNOR-FRANCHIGIA   VALORE FRANCHIGIA DA SOTTRARRE             
      *                  (VEDI PDHVAL51)                                
      *---------------------------------------------------------*       
      *                                                                 
      * -COD-OPERAT      SIGLA OPERATORE ULTIMO AGGIORNAMENTO           
      *     VALORI SPECIALI:                                            
      *                  '****'  VARIAZIONI DA FONTI ESTERNE            
      *                           (HANNO UNA SOLA RATA; IL MESE         
      *                           DI IMPIANTO E CESSAZIONE COINCIDE     
      *                           CON AL SESSIONE DI LIQUIDAZIONE)      
      *                           NON SONO MODIFICABILI ON-LINE ??      
      *                           (ES. RITENUTE RISTORANTE 4145)        
      *                           (VEDI PDHSKV05)                       
      *                           DOPO ALCUNI ANNI POTREBBERO ESSERE    
      *                           .ELIMINATE DAGLI ARCHIVI ON-LINE      
      *                           .PER EVITARE L'AUMENTO ECCESSIVO      
      *                           .DELLE DIMENSIONI (ESEGUIRE PDHSKV05  
      *                           . CON PARM-TIPO-ELAB = 'A')           
      *                                                                 
      *                  'BAT2'  VARIAZIONI DA PROCEDURE ESTERNE        
      *                           CON POSSINILE RATEIZZAZIONE           
      *                          (ES. ADDIZIONALI 4202/4217/4268)       
      *                           (VEDI PDHSKV05)                       
      *                                                                 
      *                  'BATC'  GENERICI CARICAMENTI VIA BATCH         
      *                          (ES. INIZIO E FIN ELEGISLATURA)        
      *---------------------------------------------------------*       
           SKIP1                                                        
