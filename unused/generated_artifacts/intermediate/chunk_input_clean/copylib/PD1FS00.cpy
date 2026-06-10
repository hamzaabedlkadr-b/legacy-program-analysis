      ****************************************************              
      *   PARAMETRI PER LA ROUTINE  PD1FS00                             
      ****************************************************              
           03  PD1FS00-LUNGH            PIC S9(4) COMP VALUE +4000.     
           03  PD1FS00-FUNZIONE         PIC XX.                         
           03  PD1FS00-RETURN           PIC X.                          
          SKIP1                                                         
           03  PD1FS00-MODACC-SISTEMI.                                  
               05  PD1FS00-MODACC-SISTOT  PIC X.                        
               05  PD1FS00-MODACC-SP      PIC X.                        
               05  PD1FS00-MODACC-IP      PIC X.                        
               05  PD1FS00-MODACC-AV      PIC X.                        
               05  PD1FS00-MODACC-TB      PIC X.                        
               05  FILLER                 PIC X(5).                     
           SKIP1                                                        
           03  PD1FS00-F02-SISTEMA      PIC X(2).                       
           03  PD1FS00-F02-PGM          PIC X(8).                       
           03  PD1FS00-F02-FUNZ         PIC X.                          
           03  PD1FS00-F02-LIVE-OPER    PIC X.                          
           03  PD1FS00-F02-MODACC       PIC X.                          
           03  PD1FS00-F02-GRADO        PIC X.                          
           03  PD1FS00-F02-MSG          PIC X(70).                      
           03  PD1FS00-F02-ANNO         PIC X(2).                       
           03  PD1FS00-F02-MESE         PIC X(2).                       
           SKIP1                                                        
           03  PD1FS00-SESS.                                            
               05  PD1FS00-SESS-SISTEMA    PIC XX.                      
               05  PD1FS00-SESS-ANNO.                                   
                   07  PD1FS00-SESS-AA12   PIC XX.                      
                   07  PD1FS00-SESS-AA34   PIC XX.                      
               05  PD1FS00-SESS-MESE       PIC XX.                      
               05  PD1FS00-SESS-TMENS      PIC X.                       
               05  PD1FS00-SESS-FLAG       PIC X.                       
           03  PD1FS00-F02-SIGLA-OPER      PIC X(4).                    
           03  PD1FS00-CATEG-UTENTE        PIC X(2).                    
           03  PD1FS00-SESS-FLAG-ASI       PIC X.                       
           03  FILLER                      PIC X(277).                  
      *---------------------------------------------------              
      * AREA RECORDS LETTI                                              
      *----------------------------------------------------             
           03  PD1FS00-TABREC-NUMERO           PIC S9(3) COMP-3.        
           03  PD1FS00-TABREC                  PIC X(3000).             
           03  FILLER           REDEFINES PD1FS00-TABREC.               
               05  PD1FS00-PDRSIS02            PIC X(500).              
           03  FILLER           REDEFINES PD1FS00-TABREC.               
               05  PD1FS00-PDRSIS10            PIC X(180).              
      ****************************************************              
      *                                                  *              
      * FUNZIONE:                                                       
      *               '01'   MODALITA' ACCESSO AI SISTEMI*              
      *               '02'   CONTROLLO OPERAZIONE SCELTA                
      *               '03'   TROVA ULTIMA SESSIONE                      
      *               '04'   ??                                         
      *                                                  *              
      * RETURN  :     '0'    TUTTO OK                    *              
      *               '1'    FUNZIONE NON POSSIBILE      *              
      *               '2'    TUTTO OK                    *              
      *               'E'    SITUAZIONE DI ERRORE        *              
      *                                                  *              
      *                                                  *              
      *------------------------------------------------- *              
      *   FUNZIONE = '01'                                               
      *------------------------------------------------- *              
      *                                                                 
      * INPUT:   PD1FS00-CODICE-IP                                      
      * OUTPUT:  PD1FS00-PDRAL01                                        
      *          PD1FS00-TABREC-NUMERO                                  
      *                                                  *              
      *------------------------------------------------- *              
      *   FUNZIONE = '02'                                               
      *------------------------------------------------- *              
      *                                                                 
      * INPUT:   PD1FS00-F02-PGM                                        
      *          PD1FS00-F02-FUNZ                                       
      * OUTPUT:  PD1FS00-RETURN   '0' OK; '1' NON OSSIBILE              
      *          PD1FS00-F02-MODACC                                     
      *          PD1FS00-F02-GRADO                                      
      *          PD1FS00-F02-MSG                                        
      *                                                  *              
      *------------------------------------------------- *              
      *   FUNZIONE = '03' ULTIMA SESSIONE                               
      *------------------------------------------------- *              
      *                                                                 
      * INPUT:   PD1FS00-SESS-SISTEMA                                   
      * OUTPUT:  PD1FS00-RETURN      '0' OK; ALTRIMENTI ERRORE          
      *          PD1FS00-SESS-ANNO                                      
      *          PD1FS00-SESS-MESE                                      
      *          PD1FS00-SESS-TMENS                                     
      *          PD1FS00-SESS-FLAG                                      
      *                                                  *              
      ****************************************************              
