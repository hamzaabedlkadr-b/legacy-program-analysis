      *******************************************************           
      *       PREVIDENZA DEPUTATI - SCHEDA PERSONALE        *           
      *-----------------------------------------------------*           
      *  RECORD DA (DATI ANAGRAFICI)     LRECL = 500        *           
      *  TREC=01   CHIAVE = (1 , 12)     -----------        *           
      *                                                     *           
      *-----------------------------------------------------*           
      *******************************************************           
         05 PDRAL-DA.                                                   
            10 RECORD-DA-TP.                                            
               15  DA-TIPO-DIP              PIC X.                      
           SKIP1                                                        
               15  DA-CHIAVE.                                           
                   20  DA-CHIAVE-MATR       PIC 9(5).                   
                   20  DA-CHIAVE-PAD        PIC 9.                      
                   20  DA-CHIAVE-TREC       PIC 99.                     
                   20  FILLER               PIC X(4).                   
               15  FILLER  REDEFINES DA-CHIAVE.                         
                   20  DA-CHIAVE-MATRX.                                 
                       25  DA-CHIAVE-MATRX1 PIC X.                      
                       25  DA-CHIAVE-MATRX2 PIC X(4).                   
                   20  DA-CHIAVE-PADX       PIC X.                      
                   20  DA-CHIAVE-TRECX      PIC XX.                     
                   20  FILLER               PIC X(4).                   
           SKIP1                                                        
               15  DA-STATO-REC             PIC X.                      
               15  DA-COD-OPERAT            PIC X(4).                   
               15  DA-ULTAGG-DATA.                                      
                   20  DA-ULTAGG-GG         PIC 99.                     
                   20  DA-ULTAGG-MM         PIC 99.                     
                   20  DA-ULTAGG-AA         PIC 99.                     
           SKIP1                                                        
               15  DA-POSIZIONE             PIC X.                      
      *--------------------------------------------*                    
      *      DATI ANAGRAFICI                       *                    
      *--------------------------------------------*                    
               15  DA-COGNOME               PIC X(30).                  
               15  DA-NOME                  PIC X(30).                  
           SKIP1                                                        
               15  DA-ESPANS-CN             PIC X(50).                  
               15  FILLER  REDEFINES  DA-ESPANS-CN.                     
                   20  DA-ESPANS-TITOLO     PIC X(5).                   
                   20  FILLER               PIC X(45).                  
           SKIP1                                                        
               15  DA-CODFIS                PIC X(16).                  
               15  DA-RELAZ-PARENT          PIC X.                      
               15  DA-SESSO                 PIC X.                      
               15  DA-COND-PROFESS          PIC X.                      
               15  DA-TIT-STUDIO            PIC X.                      
               15  DA-STATO-CIV             PIC X.                      
           SKIP1                                                        
               15  DA-VAR-DATA.                                         
                   20  DA-VAR-GG            PIC 99.                     
                   20  DA-VAR-MM            PIC 99.                     
                   20  DA-VAR-AA            PIC 9(4).                   
           SKIP1                                                        
               15  DA-DECESSO-DATA.                                     
                   20  DA-DECESSO-GG        PIC 99.                     
                   20  DA-DECESSO-MM        PIC 99.                     
                   20  DA-DECESSO-AA        PIC 9(4).                   
           SKIP1                                                        
               15  DA-NASCITA-DATA.                                     
                   20  DA-NASCITA-GG        PIC 99.                     
                   20  DA-NASCITA-MM        PIC 99.                     
                   20  DA-NASCITA-AA        PIC 9(4).                   
           SKIP1                                                        
               15  DA-NASCITA-COMUNE        PIC X(30).                  
               15  DA-NASCITA-PROV          PIC XX.                     
      *--------------------------------------------*                    
      *      DATI SULLA RESIDENZA                  *                    
      *--------------------------------------------*                    
               15  DA-RESID-PRESSO          PIC X(39).                  
               15  DA-RESID-NTELEF          PIC X(10).                  
               15  FILLER                   PIC X.                      
               15  DA-RESID-INDIR           PIC X(35).                  
               15  DA-RESID-FILLER          PIC X(5).                   
               15  DA-RESID-COMUNE          PIC X(30).                  
               15  DA-RESID-PROV            PIC XX.                     
               15  DA-RESID-CAP             PIC X(5).                   
               15  DA-RESID-PREFIX          PIC X(4).                   
      ****     15  DA-RESID-NTELEF          PIC X(7).                   
               15  DA-RESID-REGIONE         PIC X(2).                   
               15  FILLER                   PIC X(5).                   
      *--------------------------------------------*                    
      *      DATI SUL DOMICILIO                    *                    
      *--------------------------------------------*                    
               15  DA-DOMIC-PRESSO          PIC X(39).                  
               15  DA-DOMIC-NTELEF          PIC X(10).                  
               15  FILLER                   PIC X.                      
               15  DA-DOMIC-INDIR           PIC X(35).                  
               15  DA-DOMIC-FILLER          PIC X(5).                   
               15  DA-DOMIC-COMUNE          PIC X(30).                  
               15  DA-DOMIC-PROV            PIC XX.                     
               15  DA-DOMIC-CAP             PIC X(5).                   
               15  DA-DOMIC-PREFIX          PIC X(4).                   
      ****     15  DA-DOMIC-NTELEF          PIC X(7).                   
               15  DA-DOMIC-REGIONE         PIC X(2).                   
               15  FILLER                   PIC X(5).                   
               SKIP1                                                    
               15  DA-FLAG-INDIR            PIC X.                      
      *                                                                 
               15  DA-ATTESA-FITTIZIA       PIC X.                      
           SKIP1                                                        
      *---------------------------------------------------------        
      * SESSIONE ULTIMO AGGIORNAMENTO                                   
      *---------------------------------------------------------        
               15  DA-SESSIONE.                                         
                   20  DA-SESSIONE-ANNO     PIC X(4).                   
                   20  DA-SESSIONE-MESE     PIC X(2).                   
                   20  DA-SESSIONE-TMENS    PIC X.                      
           SKIP1                                                        
               15  FILLER                   PIC X(03).                  
      *---------------------------------------------------------*       
      *   NOTE RELATIVE AL RECORD DA.                           *       
      *                                                         *       
      *---------------------------------------------------------*       
      *   DA-STATO-REC       VALE SEMPRE  '1'                           
      *---------------------------------------------------------*       
      * TIPO-DIP    USATO PER STAMPA ETICHETTE BATCH                    
      *              (5/6/7/A)                                          
      *                                                         *       
      *---------------------------------------------------------*       
      * ESPANS-CN   ESPANSIONE NOME PER AVENTI DIRITTO (ES. VED. XX)    
      *                (TIPO POSIZIONE = 'A')                   *       
      *                                                                 
      * ESPANS-TITOLO  TITOLO PER GIUDICI CORTE COSTITUZIONALE          
      *                (TIPO POSIZIONE = 'G')                   *       
      *---------------------------------------------------------*       
      * STATO-REC   ('1' ATTIVO; '0' CANCELLATO)                        
      *                                                         *       
      * POSIZIONE:  ('P' PARLAMENTARE; 'A' AVENTE DIRITTO;      *       
      *              'G' GIUDICE CORTE COSTITUZ.                        
      *                                                         *       
      * RELAZ-PARENT:  VEDI PDTAB01 ( TAB. RELPA)               *       
      *                                                         *       
      * SESSO :        ('M' ; 'F')                              *       
      *                                                         *       
      * COND-PROFESS:  VEDI PDTAB01 (TAB. CONDP)                *       
      *                                                         *       
      * TIT-STUDIO:    VEDI PDTAB01 (TAB. TITST)                *       
      *                                                         *       
      * STATO-CIV:     VEDI PDTAB01 (TAB. STACV)                *       
      *                                                         *       
      * DA-FLAG-INDIR  VIENE IMPOSTATO A 'R' SOLO NEL CASO      *       
      *                SIANO PRESENTI SIA IL DOMICILIO CHE LA   *       
      *                RESIDENZA E SI VOGLIANO UTILIZZARE GLI   *       
      *                ELEMENTI DELLA RESIDENZA. NEGLI ALTRI    *       
      *                CASI E' SEMPRE = BLANK.                  *       
      *-------------------------------------------------------- *       
      * DA-NASCITA-PROV   PROVINCIA DI NASCITA(SE NASCITA IN ITALIA)    
      *                   CODICE STATO ESTERO (TABELLA NAZIO)           
      *                   '**'  SE NATO IN UNA EX-COLONIA (ES. ISTRIA)  
      *-------------------------------------------------------- *       
      * DA-ATTESA-FITTIZIA   NORMALMENTE VALE SPAZIO                    
      *                VIENE IMPOSTATO AD 'S'  PER GLI EX-DEPUTATI      
      *                IN ATTESA CHE PERO' NON POTRANNO MAI AVERE       
      *                L'ASSEGNO VITALIZIO; AD ESEMPIO I DEPUTATI       
      *                CHE NON HANNO UN SUFFICIENTE PERIODO CONTRIB.    
      *                E NON POSSONO RISCATTARE I PERIODI MANCANTI.     
      *---------------------------------------------------------*       
      * DA-SESSIONE          SESSIONE DI INSER./AGGIORN. RECORD         
      *---------------------------------------------------------*       
           SKIP1                                                        
