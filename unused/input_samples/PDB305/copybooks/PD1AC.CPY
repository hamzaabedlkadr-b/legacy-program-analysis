      ****************************************************              
      *   PARAMETRI PER LE ROUTINES  PD1AC/PD2AC                        
      ****************************************************              
         02  PD1AC-LUNGH              PIC S9(4) COMP VALUE +5000.       
         02  PD1AC-DATI.                                                
           03  PD1AC-FUNZIONE           PIC XX.                         
           03  PD1AC-RETURN             PIC X.                          
           SKIP1                                                        
           03  FILLER                          PIC X(6).                
           SKIP1                                                        
           03  PD1AC-CODICE-IP.                                         
               05  PD1AC-CODICE-IP-TIPO        PIC X.                   
               05  PD1AC-CODICE-IP-MATR.                                
                   07  PD1AC-CODICE-IP-MATR1   PIC X.                   
                   07  PD1AC-CODICE-IP-MATR2   PIC X(4).                
               05  PD1AC-CODICE-IP-PAD         PIC X.                   
               05  PD1AC-CODICE-IP-PADN REDEFINES                       
                        PD1AC-CODICE-IP-PAD    PIC 9.                   
               SKIP1                                                    
           03  PD1AC-RIFE-ANNO.                                         
               05  PD1AC-RIFE-ANNO12           PIC XX.                  
               05  PD1AC-RIFE-ANNO34           PIC XX.                  
               SKIP1                                                    
           03  PD1AC-RIFE-DATA.                                         
               05  PD1AC-RIFE-GG               PIC 99.                  
               05  PD1AC-RIFE-MM               PIC 99.                  
               05  PD1AC-RIFE-AAAA             PIC 9999.                
               SKIP1                                                    
           03  PD1AC-SWFILES.                                           
               05  PD1AC-SWFILES-PDKANAG0      PIC X.                   
               05  PD1AC-SWFILES-PDKIPC0       PIC X.                   
               05  PD1AC-SWFILES-PDKAVC0       PIC X.                   
               05  PD1AC-SWFILES-PDKDFCA0      PIC X.                   
               05  FILLER                      PIC X(6).                
           SKIP1                                                        
           03  PD1AC-F15-NUMIMPI5              PIC 99.                  
           03  PD1AC-F15-NUMIMPI6              PIC 99.                  
           03  PD1AC-F15-NUMAVR                PIC 99.                  
           03  PD1AC-F15-INDULT5               PIC 99.                  
           03  PD1AC-F15-INDULT6               PIC 99.                  
           03  PD1AC-F15-INDULTAVR             PIC 99.                  
           SKIP1                                                        
           03  PD1AC-RIFE2-DATA.                                        
               05  PD1AC-RIFE2-GG              PIC 99.                  
               05  PD1AC-RIFE2-MM              PIC 99.                  
               05  PD1AC-RIFE2-AAAA            PIC 9999.                
               SKIP1                                                    
           03  PD1AC-F16-STATO.                                         
               05  PD1AC-F16-STATO-INIZ        PIC X.                   
               05  PD1AC-F16-STATO-FINE        PIC X.                   
               05  PD1AC-F16-STATO-SWCONTINUO  PIC X.                   
               SKIP1                                                    
           03  PD1AC-F16-IMPI-DATA             PIC X(8).                
           03  PD1AC-F16-CESS-DATA             PIC X(8).                
               SKIP1                                                    
           03  PD1AC-F02-CODICI-AVR.                                    
               05  PD1AC-F02-CODAVR   OCCURS 10.                        
                   07  PD1AC-F02-CODAVR-TIPO   PIC X.                   
                   07  PD1AC-F02-CODAVR-MATR   PIC X(5).                
                   07  PD1AC-F02-CODAVR-PAD    PIC X.                   
           SKIP1                                                        
           03  PD1AC-NGIORNI-ATTIVI            PIC 99.                  
           03  PD1AC-TOTALE-GIORNI             PIC 999.                 
           03  PD1AC-TOTALE-GIORNI-NOTAX       PIC 999.                 
           03  PD1AC-SESSLIQ.                                           
               05  PD1AC-SESSLIQ-AAAA          PIC X(4).                
               05  PD1AC-SESSLIQ-MM            PIC X(2).                
               05  PD1AC-SESSLIQ-TMENS         PIC X.                   
