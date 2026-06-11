      *******************************************************           
      *       PREVIDENZA DEPUTATI                           *           
      *  AREA COMUNICAZIONE PER ROUTINE SELEZIONE ALFABETICA*           
      *******************************************************           
           05  PDRSELE-LUNG-COMMA           PIC S9(4) COMP              
                     VALUE +100.                                        
           05  PDRSELE-FUNZIONE             PIC XX.                     
           05  PDRSELE-FASE                 PIC X.                      
           05  PDRSELE-RETURN               PIC X.                      
           05  PDRSELE-NOMECODA.                                        
               10  PDRSELE-NOMETERM         PIC X(4).                   
               10  PDRSELE-KOST             PIC X(4).                   
           05  PDRSELE-NOME-PGM             PIC X(8).                   
           05  PDRSELE-MESS                 PIC X(70).                  
           05  PDRSELE-NELEM-CODA           PIC 9(2).                   
           05  FILLER                       PIC X(4).                   
               SKIP1                                                    
      *******************************************************           
      *   PDRSELE-FUNZIONE                                              
      *                                                                 
      *        '01'  -->  SELEZIONE ALFABETICA                          
      *                                                                 
      *   PDRSELE-RETURN                                                
      *                                                                 
      *         '0'  -->  TUTTO OK                                      
      *         '9'  -->  SELEZIONE NON EFFETTUATA PER MANCANZA DI      
      *                   SPAZIO DISPONIBILE                            
      *         'E'  -->  SITUAZIONE DI ERRORE GRAVE                    
      *                                                                 
      *---------------------------------------------------------        
      *    -NELEM-CODA    NUMERO DI CHIAVI PRESENTI IN OGNI RECORD TS   
      *******************************************************           
              SKIP1                                                     
