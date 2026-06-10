      *************************************************************     
      * AREA DI COMUNICAZIONE CON LE ROUTINES PD1VOCI/PD2VOCI           
      *----------------------------------------------------------       
      *                                                                 
      *  PER CHIAMARE LA ROUTINE:                                       
      *                                                                 
      *    A) WORKING-STORAGE                                           
      *         01 WPD1VOCI.                                            
      *            COPY PD1VOCI.                                        
      *                                                                 
      *    B) PROCEDURE DIVISION.                                       
      *       EXEC CICS LINK(PD1VOCI) COMMAREA(WPD1VOCI)                
      *            LENGTH(PD1VOCI-LENGH)  END-EXEC.                     
      *************************************************************     
      * 02  PD1VOCI-LUNGH               PIC S9(4) COMP                  
      *              VALUE +32000.                                      
        02  PD1VOCI-DATI                PIC X(32000). 
      *  02 PD1VOCI-DATI          PIC X(64000).
        02  FILLER REDEFINES   PD1VOCI-DATI.                            
           03  PD1VOCI-FUNZIONE         PIC XX.                         
           03  PD1VOCI-RETURN           PIC X.                          
           SKIP1                                                        
           03  PD1VOCI-CODDIP.                                          
               05  PD1VOCI-CODDIP-TIPO         PIC X.                   
               05  PD1VOCI-CODDIP-MATR         PIC X(5).                
               05  PD1VOCI-CODDIP-PAD          PIC X.                   
               05  PD1VOCI-CODDIP-PADN  REDEFINES                       
                      PD1VOCI-CODDIP-PAD       PIC 9.                   
           SKIP1                                                        
           03  PD1VOCI-LIQUID1.                                         
               05  PD1VOCI-LIQUID1-ANNO.                                
                   07  PD1VOCI-LIQUID1-AA12    PIC XX.                  
                   07  PD1VOCI-LIQUID1-AA34    PIC XX.                  
               05  PD1VOCI-LIQUID1-MESE        PIC XX.                  
               05  PD1VOCI-LIQUID1-TIPO        PIC X.                   
           SKIP1                                                        
           03  PD1VOCI-LIQUID2.                                         
               05  PD1VOCI-LIQUID2-ANNO.                                
                   07  PD1VOCI-LIQUID2-AA12    PIC XX.                  
                   07  PD1VOCI-LIQUID2-AA34    PIC XX.                  
               05  PD1VOCI-LIQUID2-MESE        PIC XX.                  
               05  PD1VOCI-LIQUID2-TIPO        PIC X.                   
           SKIP1                                                        
           03  PD1VOCI-COD-VOCE                PIC X(4).                
           03  PD1VOCI-TIPO-VOCE               PIC X.                   
           03  PD1VOCI-TIPO-ESTRA              PIC X.                   
           03  PD1VOCI-TIPO-GEST               PIC XX.                  
           03  PD1VOCI-TIPO-VARIAZ             PIC X.                   
           SKIP1                                                        
           03  PD1VOCI-CESS-DATA.                                       
               05  PD1VOCI-CESS-GG             PIC XX.                  
               05  PD1VOCI-CESS-MM             PIC XX.                  
               05  PD1VOCI-CESS-AAAA.                                   
                   07  PD1VOCI-CESS-AA12       PIC XX.                  
                   07  PD1VOCI-CESS-AA34       PIC XX.                  
           SKIP1                                                        
           03  PD1VOCI-CESS-NGG                PIC S99.                 
           SKIP1                                                        
           03  PD1VOCI-PDRTIP01                  PIC X(350).            
           03  PD1VOCI-PDRVC                     PIC X(200).            
           03  PD1VOCI-SWFILES.                                         
               05  PD1VOCI-SWFILES-PDKTIP0      PIC X.                  
               05  PD1VOCI-SWFILES-PDKVCIP0     PIC X.                  
               05  PD1VOCI-SWFILES-PDKVCAV0     PIC X.                  
               05  FILLER                       PIC X(7).               
           SKIP1                                                        
           03  PD1VOCI-IMPI-DATA.                                       
               05  PD1VOCI-IMPI-GG             PIC XX.                  
               05  PD1VOCI-IMPI-MM             PIC XX.                  
               05  PD1VOCI-IMPI-AAAA.                                   
                   07  PD1VOCI-IMPI-AA12       PIC XX.                  
                   07  PD1VOCI-IMPI-AA34       PIC XX.                  
           SKIP1                                                        
           03  PD1VOCI-CESSPREC-DATA           PIC X(8).                
           03  PD1VOCI-IMPI-NGG                PIC S99.                 
           03  PD1VOCI-SW-STESSA-SESSIONE      PIC X.                   
           03  PD1VOCI-PROG-VOCE               PIC 999.                 
           SKIP1                                                        
      *---------------------------------------------------              
           03  PD1VOCI-LIQUID3.                                         
               05  PD1VOCI-LIQUID3-ANNO.                                
                   07  PD1VOCI-LIQUID3-AA12    PIC XX.                  
                   07  PD1VOCI-LIQUID3-AA34    PIC XX.                  
               05  PD1VOCI-LIQUID3-MESE        PIC XX.                  
               05  PD1VOCI-LIQUID3-TIPO        PIC X.                   
           03  FILLER                          PIC X(161).              
           SKIP1                                                        
      *---------------------------------------------------              
      * TABELLA VOCI CONTABILI                                          
      *  TABVOX-MODAGG:  ' ' AGG.NORMALE; 'A' AUTOMATICO(PDCANA)        
      *----------------------------------------------------             
           03  PD1VOCI-TABVOX-NUMERO            PIC S9(5) COMP-3.       
           03  PD1VOCI-TABVOX.  
               05  PD1VOCI-TABVOX-EL   OCCURS 350.            
      *         05  PD1VOCI-TABVOX-EL   OCCURS 500.                     
                   07   PD1VOCI-TABVOX-CODVOX       PIC  X(4).          
                   07   PD1VOCI-TABVOX-TIPVOX       PIC  X.             
                   07   PD1VOCI-TABVOX-PROGVOX      PIC  999.           
      *----------------------------------------------------             
      *            07   PD1VOCI-TABVOX-DESCRIZ      PIC  X(37).         
                   07   PD1VOCI-TABVOX-DESCRIZ      PIC  X(33).         
                   07   PD1VOCI-TABVOX-INIZ-NGG     PIC  99.            
                   07   PD1VOCI-TABVOX-FINE-NGG     PIC  99.            
      *----------------------------------------------------             
                   07   PD1VOCI-TABVOX-INIZ         PIC  X(8).          
                   07   PD1VOCI-TABVOX-FINE         PIC  X(8).          
                   07   PD1VOCI-TABVOX-IRATA        PIC  S9(9) COMP-3.  
                   07   PD1VOCI-TABVOX-IULTRATA     PIC  S9(9) COMP-3.  
                   07   PD1VOCI-TABVOX-LIQUID.                          
                        09   PD1VOCI-TABVOX-ANNO.                       
                             11  PD1VOCI-TABVOX-AA12    PIC  X(2).      
                             11  PD1VOCI-TABVOX-AA34    PIC  X(2).      
                        09   PD1VOCI-TABVOX-MESE    PIC  XX.            
                        09   PD1VOCI-TABVOX-TMENS   PIC  X.             
                   07   PD1VOCI-TABVOX-TIPVAR       PIC  X.             
                   07   PD1VOCI-TABVOX-MODAGG       PIC  X.
