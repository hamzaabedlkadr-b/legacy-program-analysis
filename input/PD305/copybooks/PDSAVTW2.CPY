      *--------------------------------------------------------------   
      *    ISTRUZIONI CATALOGATE PER SAVE TWA                           
      *     USARE TRANSLATOR CICS COBOL II                              
      *--------------------------------------------------------------   
           MOVE  1 TO TWCOB-TS-ITEM.                                    
           MOVE  LOW-VALUE TO TWCOB-LLTS.                               
           MOVE  3000      TO TWCOB-LLTS-VALORE.                        
                                                                        
           EXEC  CICS  WRITEQ TS QUEUE(TWCOB-TS-CODA)                   
               FROM(TWCOB-INIZIO) LENGTH(TWCOB-LLTS)                    
               ITEM(TWCOB-TS-ITEM)  END-EXEC.                           