ERA68      03  FILLER                          PIC X(67).               
      *---------------------------------------------------------        
      *   DATI IMPIANTO/CESSAZIONE NELL'ANNO DI RIFERIMENTO             
      *---------------------------------------------------------
24I24I     03  PD1AC-STATO-REC                 PIC X.
           03  PD1AC-STATO-RUOLO               PIC X.                   
           03  PD1AC-IMCE-NUMERO               PIC S9(3) COMP-3.        
           03  PD1AC-IMCE-TAB.                                          
               05  PD1AC-IMCE-EL OCCURS 4                               
                        INDEXED BY PD1AC-IIMCE.                         
           SKIP1                                                        
                   07  PD1AC-IMCE-INIZ-TIPO           PIC X.            
                   07  PD1AC-IMCE-INIZ-DATA.                            
                       09  PD1AC-IMCE-INIZ-GG         PIC XX.           
                       09  PD1AC-IMCE-INIZ-MM         PIC XX.           
                       09  PD1AC-IMCE-INIZ-AAAA.                        
                           11  PD1AC-IMCE-INIZ-AA12   PIC XX.           
                           11  PD1AC-IMCE-INIZ-AA34   PIC XX.           
           SKIP1                                                        
                   07  PD1AC-IMCE-FINE-TIPO           PIC X.            
                   07  PD1AC-IMCE-FINE-DATA.                            
                       09  PD1AC-IMCE-FINE-GG         PIC XX.           
                       09  PD1AC-IMCE-FINE-MM         PIC XX.           
                       09  PD1AC-IMCE-FINE-AAAA.                        
                           11  PD1AC-IMCE-FINE-AA12   PIC XX.           
                           11  PD1AC-IMCE-FINE-AA34   PIC XX.           
           SKIP1                                                        
      *---------------------------------------------------              
      * AREA RECORDS LETTI   (MAX. 3000 BYTES)                          
      *----------------------------------------------------             
           03  PD1AC-TABREC-NUMERO               PIC S9(3) COMP-3.      
           SKIP1                                                        
           03  PD1AC-TABREC                      PIC X(3000).           
           SKIP1                                                        
           03  FILLER           REDEFINES PD1AC-TABREC.                 
               05  PD1AC-PDRDP04                 PIC X(300).            
           SKIP1                                                        
           03  FILLER           REDEFINES PD1AC-TABREC.                 
               05  PD1AC-PDRAL01                 PIC X(500).            
           SKIP1                                                        
           03  FILLER           REDEFINES PD1AC-TABREC.                 
               05  PD1AC-PDRDF10                 PIC X(400).            
           SKIP1                                                        
           03  FILLER           REDEFINES PD1AC-TABREC.                 
               05  PD1AC-PDRDP01-EL OCCURS 10    PIC X(130).            
           SKIP1                                                        
           03  FILLER           REDEFINES PD1AC-TABREC.                 
               05  PD1AC-PDRDP02-EL OCCURS 10    PIC X(110).            
           SKIP1                                                        
           03  FILLER           REDEFINES PD1AC-TABREC.                 
               05  PD1AC-PDRDP03-EL OCCURS 10    PIC X(100).            
           SKIP2                                                        
           03  FILLER           REDEFINES PD1AC-TABREC.                 
               05  PD1AC-PDRDP05-EL OCCURS 10    PIC X(100).            
           SKIP2                                                        
           03  FILLER           REDEFINES PD1AC-TABREC.                 
               05  PD1AC-PDRDP06-EL OCCURS 10    PIC X(200).            
           SKIP2                                                        
      *---------------------------------------------------------        
      * AREA DISTRIBUZIONI MENSILI PER ANNO DI RIFERIMENTO              
      *---------------------------------------------------------        
           03  PD1AC-DATI-ANNORIFE               PIC X(1000).           
           SKIP1                                                        
      *---------------------------------------------------------        
      *     DISTRIBUZIONE MENSILE STATO RUOLO PAGAMENTO                 
      *---------------------------------------------------------        
           03  PD1AC-MMDP01  REDEFINES PD1AC-DATI-ANNORIFE.             
               05  PD1AC-MMDP01-EL OCCURS 12                            
                     INDEXED BY PD1AC-IMMDP01.                          
                   07  PD1AC-MMDP01-STATO            PIC X.             
                   07  PD1AC-MMDP01-NGGTOT           PIC 99.            
                   07  PD1AC-MMDP01-NUMASS           PIC 9.             
                   07  PD1AC-MMDP01-TIPOASS1         PIC X.             
                   07  PD1AC-MMDP01-TIPOASS2         PIC X.             
                   07  PD1AC-MMDP01-NGG1             PIC 99.            
                   07  PD1AC-MMDP01-NGG2             PIC 99.            
                   07  PD1AC-MMDP01-ID-SUBTAB1       PIC XX.            
                   07  FILLER                        PIC X(18).         
           SKIP1                                                        
      *---------------------------------------------------------        
      *     DISTRIBUZIONE MENSILE DEL PERIODO CONTRIBUTIVO              
      *---------------------------------------------------------        
           03  PD1AC-MMDP02  REDEFINES PD1AC-DATI-ANNORIFE.             
               05  PD1AC-MMDP02-EL OCCURS 12                            
                     INDEXED BY PD1AC-IMMDP02.                          
           SKIP1                                                        
                   07  PD1AC-MMDP02-PERTOT.                             
                       09  PD1AC-MMDP02-TOT-AA       PIC XX.            
                       09  PD1AC-MMDP02-TOT-MM       PIC XX.            
                       09  PD1AC-MMDP02-TOT-GG       PIC XX.            
           SKIP1                                                        
                   07  PD1AC-MMDP02-PERCAM.                             
                       09  PD1AC-MMDP02-CAM-AA       PIC XX.            
                       09  PD1AC-MMDP02-CAM-MM       PIC XX.            
                       09  PD1AC-MMDP02-CAM-GG       PIC XX.            
           SKIP1                                                        
                   07  PD1AC-MMDP02-PERSEN.                             
                       09  PD1AC-MMDP02-SEN-AA       PIC XX.            
                       09  PD1AC-MMDP02-SEN-MM       PIC XX.            
                       09  PD1AC-MMDP02-SEN-GG       PIC XX.            
           SKIP1                                                        
      *-  PERIODO AL PARLAMENTO EUROPEO                                 
                   07  PD1AC-MMDP02-PERPEU.                             
                       09  PD1AC-MMDP02-PEU-AA       PIC XX.            
                       09  PD1AC-MMDP02-PEU-MM       PIC XX.            
                       09  PD1AC-MMDP02-PEU-GG       PIC XX.            
           SKIP1                                                        
                   07  PD1AC-MMDP02-INIZ-DATA.                          
                       09  PD1AC-MMDP02-INIZ-GG      PIC XX.            
                       09  PD1AC-MMDP02-INIZ-MM      PIC XX.            
                       09  PD1AC-MMDP02-INIZ-AAAA.                      
                           11  PD1AC-MMDP02-INIZ-AA12  PIC XX.          
                           11  PD1AC-MMDP02-INIZ-AA34  PIC XX.          
                   07  FILLER                        PIC X(10).         
      *---------------------------------------------------              
           SKIP1                                                        
      *---------------------------------------------------              
      *    DISTRIBUZIONE MENSILE PERCENTUALE RIVERSIBILITA'             
      *----------------------------------------------------             
           03  PD1AC-MMDP03  REDEFINES PD1AC-DATI-ANNORIFE.             
               05  PD1AC-MMDP03-EL OCCURS 12                            
                     INDEXED BY PD1AC-IMMDP03.                          
           SKIP1                                                        
                   07  PD1AC-MMDP03-PAVR          PIC S9(3)V99 COMP-3.  
                   07  PD1AC-MMDP03-INIZ-DATA.                          
                       09  PD1AC-MMDP03-INIZ-GG     PIC XX.             
                       09  PD1AC-MMDP03-INIZ-MM     PIC XX.             
                       09  PD1AC-MMDP03-INIZ-AAAA.                      
                           11  PD1AC-MMDP03-INIZ-AA12   PIC XX.         
                           11  PD1AC-MMDP03-INIZ-AA34   PIC XX.         
           SKIP1                                                        
           SKIP1                                                        
      *---------------------------------------------------              
      *    DISTRIBUZIONE MENSILE ASSEGNO STRAORDINARIO                  
      *----------------------------------------------------             
           03  PD1AC-MMDP05  REDEFINES PD1AC-DATI-ANNORIFE.             
               05  PD1AC-MMDP05-EL OCCURS 12                            
                     INDEXED BY PD1AC-IMMDP05.                          
           SKIP1                                                        
                   07  PD1AC-MMDP05-NETTO         PIC S9(11)  COMP-3.   
                   07  PD1AC-MMDP05-INIZ-DATA.                          
                       09  PD1AC-MMDP05-INIZ-GG     PIC XX.             
                       09  PD1AC-MMDP05-INIZ-MM     PIC XX.             
                       09  PD1AC-MMDP05-INIZ-AAAA.                      
                           11  PD1AC-MMDP05-INIZ-AA12   PIC XX.         
                           11  PD1AC-MMDP05-INIZ-AA34   PIC XX.         
           SKIP1                                                        
      *----------------------------------------------------             
           03  FILLER                   PIC X(691).                     
      ****************************************************              
      *                                                  *              
      * FUNZIONE:     '00'   OPEN FILES                  *              
      *               '99'   CLOSE FILES                 *              
      *               '01'   DATI ANAGRAFICI (PDRAL01)   *              
      *               '02'   TROVA I CODICI AVR LEGATI                  
      *                        AD UN DANTE CAUSA                        
      *               '03'   INTABELLA RECORDS IMPIANTO                 
      *               '11'   STATO RUOLO PAGAMENTO    .                 
      *                       (DA COMPLETARE CON IL CALCOLO NGGMM)      
      *               '12'   DISTRIBUZION MENSILE PERIODO*              
      *                       CONTRIBUTIVO                              
      *               '13'   DISTRIBUZION MENSILE PERCENT.              
      *                       RIVERSIBILITA'                            
      *               '14'   MODALITA' DI PAGAMENTO                     
      *               '10'   DETRAZIONI FISCALI                         
      *               '15'   RECORDS IMPIANTO IP/AVD/AVR                
      *               '16'   CONTROLLO STATO IN UN PERIODO              
      *                       (DA COMPLETARE)                           
      *               '18'   DISTRIBUZION MENSILE ASSEGNO               
      *                       STRAORDINARIO                             
      *               '19'   RECORD PENSIONE CONTRIB. DP06              
      *                                                  *              
      * RETURN  :     '0'    TUTTO OK                    *              
      *               'E'    SITUAZIONE DI ERRORE        *              
      *                                                  *              
      *                                                  *              
      *------------------------------------------------- *              
      *   FUNZIONI = '00/99'   OPEN/CLOSE                               
      *------------------------------------------------- *              
      *                                                                 
      * FILES GESTITI:  PDKANAG0/PDKIPC0/PDKAVC0/PDKDFCA0               
      *                                                  *              
      *                                                  *              
      *------------------------------------------------- *              
      *   FUNZIONE = '01'                                               
      *------------------------------------------------- *              
      *                                                                 
      * INPUT:   PD1AC-CODICE-IP                                        
      * OUTPUT:  PD1AC-PDRAL01                                          
      *          PD1AC-TABREC-NUMERO                                    
      *                                                  *              
      *------------------------------------------------- *              
      *   FUNZIONE = '02'   TROVA CODICI AVR - NON ESISTE               
      *------------------------------------------------- *              
      *                                                                 
      * INPUT:   PD1AC-CODICE-IP                                        
      * OUTPUT:  PD1AC-F02-CODICI-AVR                                   
      *                                                  *              
      *------------------------------------------------- *              
      *   FUNZIONE = '03'     INTABELLA RECORDS IMPIANTO                
      *------------------------------------------------- *              
      *                                                                 
      *    VENGONO INTABELLATI I RECORDS IMPIANTO                       
      *     IP/AVD/AVR A SECONDA CHE IL CODICE SIA 5/6/7                
      *                                                                 
      * INPUT:   PD1AC-CODICE-IP                                        
      * OUTPUT:  PD1AC-TABREC                                           
      *          PD1AC-TABREC-NUMERO                                    
      *                                                  *              
      *------------------------------------------------- *              
      *   FUNZIONE = '10'                                               
      *------------------------------------------------- *              
      *                                                                 
      * INPUT:   PD1AC-CODICE-IP                                        
      *          PD1AC-RIFE-ANNO                                        
      * OUTPUT:  PD1AC-PDRDF10                                          
      *                                                  *              
      *------------------------------------------------- *              
      *   FUNZIONE = '11'                                               
      *    SI DEVE COMPLETARE IL CALCOLO DEL NGG MENSILE                
      *------------------------------------------------- *              
      *                                                                 
      * INPUT:   PD1AC-CODICE-IP                                        
      *          PD1AC-RIFE-ANNO                                        
      * OUTPUT:  PD1AC-STATO-RUOLO   (S/N)                              
      *          PD1AC-IMCE-TAB                                         
      *          PD1AC-TABREC                                           
      *          PD1AC-TABREC-NUMERO                                    
      *                                                                 
      *          PD1AC-MMDP01:                                          
      *              -STATO    ('1' ATTIVO; '0' NON ATTIVO)             
      *              -NGG      NUMERO GIORNI DA LIQUIDARE               
      *                         (30 SE MESE INTERO)                     
      *              -GIORNI   NUMERO GIORNI EFFETTIVI                  
      *------------------------------------------------- *              
      *   FUNZIONE = '12'   (PERIODO CONTRIBUTIVO PER AV)               
      *------------------------------------------------- *              
      *                                                                 
      * INPUT:   PD1AC-CODICE-IP                                        
      *          PD1AC-RIFE-ANNO                                        
      * OUTPUT:                                                         
      *          PD1AC-TABREC-NUMERO                                    
      *          PD1AC-MMDP02                                           
      *                                                  *              
      *------------------------------------------------- *              
      *   FUNZIONE = '13'   (PERC. RIVERSIBILITA' PER AVR)              
      *------------------------------------------------- *              
      *                                                                 
      * INPUT:   PD1AC-CODICE-IP                                        
      *          PD1AC-RIFE-ANNO                                        
      * OUTPUT:                                                         
      *          PD1AC-TABREC-NUMERO                                    
      *          PD1AC-MMDP03                                           
      *                                                  *              
      *------------------------------------------------- *              
      *   FUNZIONE = '14'   (MODALITA' DI PAGAMENTO)                    
      *------------------------------------------------- *              
      *                                                                 
      * INPUT:   PD1AC-CODICE-IP                                        
      *                                                                 
      * OUTPUT:                                                         
      *          PD1AC-TABREC-NUMERO                                    
      *          PD1AC-PDRDP04                                          
      *                                                  *              
      *------------------------------------------------- *              
      *   FUNZIONE = '15'   (SEQUENZA IMPIANTI IP/AVD/AVR               
      *                     (SOLO VERSIONE BATCH -PD2AC)                
      *------------------------------------------------- *              
      *                                                                 
      * INPUT:   PD1AC-CODICE-IP                                        
      *                                                                 
      * OUTPUT:  PD1AC-TABREC (IN ORDINE CRONOLOGICO DI IMPIANTO        
      *          PD1AC-TABREC-NUMERO                                    
      *                                                  *              
      *------------------------------------------------- *              
      *   FUNZIONE = '17'   (PERC. BASE RIVERS. SENZA MAGGIORAZIONE     
      *------------------------------------------------- *              
      *                                                                 
      * INPUT:   PD1AC-CODICE-IP                                        
      *          PD1AC-RIFE-ANNO                                        
      * OUTPUT:                                                         
      *          PD1AC-TABREC-NUMERO                                    
      *          PD1AC-MMDP03                                           
      *                                                  *              
      *------------------------------------------------- *              
      *   FUNZIONE = '18'   (ASSEGNI STRAORDINARI                       
      *------------------------------------------------- *              
      *                                                                 
      * INPUT:   PD1AC-CODICE-IP                                        
      *          PD1AC-RIFE-ANNO                                        
      * OUTPUT:                                                         
      *          PD1AC-TABREC-NUMERO                                    
      *          PD1AC-MMDP05                                           
      *                                                  *              
      *------------------------------------------------- *              
      *   FUNZIONE = '19'   (PENSIONE CONTRIBUTIVA PDRDP06)             
      *------------------------------------------------- *              
      *                                                                 
      * INPUT:   PD1AC-CODICE-IP                                        
      *          PD1AC-RIFE-ANNO                                        
      * OUTPUT:                                                         
      *          PD1AC-TABREC                                           
      *          PD1AC-TABREC-NUMERO                                    
      *                                                  *              
      *------------------------------------------------- *              
      *   FUNZIONE = 'XX'                                               
      *------------------------------------------------- *              
      *                                                  *              
      *                                                  *              
      ****************************************************              