22N14I*            07   PD1VOCI-TABVOX-PERC-COLL    PIC  S9(3) COMP-3.
22N14C*            07   FILLER                      PIC  X(2).
23D12I*  LA PERC-COLL E' STATA SOSTITUITA DA IMPO-CALC-COLL NELLA
23D12I*  GESTIONE DEI COLLABORATORI
23D12I             07   PD1VOCI-TABVOX-IMPO-CALC-COLL PIC S9(7) COMP-3.
           SKIP1                                                        
           03  PD1VOCI-TABMATR REDEFINES PD1VOCI-TABVOX.                
               05  PD1VOCI-TABMATR-EL  OCCURS 2000.                     
                   07   PD1VOCI-TABMATR-CODDIP      PIC  X(7).          
                   07   PD1VOCI-TABMATR-PROG-VOCE   PIC  9(3).          
           SKIP1                
      ****************************************************              
      *                                                                 
      * FUNZIONE:     '00'   OPEN FILES (SOLO BATCH)                    
      *               '99'   CLOSE FILES (SOLO BATCH)                   
      *               '01'   LEGGE UN RECORD VOCE (PDRTIP01)            
      *               '02'   ESTRAE VOCI TABELLARI                      
      *               '11'   ESTRAE VOCI PERSONALI                      
      *               '12'   ESTRAE VARIAZIONI CONTABILI                
      *               '13'   ESTRAE MATRICOLE CON UNA DATA VOCE         
      *               '21'   CESSAZIONE VOCI CONTABILI                  
      *                                                                 
      *------------------------------------------------- *              
      * RETURN  :     '0'    TUTTO OK                    *              
      *               'E'    SITUAZIONE DI ERRORE        *              
      *                                                                 
      *------------------------------------------------- *              
      *   FUNZIONI = '00/99'   OPEN/CLOSE                               
      *------------------------------------------------- *              
      *------------------------------------------------- *              
      *   FUNZIONE = '01'                                               
      *                                                                 
      *   LETTURA DI UN  RECORD VOCE CONTABILE NELLE TABELLE IP/AV      
      *                                                                 
      *                                                                 
      * INPUT:   PD1VOCI-LIQUID-ANNO                                    
      *          PD1VOCI-CODICE-VOCE                                    
      *                                                                 
      * OUTPUT:  PD1VOCI-PDRTIP01                                       
      *---------------------------------------------------------------- 
      *                                                                 
      *   FUNZIONE = '02'                                               
      *                                                                 
      *  ESTRAE UN INSIEME DI VOCI DALLE TABELLE IP/AV                  
      *                                                                 
      *  INPUT:  PD1VOCI-CODDIP          CODICE DIPENDENTE              
      *          PD1VOCI-LIQUID1         MENSILITA'                     
      *          PD1VOCI-TIPO-VOCE          ('0' TUTTE; ALTRIMENTI      
      *                                       VALE 1/2/3/4/7).          
      *          PD1VOCI-TIPO-ESTRA      TIPO ESTRAZIONE: T --> TUTTE   
      *                                  'A' SOLO VOCI ATTIVE           
      *          PD1VOCI-TIPO-GEST       TIPO GESTIONE: '00' TUTTI;     
      *                                  ALTR. 'TIPGEST' IN PDTAB01     
      *                                                                 
      * OUTPUT:  PD1VOCI-TABVOX-NUMERO                                  
      *          PD1VOCI-TABVOX                                         
      *                                                                 
      *-------------------------------------------------------------    
      *   FUNZIONE = '10'                                               
      *                                                                 
      *  LEGGE UN RECORD VOCE CONTABILE (PDRVC) SUGLI ARCHIVI           
      *   PDKVCIP / PDKVCAV                                             
      *                                                                 
      *  INPUT:  PD1VOCI-CODDIP           CODICE DIPENDENTE             
      *          PD1VOCI-COD-VOCE         CODICE VOCE (= ZERO SE TUTTE) 
      *          PD1VOCI-PROG-VOCE        TIPO VARIAZIONE               
      *                                                                 
      * OUTPUT:  PD1VOCI-PDRVC                                          
      *                                                                 
      *                                                                 
      *-------------------------------------------------------------    
      *   FUNZIONE = '11'                                               
      *                                                                 
      *  ESTRAE UN INSIEME DI VOCI PERSONALI  DAGLI ARCHIVI             
      *   PDKVCIP / PDKVCAV                                             
      *                                                                 
      *  INPUT:  PD1VOCI-CODDIP           CODICE DIPENDENTE             
      *          PD1VOCI-COD-VOCE         CODICE VOCE (= ZERO SE TUTTE) 
      *          PD1VOCI-TIPO-VARIAZ      TIPO VARIAZIONE               
      *          PD1VOCI-LIQUID1          MENSILITA' CORRENTE SE        
      *                                   .FUNZIONE NON = 'V'           
      *          PD1VOCI-TIPO-VOCE          ('0' TUTTE; ALTRIMENTI      
      *                                       VALE 1/2/3/4/7).          
      *                                                                 
      * OUTPUT:  PD1VOCI-TABVOX-NUMERO                                  
      *          PD1VOCI-TABVOX                                         
      *                                                                 
      *-------------------------------------------------------------    
      *   FUNZIONE = '12'                                               
      *                                                                 
      *  ESTRAE UN INSIEME DI VARIAZIONI CONTABILI DAGLI ARCHIVI        
      *   PDKVCIP / PDKVCAV                                             
      *                                                                 
      *  INPUT:  PD1VOCI-CODDIP           CODICE DIPENDENTE             
      *          PD1VOCI-COD-VOCE         CODICE VOCE (= ZERO SE TUTTE) 
      *          PD1VOCI-LIQUID1          MENSILITA' INIZIALE           
      *                                                                 
      * OUTPUT:  PD1VOCI-TABVOX-NUMERO                                  
      *          PD1VOCI-TABVOX                                         
      *                                                                 
      *-------------------------------------------------------------    
      *   FUNZIONE = '13'                                               
      *                                                                 
      *  ESTRAE UN INSIEME DI MATRICOLE CHE HANNO UNA VOCE              
      *                                                                 
      *  INPUT:  PD1VOCI-CODDIP-TIPO      TIPO DIPENDENTE               
      *                                   ('5' SE IP; '6' SE AV)        
      *          PD1VOCI-COD-VOCE         CODICE VOCE (= ZERO SE TUTTE) 
      *          PD1VOCI-LIQUID1          MENSILITA' INIZIALE           
      *          PD1VOCI-LIQUID2          MENSILITA' FINALE             
      *          PD1VOCI-IMPI-DATA        DATA IMPIANTO VOCE            
      *          PD1VOCI-CESS-DATA        DATA CESSAZIONE VOCE          
      *                                                                 
      * OUTPUT:  PD1VOCI-TABVOX-NUMERO                                  
      *          PD1VOCI-TABMATR                                        
      *                                                                 
      *-------------------------------------------------------------    
      *   FUNZIONE = '21'                                               
      *                                                                 
      *  CESSAZIONE DELLE VOCI CONTABILI DI UN SOGGETTO                 
      *                                                                 
      *  INPUT:  PD1VOCI-CODDIP           CODICE DIPENDENTE             
      *          PD1VOCI-CESS-DATA        DATA CESSAZIONE               
      *          PD1VOCI-LIQUID1          MENSILITA' ?????              
      *                                                                 
      *-------------------------------------------------------------    
      *  NOTE SUI PARAMETRI.                                            
      *                                                                 
      *   1) PD1VOCI-LIQUID1                                            
      *                                                                 
      *     1.1) SE ANNO = 'TTTT'   TUTTE LE VOCI                       
      *     1.2) SE = '1991  '      VOCI ATTIVE NEL 1991                
      *     1.3) SE = '199105'      SOLO VOCI ATTIVE NEL 199195         
      *                                                                 
      *                                                                 
      ***************************************************************   
