      *-------------------------------------------  02-10-2015  ----*  
      *  MODULO STANDARD  GESTIONE ABEND                            *   
      *-------------------------------------------------------------*   
      *  per utilizzare la routine impostare i seguenti campi:      *   
      *                                                             *   
      *    . WABEND-CODE    PIC X(4)    codice abend 
      *                                                             *   
      *-------------------------------------------------------------*   
                                                                        
      *    RICHIEDI CORE DUMP
           EXEC CICS SYNCPOINT ROLLBACK END-EXEC
           EXEC CICS LINK PROGRAM('TE0CDUMP') COMMAREA(WABEND-CODE) 
               LENGTH(4) END-EXEC.                                    
                                                                        
      *    RICHIEDI ABEND CICS                                         
           EXEC CICS ABEND ABCODE(WABEND-CODE) END-EXEC.              
                                                                        
