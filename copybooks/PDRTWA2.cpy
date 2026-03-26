       01  PDRTWA2.                                                     
      ***********************************************************       
      *          TWA PREVIDENZA DEPUTATI (COBOL)                *       
      *          -----------------------                        *       
      *                                                         *       
      *   ++++++++++++++++++++++++++++++++++++++++++++++++      *       
      *   NB. OGNI VARIAZIONE VA' RIPORTATA ANCHE SULLA         *       
      *   --  VERSIONE ASSEMBLER 'PDDSTWA'.                     *       
      *   ++++++++++++++++++++++++++++++++++++++++++++++++      *       
      *                                                         *       
      *                                                         *       
      * LA TWA E' SUDDIVISA IN 3 PARTI:                         *       
      *      1) BYTES 1-1000      DATI DI PASSAGGIO             *       
      *      2) BYTES 1001-2000   SALVATAGGIO RECORDS           *       
      *      3) BYTES 2001-3000   DATI DI PASSAGGIO             *       
      ***********************************************************       
         03  TWCOB-PARTE-PRIMA              PIC X(1000).                
         03  FILLER REDEFINES TWCOB-PARTE-PRIMA.                        
             05  TWCOB-LLTS.                                            
                 07   TWCOB-LLTS-VALORE     PIC S9(4) COMP.             
                 07   FILLER                PIC X(2).                   
      *                        INIZIO PARTE DATI                        
           04  TWCOB-INIZIO.                                            
             05  TWCOB-INDCSA-SISTEMA       PIC S9(8) COMP.             
             05  TWCOB-DISPLCWA-APPLIC      PIC S9(8) COMP.             
             05  TWCOB-INDCWA-APPLIC        PIC S9(8) COMP.             
             05  TWCOB-NOME-PGM             PIC X(8).                   
             05  TWCOB-FUNZIONE             PIC X.                      
             05  TWCOB-FASE                 PIC X.                      
             05  TWCOB-CODICE-DIP           PIC X(7).                   
             05  FILLER REDEFINES  TWCOB-CODICE-DIP.                    
                 07  TWCOB-TIPO-DIP         PIC X.                      
                 07  TWCOB-SP-MATR.                                     
                     09  TWCOB-SP-MATR1     PIC X.                      
                     09  TWCOB-SP-MATR2     PIC X(4).                   
                 07  TWCOB-SP-PAD           PIC X.                      
                 07  TWCOB-SP-PADN REDEFINES                            
                        TWCOB-SP-PAD        PIC 9.                      
             05  TWCOB-COGNOME              PIC X(30).                  
             05  TWCOB-NOME                 PIC X(30).                  
             05  TWCOB-OPER-SIGLA           PIC X(4).                   
             05  TWCOB-OPER-FLAG            PIC X.                      
             05  TWCOB-TS-ITEM              PIC S9(4) COMP.             
             05  TWCOB-TS-CODA.                                         
                 07  TWCOB-TS-CODA-TERMID   PIC X(4).                   
                 07  TWCOB-TS-CODA-TRANSID  PIC X(4).                   
             SKIP1                                                      
             05  TWCOB-TIPO-VERS-PDB114     PIC X.                      
             05  TWCOB-CODFUNZ              PIC X(2).                   
             05  TWCOB-AREA-MSG             PIC X(70).                  
             SKIP1                                                      
      *  TIPO AGGIORN ('I' INSER; 'U' VARIAZ.)                          
             05  TWCOB-TIPA-AGG             PIC X.                      
             SKIP1                                                      
      *  TIPO ANNO(AP/AC --> PRECEDENTE/CORRENTE)                       
             05  TWCOB-ANNO-TIPO            PIC X(2).                   
             SKIP1                                                      
      *--------- ULTIME 2 CIFRE DELL'ANNO SCELTO                        
             05  TWCOB-ANNO-ELAB            PIC X(2).                   
             SKIP1                                                      
      *--------- PRIME  2 CIFRE DELL'ANNO SCELTO                        
             05  TWCOB-ANNO-ELAB12          PIC X(2).                   
             SKIP1                                                      
             05  TWCOB-ADDREG-ANNO          PIC X(4).                   
             05  TWCOB-ADDREG-STATO         PIC X.                      
             05  TWCOB-SW-STAMPA-SU-CODA    PIC X.                      
             05  TWCOB-COMANDO-PRED         PIC X(8).                   
             05  TWCOB-NOME-TABDF           PIC X(8).                   
             05  TWCOB-SP-ITEMTS            PIC S9(3) COMP-3.           
             05  TWCOB-SP-MAXRECTS          PIC S9(3) COMP-3.           
             05  TWCOB-TIPO-POSIZ           PIC X.                      
             05  TWCOB-ESPANS-CN            PIC X(47).                  
             SKIP1                                                      
             05  TWCOB-BRO-GRUPPO-PARL.                                 
                 10  TWCOB-BRO-GRUPPO-PARL1  PIC X.                     
                 10  TWCOB-BRO-GRUPPO-PARL23 PIC XX.                    
             SKIP1                                                      
             05  TWCOB-NSISTEMA             PIC XX.                     
             05  TWCOB-NTAB-IPAV            PIC X.                      
             05  TWCOB-NTAB-IPAVNUM REDEFINES  TWCOB-NTAB-IPAV          
                                            PIC 9.                      
             05  TWCOB-ULTIMA-VOCE.                                     
                10  TWCOB-ULTIMA-VOCE-NT    PIC 9.                      
                10  TWCOB-ULTIMA-VOCE-XX    PIC 9.                      
                10  TWCOB-ULTIMA-VOCE-COD   PIC 9(2).                   
             05  TWCOB-MESE-RIFE            PIC X(2).                   
             05  TWCOB-ULTIMA-PERC-AVR      PIC S9(3)V99 COMP-3.        
             05  TWCOB-ID-SISTEMA           PIC XX.                     
             SKIP1                                                      
             05  TWCOB-IMPI-TIPO                PIC X.                  
             05  TWCOB-IMPI-DATA.                                       
                 07  TWCOB-IMPI-GG              PIC XX.                 
                 07  TWCOB-IMPI-MM              PIC XX.                 
                 07  TWCOB-IMPI-AAAA.                                   
                     09  TWCOB-IMPI-AA12        PIC XX.                 
                     09  TWCOB-IMPI-AA34        PIC XX.                 
           SKIP1                                                        
             05  TWCOB-CESS-TIPO                PIC X.                  
             05  TWCOB-CESS-DATA.                                       
                 07  TWCOB-CESS-GG              PIC XX.                 
                 07  TWCOB-CESS-MM              PIC XX.                 
                 07  TWCOB-CESS-AAAA.                                   
                     09  TWCOB-CESS-AA12        PIC XX.                 
                     09  TWCOB-CESS-AA34        PIC XX.                 
             05  TWCOB-AMBIENTE-CICS            PIC X.                  
             05  TWCOB-NOME-CICS                PIC X(4).               
             SKIP1                                                      
             05  TWCOB-FSLIV1-SISTEMA           PIC X.                  
             05  TWCOB-FSLIV2-DATI.                                     
                 07  TWCOB-FSLIV2-DATI1         PIC X.                  
                 07  TWCOB-FSLIV2-DATI2         PIC X.                  
             05  TWCOB-CATEG-FAMILIARE          PIC X(02).              
             05  TWCOB-ELEM-PROG                PIC S9(3) COMP-3.       
             05  TWCOB-ELEM-NTOT                PIC S9(3) COMP-3.       
             05  TWCOB-ANNO-RIFE                PIC XX.                 
             05   TWCOB-XCTL2.                                          
                  07   TWCOB-XCTL2-PGM          PIC X(8).               
                  07   TWCOB-XCTL2-FUNZ         PIC X.                  
                  07   TWCOB-XCTL2-FASE         PIC X.                  
             SKIP1                                                      
             05   TWCOB-SWIMPIANTO-RUOLOIP      PIC X.                  
             05   TWCOB-CATEG-UTENTE            PIC XX.                 
      *-----------------------------------------------------------      
      * TWCOB-UNITA-MONETARIA: 'E' EURO; ' ' LIRA (IN FASE DI TEST)     
      *-----------------------------------------------------------      
             05  TWCOB-UNITA-MONETARIA          PIC X(1).               
             SKIP1                                                      
             05  TWCOB-SESSO                PIC X.                      
             05  TWCOB-STATO-REC            PIC X.                      
             05  TWCOB-ANNO-NASCITA         PIC 9(4).                   
             05  TWCOB-ESTREMI REDEFINES TWCOB-ANNO-NASCITA.            
                 07  TWCOB-LIMITE-INF       PIC 99.                     
                 07  TWCOB-LIMITE-SUP       PIC 99.                     
             SKIP1                                                      
             05  TWCOB-RISCATTI                PIC X(31).               
             05  FILLER REDEFINES TWCOB-RISCATTI.                       
                 07  TWCOB-RISCATTI-DOMAULT    PIC 99.                  
                 07  TWCOB-RISCATTI-DOMACORR   PIC 99.                  
                 07  TWCOB-RISCATTI-NLEGIS     PIC XX.                  
                 07  TWCOB-RISCATTI-RAMOMAND   PIC X.                   
                 07  TWCOB-RISCATTI-PAGCORR    PIC S9(3) COMP-3.        
                 07  TWCOB-RISCATTI-PAGTOT     PIC S9(3) COMP-3.        
                 07  TWCOB-RISCATTI-DATADOM    PIC X(8).                
                 07  TWCOB-RISCATTI-RAMOESAT   PIC X.                   
                 07  TWCOB-RISCATTI-NRATE      PIC S9(3) COMP-3.        
                 07  TWCOB-RISCATTI-IRATA      PIC S9(11) COMP-3.       
                 07  FILLER                    PIC X(3).                
             SKIP1                                                      
             05  TWCOB-ULTIMA-LEGIS         PIC XX.                     
             05  TWCOB-ITEM-CODA            PIC S9(5) COMP-3.           
             05  TWCOB-PROG-REC             PIC XX.                     
             05  TWCOB-PDBLEG-CONTRBACI     PIC X(6).                   
             05  TWCOB-PROG-PDRDP01         PIC 99.                     
             05  TWCOB-FAMILIARE-PROG       PIC 99.                     
             05  TWCOB-EREDE-PROG           REDEFINES                   
                 TWCOB-FAMILIARE-PROG       PIC 99.                     
             05  TWCOB-COD-REGIONE          REDEFINES                   
                 TWCOB-FAMILIARE-PROG       PIC 99.                     
             SKIP1                                                      
             05  TWCOB-CODATS-PRINT         PIC X(4).                   
             05  TWCOB-ASI-TIPO-VERS        PIC X.                      
             05  TWCOB-ASI-MESE2            PIC XX.                     
             05  TWCOB-ASI-GIORNI1          PIC X(2).                   
             05  TWCOB-ASI-GIORNI2          PIC X(2).                   
             05  TWCOB-ITEM-CODA-INIZ       PIC S9(5) COMP-3.           
             SKIP1                                                      
             05  TWCOB-BENEFICIARIO-PROG    PIC 99.                     
             05  TWCOB-NMAX-SORT            PIC S9(5)  COMP-3.          
             05  TWCOB-CHIAVE-RECINT        PIC X(20).
             05  TWCOB-AREA-RIV REDEFINES TWCOB-CHIAVE-RECINT.
                 10 TWCOB-RIV-PROGELAB      PIC 9(03).
                 10 TWCOB-RIV-ANNO          PIC X(04).
                 10 TWCOB-RIV-TIPORIV       PIC X(01).
                 10 TWCOB-RIV-PAG           PIC 9(03).
                 10 FILLER                  PIC X(09).
      *-----------------------------------------------------------      
      *   CAMPI PER ASSISTENZA SANITARIA                                
      * TWCOB-ASI-TIPO-VERS:  T/F/' '  (PDB130/PDB131)                  
      * TWCOB-ASI-SESSIONE:  IP/AV                                      
      * TWCOB-ASI-SESSAV-TIPO: D --> AVD; R --> AVR; A --> DEP.ATTESA   
      *                        F -> CONIUGE SENZA AVR                   
      *                        G --> GIUDICI C.C.;                      
      * TWCOB-ASI-STATO-SESS : C --> CHIUSA; ' ' --> APERTA             
      * TWCOB-ASI-TIPO-ELENCO (1/2/3/4: VEDI PROG. PDB209)              
      * TWCOB-ASI-SWELENCO (D --> DETTAGLIO; T --> TOTALIZZATO)
24F07I* TWCOB-ASI-SWELENCO X -> LETTERA TESORIERE IN CSV (OPZ 4)
      * TWCOB-ASI-TIPO-ESTRAZ --> (VEDI PDB200/PDB205/PDB214)           
      *-----------------------------------------------------------      
             05  TWCOB-ASI-SESSIONE         PIC XX.                     
             05  TWCOB-ASI-SESSAV-TIPO      PIC X.                      
             05  TWCOB-ASI-ANNO             PIC X(4).                   
             05  TWCOB-ASI-MESE             PIC XX.                     
             05  TWCOB-ASI-STATO-SESS       PIC X.                      
             05  TWCOB-ASI-TIPO-ELENCO      PIC X.                      
             05  TWCOB-ASI-SWELENCO         PIC X.                      
             05  TWCOB-ASI-ARTICOLO         PIC X.                      
             05  TWCOB-ASI-NRIGHE           PIC S9(5) COMP-3.           
             05  TWCOB-BEX-NRIGHE           REDEFINES                   
                 TWCOB-ASI-NRIGHE           PIC S9(5) COMP-3.           
             05  TWCOB-ASI-PROT-NUM         PIC X(6).                   
             05  TWCOB-ASI-MAND-NUM         REDEFINES                   
                 TWCOB-ASI-PROT-NUM         PIC X(6).                   
             05  TWCOB-ASI-PROT-DATA.                                   
                 07  TWCOB-ASI-PROT-GG      PIC XX.                     
                 07  TWCOB-ASI-PROT-MM      PIC XX.                     
                 07  TWCOB-ASI-PROT-AAAA    PIC XXXX.                   
             05  TWCOB-ASI-TIPO-ESTRAZ      PIC X.                      
             05  TWCOB-ASI-MODPAG           PIC X.                      
             05  TWCOB-CODICE-ABI           PIC X(5).                   
      *      05  TWCOB-CODICE-COMUNE REDEFINES TWCOB-CODICE-ABI         
      *                                     PIC X(5).                   
             05  TWCOB-COD-AEROPORTO REDEFINES TWCOB-CODICE-ABI         
                                            PIC X(5).                   
             SKIP1                                                      
             05  TWCOB-RISCATTI-DATAARR     PIC X(8).                   
             05  TWCOB-AFM-FLAG             PIC X.                      
             05  TWCOB-LEGIS-CORRENTE       PIC XX.                     
             05  TWCOB-AFM-NUMREC05         PIC S9(3) COMP-3.           
             05  TWCOB-AFM-LORDO-PREC       PIC S9(11) COMP-3.          
             05  TWCOB-AFM-IMPOSTA-PREC     PIC S9(11) COMP-3.          
             05  TWCOB-TIPO-FINEMAND        PIC X.                      
             05  TWCOB-AFM-PROG             PIC 99.                     
             05  TWCOB-ULTIMO-RAMO          PIC X.                      
             05  TWCOB-AFM-LORDESEN-PREC    PIC S9(11) COMP-3.          
             05  TWCOB-AFM-FINE-DATA.                                   
                 07  TWCOB-AFM-FINE-GG      PIC 9(2).                   
                 07  TWCOB-AFM-FINE-MM      PIC 9(2).                   
                 07  TWCOB-AFM-FINE-AAAA    PIC 9(4).                   
                 07  FILLER  REDEFINES                                  
                             TWCOB-AFM-FINE-AAAA.                       
                     09  TWCOB-AFM-FINE-AA12   PIC 99.                  
                     09  TWCOB-AFM-FINE-AA34   PIC 99.                  
             05  TWCOB-PGM-SWATT            PIC X.                      
             05  TWCOB-KEY05                PIC X(12).                  
             05  TWCOB-PAGINA-CORRENTE      PIC S9(3) COMP-3.           
             05  TWCOB-SW-MAP               PIC X.                      
             05  TWCOB-STAMPANTI            PIC X(20).                  
             05  FILLER  REDEFINES TWCOB-STAMPANTI.                     
                 07  TWCOB-STAMPANTI-EL                                 
                          OCCURS 5          PIC X(4).                   
      *                                                                 
             05  TWCOB-OPETIP               PIC X(10).                  
             05  FILLER  REDEFINES TWCOB-OPETIP.                        
                 07  TWCOB-OPETIP-EL                                    
                          OCCURS 10         PIC X.                      
             05  TWCOB-OPER-NOME            PIC X(32).                  
             05  TWCOB-PDCPAG-NRIGA         PIC 9.                      
             05  TWCOB-PDCPAG-TBROW         PIC X.                      
      *-----------------------------------------------------------      
      * CAMPI PER GESTIONE ON-LINE DEI CEDOLINI                         
      * I VALORI SI RIFERISCONO ALL'ANNO IMPOSTATO NEL CAMPO            
      *    TWCOB-ANNO-ELAB.                                             
      *-----------------------------------------------------------      
             05  TWCOB-CEDOLINI.                                        
                 07  TWCOB-CED-ULTLIQ.                                  
                     09  TWCOB-CED-ULTLIQ-ANNO        PIC X(4).         
                     09  TWCOB-CED-ULTLIQ-MESE        PIC XX.           
                     09  TWCOB-CED-ULTLIQ-TMENS       PIC X.            
             SKIP1                                                      
                 07  TWCOB-CED.                                         
                     09  TWCOB-CED-FUNZIONE            PIC X.           
                     09  TWCOB-CED-LIQUID1-MESE        PIC XX.          
                     09  TWCOB-CED-LIQUID2-MESE        PIC XX.          
                     09  TWCOB-CED-VOCE.                                
                         11  TWCOB-CED-VOCE-CATEG      PIC XX.          
                         11  TWCOB-CED-VOCE-COD        PIC X(4).        
                         11  TWCOB-CED-VOCE-TIPO       PIC X.           
                     09  TWCOB-CED-MESE-VIS            PIC XX.          
                     09  TWCOB-CED-LIQUID1-TMENS       PIC X.           
                     09  TWCOB-CED-LIQUID2-TMENS       PIC X.           
                     09  TWCOB-CED-TIPO-ARRE           PIC X.           
                     09  TWCOB-CED-STATO-DIP           PIC X.           
                     09  FILLER                        PIC X(5).        
      *-----------------------------------------------------------      
      * CAMPI PER GESTIONE ON-LINE ASSENZE IN AULA                      
      * I VALORI SI RIFERISCONO ALL'ANNO IMPOSTATO NEL CAMPO            
      *    TWCOB-ANNO-ELAB.                                             
      *-----------------------------------------------------------      
             05  TWCOB-PDRASS-STATO               PIC X.                
             05  TWCOB-MESE-ELAB                  PIC 99.               
             05  TWCOB-GIORNO-ELAB                PIC 99.               
      ***    05  TWCOB-BRO-GRUPPO-PARL            PIC X(2).             
      *      05  FILLER                           PIC X(2).             
             05  TWCOB-SUBTAB-AV                  PIC X(2).             
             05  TWCOB-BRO-MESE-ELAB              PIC X(2).             
             SKIP1                                                      
      *-----------------------------------------------------------      
      * CAMPI PER GESTIONE RIMBORSI TELEFONINI                          
      * E RIDEFINIZIONI PER RIMBORSI VARI:                              
      *  TITVG = TITOLI DI VIAGGIO                                      
      *  VGGSE = VIAGGI DI STUDIO ALL'ESTERO                            
      *  SPRAP = SPESE DI RAPPRESENTANZA                                
      *  MISSI = SPESE DI MISSIONE                                      
      *  SPAVG = SPESE ACCESSORIE DI VIAGGIO                            
      *  SPESM = SPESE ESERCIZIO MANDATO                                
      *  SPTEL = SPESE DOCUMENTATE TELEFONIA                            
      *-----------------------------------------------------------      
             05  TWCOB-TELEF-ANNO           PIC X(4).                   
             05  TWCOB-TITVG-ANNO           REDEFINES                   
                 TWCOB-TELEF-ANNO           PIC X(4).                   
             05  TWCOB-VGGSE-ANNO           REDEFINES                   
                 TWCOB-TELEF-ANNO           PIC X(4).                   
             05  TWCOB-SPRAP-ANNO           REDEFINES                   
                 TWCOB-TELEF-ANNO           PIC X(4).                   
             05  TWCOB-SPESM-ANNO           REDEFINES                   
                 TWCOB-TELEF-ANNO           PIC X(4).                   
             05  TWCOB-SPTEL-ANNO           REDEFINES                   
                 TWCOB-TELEF-ANNO           PIC X(4).                   
             05  TWCOB-MISSI-ANNO           REDEFINES                   
                 TWCOB-TELEF-ANNO           PIC X(4).                   
             05  TWCOB-SPAVG-ANNO           REDEFINES                   
                 TWCOB-TELEF-ANNO           PIC X(4).                   
             05  TWCOB-BIGEX-ANNO           REDEFINES                   
                 TWCOB-TELEF-ANNO           PIC X(4).                   
                                                                        
             05  TWCOB-TELEF-SESSLIQ-ANNO   PIC X(4).                   
             05  TWCOB-TITVG-SESSLIQ-ANNO   REDEFINES                   
                 TWCOB-TELEF-SESSLIQ-ANNO   PIC X(4).                   
             05  TWCOB-VGGSE-SESSLIQ-ANNO   REDEFINES                   
                 TWCOB-TELEF-SESSLIQ-ANNO   PIC X(4).                   
             05  TWCOB-SPRAP-MESE-DA-A      REDEFINES                   
                 TWCOB-TELEF-SESSLIQ-ANNO.                              
                 10 TWCOB-SPRAP-MMDA        PIC X(2).                   
                 10 TWCOB-SPRAP-MMA         PIC X(2).                   
             05  TWCOB-SPESM-MESE-DA-A      REDEFINES                   
                 TWCOB-TELEF-SESSLIQ-ANNO.                              
                 10 TWCOB-SPESM-MMDA        PIC X(2).                   
                 10 TWCOB-SPESM-MMA         PIC X(2).                   
             05  TWCOB-SPTEL-MESE-DA-A      REDEFINES                   
                 TWCOB-TELEF-SESSLIQ-ANNO.                              
                 10 TWCOB-SPTEL-MMDA        PIC X(2).                   
                 10 TWCOB-SPTEL-MMA         PIC X(2).                   
             05  TWCOB-MISSI-SESSLIQ-ANNO   REDEFINES                   
                 TWCOB-TELEF-SESSLIQ-ANNO   PIC X(4).                   
             05  TWCOB-SPAVG-SESSLIQ-ANNO   REDEFINES                   
                 TWCOB-TELEF-SESSLIQ-ANNO   PIC X(4).                   
             05  TWCOB-BIGEX-SESSLIQ-ANNO   REDEFINES                   
                 TWCOB-TELEF-SESSLIQ-ANNO   PIC X(4).                   
                                                                        
             05  TWCOB-TELEF-SESSLIQ-MESE   PIC X(2).                   
             05  TWCOB-TITVG-SESSLIQ-MESE   REDEFINES                   
                 TWCOB-TELEF-SESSLIQ-MESE   PIC X(2).                   
             05  TWCOB-VGGSE-SESSLIQ-MESE   REDEFINES                   
                 TWCOB-TELEF-SESSLIQ-MESE   PIC X(2).                   
             05  TWCOB-SPRAP-SESSLIQ-MESE   REDEFINES                   
                 TWCOB-TELEF-SESSLIQ-MESE   PIC X(2).                   
             05  TWCOB-MISSI-SESSLIQ-MESE   REDEFINES                   
                 TWCOB-TELEF-SESSLIQ-MESE   PIC X(2).                   
             05  TWCOB-SPAVG-SESSLIQ-MESE   REDEFINES                   
                 TWCOB-TELEF-SESSLIQ-MESE   PIC X(2).                   
             05  TWCOB-BIGEX-SESSLIQ-MESE   REDEFINES                   
                 TWCOB-TELEF-SESSLIQ-MESE   PIC X(2).                   
                                                                        
             05  TWCOB-TELEF-SESSLIQ-STATO  PIC X.                      
             05  TWCOB-TITVG-SESSLIQ-TMENS  REDEFINES                   
                 TWCOB-TELEF-SESSLIQ-STATO  PIC X.                      
             05  TWCOB-VGGSE-SESSLIQ-STATO  REDEFINES                   
                 TWCOB-TELEF-SESSLIQ-STATO  PIC X.                      
             05  TWCOB-SPRAP-SESSLIQ-STATO  REDEFINES                   
                 TWCOB-TELEF-SESSLIQ-STATO  PIC X.                      
             05  TWCOB-MISSI-SESSLIQ-TMENS  REDEFINES                   
                 TWCOB-TELEF-SESSLIQ-STATO  PIC X.                      
             05  TWCOB-SPAVG-SESSLIQ-TMENS  REDEFINES                   
                 TWCOB-TELEF-SESSLIQ-STATO  PIC X.                      
             05  TWCOB-BIGEX-SESSLIQ-STATO  REDEFINES                   
                 TWCOB-TELEF-SESSLIQ-STATO  PIC X.                      
                                                                        
             05  TWCOB-TELEF-BOLLETTA-ANNO  PIC X(4).                   
             05  TWCOB-TITVG-SOC-CRIM       REDEFINES                   
                 TWCOB-TELEF-BOLLETTA-ANNO.                             
                 10 TWCOB-TITVG-SOC         PIC X(3).                   
                 10 TWCOB-TITVG-CRIM        PIC X.                      
             05  TWCOB-TELEF-BOLLETTA-BIM   PIC X(2).                   
                                                                        
             05  TWCOB-TELEF-PROGTEL        PIC X(2).                   
             05  TWCOB-VGGSE-LEGIS          REDEFINES                   
                 TWCOB-TELEF-PROGTEL        PIC X(2).                   
             05  TWCOB-SPESM-LEGIS          REDEFINES                   
                 TWCOB-TELEF-PROGTEL        PIC X(2).                   
             05  TWCOB-SPTEL-LEGIS          REDEFINES                   
                 TWCOB-TELEF-PROGTEL        PIC X(2).                   
             05  TWCOB-SPAVG-LEGIS          REDEFINES                   
                 TWCOB-TELEF-PROGTEL        PIC X(2).                   
             05  TWCOB-BIGEX-LEGIS          REDEFINES                   
                 TWCOB-TELEF-PROGTEL        PIC X(2).                   
                                                                        
             05  TWCOB-TELEF-OPZIONE        PIC X.                      
             05  TWCOB-TITVG-VETTORE        REDEFINES                   
                 TWCOB-TELEF-OPZIONE        PIC X.                      
                                                                        
             05  TWCOB-ASI-PRIMO-REC        PIC S9(5) COMP-3.           
             05  TWCOB-ASI-ULTIMO-REC       PIC S9(5) COMP-3.           
             05  TWCOB-CAF-ANNO             PIC X(4).                   
             SKIP1                                                      
             05  TWCOB-TELEF-IMPZERO        PIC X.                      
             05  TWCOB-TITVG-IMPZERO        REDEFINES                   
                 TWCOB-TELEF-IMPZERO        PIC X.                      
             05  TWCOB-VGGSE-IMPZERO        REDEFINES                   
                 TWCOB-TELEF-IMPZERO        PIC X.                      
             05  TWCOB-SPRAP-IMPZERO        REDEFINES                   
                 TWCOB-TELEF-IMPZERO        PIC X.                      
             05  TWCOB-MISSI-IMPZERO        REDEFINES                   
                 TWCOB-TELEF-IMPZERO        PIC X.                      
             05  TWCOB-SPAVG-IMPZERO        REDEFINES                   
                 TWCOB-TELEF-IMPZERO        PIC X.                      
                                                                        
             05  TWCOB-TELEF-PROGPLAF       PIC X.                      
             SKIP1                                                      
             05  TWCOB-OPER-TIPO            PIC X(1).                   
             SKIP1                                                      
             05  TWCOB-ITAB                 PIC S9(3) COMP-3.           
             05  TWCOB-IP-MAX               PIC S9(3) COMP-3.           
             05  TWCOB-IP                   PIC 999.                    
      *------------------------------------------*                      
      * SALVATAGGIO PROGRAMMA, FUNZIONE, FASE                           
      *------------------------------------------*                      
             05   TWCOB-XCTL.                                           
                  07   TWCOB-XCTL-PGM       PIC X(8).                   
                  07   TWCOB-XCTL-FUNZ      PIC X.                      
                  07   TWCOB-XCTL-FASE      PIC X.                      
             05   TWCOB-SWPF4               PIC X.                      
             05   TWCOB-SWAC                PIC X.                      
             05   TWCOB-SWPERC              PIC X.                      
           SKIP1                                                        
             05   TWCOB-IND-PARL            PIC 9(11).                  
             05   TWCOB-ANNI-MANDATO        PIC 99.                     
             05   TWCOB-RIFE-GG             PIC 99.                     
             05   TWCOB-TABLEGIS            PIC X(210).                 
           SKIP1                                                        
             05   TWCOB-PRESENTA-BANCHE     PIC X.                      
             05   TWCOB-PRESENTA-COMUNI REDEFINES TWCOB-PRESENTA-BANCHE 
                                            PIC X.                      
             05   TWCOB-PRESENTA-NOMI       PIC X.                      
             05   TWCOB-ACCESSO-SISTEMA     PIC X.                      
           SKIP1                                                        
      *      05  TWCOB-DESC-GRUPPO          PIC X(50).                  
             05  TWCOB-OPER-EMAIL           PIC X(35).
lug 21       05  TWCOB-SAVE-ID              PIC S9(9) COMP. 
lug 21* ci sarebbe anche altro filler disp. - era 11 - mod. 11/11/24
24M11I       05  FILLER                     PIC X(07).   
lug 21*       05  FILLER                     PIC X(15).  
24M11I       05  TWCOB-RIV-VERSA            PIC S9(3) COMP-3.       
24M11I       05  TWCOB-RIV-VERST            PIC S9(3) COMP-3.
           SKIP1                                                        
             05  TWCOB-ANNO4-RIFE           PIC X(04).                  
           SKIP1                                                        
             05  TWCOB-PARM-DATA1.                                      
                 10 TWCOB-PARM-DATA1-GG     PIC X(02).                  
                 10 TWCOB-PARM-DATA1-MM     PIC X(02).                  
                 10 TWCOB-PARM-DATA1-AAAA   PIC X(04).                  
           SKIP1                                                        
             05  TWCOB-FUNZIONI-UTENTE.                                 
                 10 TWCOB-FUNZIONI-SP           PIC X(1).               
                 10 TWCOB-FUNZIONI-LIQIP        PIC X(1).               
                 10 TWCOB-FUNZIONI-LIQAV        PIC X(1).               
                 10 TWCOB-FUNZIONI-ASI          PIC X(1).               
                 10 TWCOB-FUNZIONI-BILCASSA     PIC X(1).               
                 10 TWCOB-FUNZIONI-BIGLIETTI    PIC X(1).               
                 10 TWCOB-FUNZIONI-BIGL-EX      PIC X(1).               
                 10 TWCOB-FUNZIONI-PROTASI      PIC X(1).               
                 10 FILLER                      PIC X(2).               
      *------------------------------------------------*                
      *       !!!!!   ATTENZIONE   !!!!!!!                              
      *                                                                 
      *    PER INSERIRE ULTERIORI CAMPI USARE IL FILLER                 
      *    SOTTOSTANTE, AGGIORNANDONE LA LUNGHEZZA.                     
      * CONTROLLARE SUL LISTING DELLA COMPILAZIONE                      
      *  CHE LA PARTE PRIMA DELLA TWA NON SIA PIU'                      
      *  LUNGA DI 1000 BYTES.                                           
      *------------------------------------------------*                
      ****   05   FILLER                    PIC X(28).                  
           SKIP1                                                        
         03  TWCOB-PARTE-SECONDA            PIC X(1000).                
      *------------------------------------------------*                
      * PARTE SECONDA: USATA PER SALVATAGGIO DEI RECORDS                
      *    FRA UNA FASE E L'ALTRA                                       
      *------------------------------------------------*                
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
      *          TWCOB-PDRAL03                                          
             05  TWCOB-RECORD-DL            PIC X(100).                 
             05  FILLER                     PIC X(900).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
      *          TWCOB-PDRFAM                                           
             05  TWCOB-RECORD-FA            PIC X(130).                 
             05  FILLER                     PIC X(870).                 
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
      *          TWCOB-PDRAL01                                          
             05  TWCOB-RECORD-DA            PIC X(500).                 
             05  FILLER                     PIC X(500).                 
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
      *          TWCOB-PDRAL011                                         
             05  TWCOB-RECORD-DAREV         PIC X(50).                  
             05  FILLER                     PIC X(950).                 
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
      *          TWCOB-PDRAL05                                          
             05  TWCOB-RECORD-AFM           PIC X(400).                 
             05  TWCOB-RECORD-AFM2          PIC X(400).                 
             05  FILLER                     PIC X(200).                 
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
      *          TWCOB-PDRAL50                                          
             05  TWCOB-RECORD-MPAG          PIC X(200).                 
             05  FILLER                     PIC X(800).                 
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRAL06              PIC X(100).                 
             05  TWCOB-PDRAL06-PREC         PIC X(100).                 
             05  FILLER                     PIC X(800).                 
             SKIP1                                                      
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
      *          TWCOB-PDRTIP00                                         
             05  TWCOB-PDRTIP-REC00         PIC X(350).                 
             05  FILLER                     PIC X(650).                 
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
      *          TWCOB-PDRTIP01                                         
             05  TWCOB-PDRTIP-REC01         PIC X(350).                 
             05  FILLER                     PIC X(650).                 
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRTIP02             PIC X(1000).                
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
      *          TWCOB-PDRBAN                                           
             05  TWCOB-PDRBAN-REC           PIC X(200).                 
             05  FILLER                     PIC X(800).                 
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
      *          TWCOB-PDRSBA                                           
             05  TWCOB-PDRSBA-REC           PIC X(200).                 
             05  FILLER                     PIC X(800).                 
             SKIP1                                                      
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRDP00              PIC X(110).                 
             05  TWCOB-PDRDP01              PIC X(130).                 
             05  TWCOB-PDRDP01-PREC         PIC X(130).                 
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRDP03              PIC X(100).                 
             05  TWCOB-PDRDP03-PREC         PIC X(100).                 
             05  FILLER                     PIC X(800).                 
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRDP05              PIC X(100).                 
             05  TWCOB-PDRDP05-PREC         PIC X(100).                 
             05  FILLER                     PIC X(800).                 
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRDP04              PIC X(300).                 
             05  FILLER                     PIC X(700).                 
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRDP02              PIC X(110).                 
             05  TWCOB-PDRDP02-PREC         PIC X(110).                 
             05  FILLER                     PIC X(780).                 
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRDP06              PIC X(200).                 
             05  TWCOB-PDRDP06-PREC         PIC X(200).                 
             05  FILLER                     PIC X(600).                 
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRAL21              PIC X(100).                 
             05  TWCOB-PDRAL21-PREC         PIC X(100).                 
             05  TWCOB-PDRAL21-SUCC         PIC X(100).                 
             05  FILLER                     PIC X(700).                 
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRSIS02             PIC X(500).                 
             05  FILLER                     PIC X(500).                 
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-RECORD-REQ           PIC X(100).                 
             05  TWCOB-RECORD-REQ-PREC      PIC X(100).                 
             05  FILLER                     PIC X(800).                 
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRVERS              PIC X(250).                 
             05  TWCOB-PDRVERS-PREC         PIC X(250).                 
             05  FILLER                     PIC X(500).                 
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRASIF              PIC X(80).                  
             05  TWCOB-PDRASIF-PREC         PIC X(80).                  
             05  FILLER                     PIC X(840).                 
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRASS01             PIC X(250).                 
             05  FILLER                     PIC X(750).                 
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRASS02             PIC X(250).                 
             05  FILLER                     PIC X(750).                 
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRVC                PIC X(200).                 
             05  FILLER                     PIC X(800).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRRIS01             PIC X(160).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRRIS02             PIC X(160).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRRIS03             PIC X(80).                  
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRDCA               PIC X(1000).                
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRASI               PIC X(250).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRASID              PIC X(250).                 
             05  FILLER                     PIC X(750).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRASIMP             PIC X(130).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRSVPAR             PIC X(120).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRM101              PIC X(900).                 
             05  FILLER                     PIC X(100).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRTABE              PIC X(250).                 
             05  FILLER                     PIC X(750).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRTABDF             PIC X(350).                 
             05  TWCOB-PDRTABDF-PREC        PIC X(350).                 
             05  FILLER                     PIC X(300).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRDF10              PIC X(400).                 
             05  TWCOB-PDRDF10-PREC         PIC X(400).                 
             05  FILLER                     PIC X(200).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRTELP              PIC X(250).                 
             05  FILLER                     PIC X(750).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRTELR              PIC X(250).                 
             05  TWCOB-PDRTELR-PREC         PIC X(250).                 
             05  FILLER                     PIC X(500).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRCAF               PIC X(600).                 
             05  FILLER                     PIC X(400).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRADR               PIC X(100).                 
             05  FILLER                     PIC X(900).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRADC               PIC X(100).                 
             05  FILLER                     PIC X(900).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRALQC              PIC X(200).                 
             05  FILLER                     PIC X(800).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRAN2               PIC X(500).                 
             05  FILLER                     PIC X(500).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRUDF               PIC X(500).                 
             05  FILLER                     PIC X(500).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRFPE               PIC X(500).                 
             05  FILLER                     PIC X(500).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRFPD               PIC X(500).                 
             05  TWCOB-PDRFPD-PREC          PIC X(500).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDROPER              PIC X(200).                 
             05  FILLER                     PIC X(800).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRERA               PIC X(400).                 
             05  FILLER                     PIC X(600).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRERC               PIC X(900).                 
             05  FILLER                     PIC X(100).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRALQR              PIC X(300).                 
             05  FILLER                     PIC X(700).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRTVG               PIC X(300).                 
             05  FILLER                     PIC X(700).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRVSEP              PIC X(150).                 
             05  FILLER                     PIC X(850).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRVSER              PIC X(250).                 
             05  FILLER                     PIC X(750).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRSRAP              PIC X(150).                 
             05  FILLER                     PIC X(850).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRSRAR              PIC X(250).                 
             05  FILLER                     PIC X(750).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRSRAS              PIC X(250).                 
             05  FILLER                     PIC X(750).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRMIS               PIC X(300).                 
             05  FILLER                     PIC X(700).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRSAVA              PIC X(100).                 
             05  FILLER                     PIC X(900).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRSAVD              PIC X(100).                 
             05  FILLER                     PIC X(900).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRSAVP              PIC X(150).                 
             05  FILLER                     PIC X(850).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRSAVL              PIC X(700).                 
             05  FILLER                     PIC X(300).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRBEXP              PIC X(200).                 
             05  FILLER                     PIC X(800).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRBEXR              PIC X(250).                 
             05  FILLER                     PIC X(750).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRSEMC              PIC X(200).                 
             05  FILLER                     PIC X(800).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRSEMS              PIC X(400).                 
             05  FILLER                     PIC X(600).                 
           SKIP1                                                        
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDRTELS              PIC X(250).                 
             05  FILLER                     PIC X(750).                 
           SKIP1                                
         03  FILLER REDEFINES TWCOB-PARTE-SECONDA.                      
             05  TWCOB-PDBCESQ.                       
                 07  TWCOB-PDBCESQ-STATO-CONTR    PIC X(01).
                 07  TWCOB-PDBCESQ-CHIAVE-INTFIN  PIC X(05).
                 07  TWCOB-PDBCESQ-NUM-CONTR      PIC X(15).
                 07  TWCOB-PDBCESQ-NOMIN-RESP     PIC X(40).
                 07  TWCOB-PDBCESQ-MAIL-RESP      PIC X(40).  
                 07  TWCOB-PDBCESQ-IMP-CESSIONE   PIC X(12).
                 07  TWCOB-PDBCESQ-IMP-RATA       PIC X(12).
                 07  TWCOB-PDBCESQ-NUM-RATE-PREV  PIC X(03).
                 07  TWCOB-PDBCESQ-PROGR-TES      PIC X(03).
                 07  TWCOB-PDBCESQ-FLAG           PIC X(01).
                 07  TWCOB-PDBCESQ-NETTO-CEDO     PIC X(12).
                 07  TWCOB-PDBCESQ-MENS-CEDO      PIC X(07).
                 07  TWCOB-PDBCESQ-QUOTA-CEDIBILE PIC 9(04)V9(02).  
                 07  TWCOB-PDBCESQ-MSG            PIC X(79).      
                 07  FILLER                       PIC X(764). 
      *-----------------------------------------------------------
      *  APR 2022 AREA SALVATAGGIO NUO GESTIONE ANAGRAFICA A 2 MAPPE
      *-----------------------------------------------------------
         03 FILLER REDEFINES TWCOB-PARTE-SECONDA.
          05 TWCOB-ANASAVE.
             10 TWCOB-MAP1. 
                15 TWCOB-DACOGN                    PIC X(30).
                15 TWCOB-DANOME                    PIC X(30).
                15 TWCOB-DACOFIO                   PIC X(16).
                15 TWCOB-DASEXO                    PIC X(01).
                15 TWCOB-DAESCNO                   PIC X(50).          
                15 TWCOB-DAREPAO                   PIC X(01).      
                15 TWCOB-DAATTEO                   PIC X(01).
                15 TWCOB-DAPROFO                   PIC X(01).
                15 TWCOB-DATISTO                   PIC X(01). 
                15 TWCOB-DASTCIO                   PIC X(01).
                15 TWCOB-DAGGVARO                  PIC X(02).
                15 TWCOB-DAMMVARO                  PIC X(02).
                15 TWCOB-DAAAVARO                  PIC X(04).
                15 TWCOB-DAGGNASO                  PIC X(02).
                15 TWCOB-DAMMNASO                  PIC X(02).
                15 TWCOB-DAAANASO                  PIC X(04). 
                15 TWCOB-CODNASO                   PIC X(04).
                15 TWCOB-LOCNASO                   PIC X(50).
                15 TWCOB-DAGGDECO                  PIC X(02).
                15 TWCOB-DAMMDECO                  PIC X(02).
                15 TWCOB-DAAADECO                  PIC X(04). 
                15 TWCOB-DACANC                    PIC X(02).
             10 TWCOB-MAP2.
                15 TWCOB-DAFLAGO                   PIC X(01).
                15 TWCOB-CODRESO                   PIC X(04).
                15 TWCOB-DAPRESSO                  PIC X(39).
                15 TWCOB-DAINDIO                   PIC X(35).
                15 TWCOB-DACAPO                    PIC X(05).
                15 TWCOB-DATELRO                   PIC X(14).
                15 TWCOB-LOCRESO                   PIC X(50).
                15 TWCOB-CODDOMO                   PIC X(04).
                15 TWCOB-DAPRESDO                  PIC X(39).
                15 TWCOB-DAINDIDO                  PIC X(35).
                15 TWCOB-DACAPDO                   PIC X(05).
                15 TWCOB-DATELDO                   PIC X(14).
                15 TWCOB-LOCDOMO                   PIC X(50).
                15 TWCOB-M1FAXO                    PIC X(14).
                15 TWCOB-M1TEL2O                   PIC X(14).
                15 TWCOB-M1CARTO                   PIC X(01).
                15 TWCOB-M1EML2O                   PIC X(40).
                15 TWCOB-M1PGASO                   PIC X(01).
set23           15 TWCOB-M1CONSO                   PIC X(01).      
          05 TWCOB-ANASAVE-CTRL.
                10 TWCOB-CALLER-PGM                PIC X(08).
                10 TWCOB-AUS-ANAG                  PIC 9(01).
                10 TWCOB-ANA-MAP1                  PIC 9(01).
                10 TWCOB-ANA-MAP2                  PIC 9(01).
      *    05 FILLER                                PIC X(412).
          05 TWCOB-CTRL-HELP                       PIC X(1).  
      *    05 TWCOB-ANA-ELAB-SAVE-MAP1.
      *       10 TWCOB-ANA-ELAB-CF                  PIC X(16).          
      *       10 TWCOB-ANA-ELAB-COGNOME             PIC X(30).
      *       10 TWCOB-ANA-ELAB-NOME                PIC X(30).
      *       10 TWCOB-ANA-ELAB-ATTFITT             PIC X(01).
      *       10 TWCOB-ANA-ELAB-CONDPROF            PIC X(01).
      *       10 TWCOB-ANA-ELAB-CONDPROF            PIC X(01).
      *       10 TWCOB-ANA-ELAB-TITSTUD             PIC X(01).
      *       10 TWCOB-ANA-ELAB-STATOCIV            PIC X(01).
      *       10 TWCOB-ANA-ELAB-CONDPROF            PIC X(01).
      *       10 TWCOB-ANA-ELAB-GGVAR               PIC X(02).
      *       10 TWCOB-ANA-ELAB-MMVAR               PIC X(02).
      *       10 TWCOB-ANA-ELAB-AAVAR               PIC X(04).
      *    05 FILLER                                PIC X(411).      
           SKIP1             
           
      *       05 TWCOB-PDBCESQ-NOMIN-RESP        REDEFINES 
      *                TWCOB-BROW-FIRST-VKEYPRIM PIC X(40).
                      
      *---------------------------------------------------------*       
      *  PARTE TERZA: UTILIZZARE QUANDO LA PARTE PRIMA E' PIENA         
      *---------------------------------------------------------*       
         03  TWCOB-PARTE-TERZA              PIC X(1000).                
         03  FILLER  REDEFINES  TWCOB-PARTE-TERZA.                      
           SKIP1                                                        
      *------------------------------------------------*                
      *   TWCOB-BROWSE:  AREA PER BROWSE LIVELLO 1     *                
      *------------------------------------------------*                
             05 TWCOB-BROWSE                    PIC X(350).             
             05  FILLER  REDEFINES  TWCOB-BROWSE.                       
                 07  TWCOB-BRO-STATO            PIC X.                  
      *    STATO BROWSE ( 0 DISATTIVO; 1 ATTIVO )                       
                 07  TWCOB-BRO-ARCH             PIC X(8).               
                 07  TWCOB-BRO-LLKEY            PIC 99.                 
      *    CHIAVE SELEZIONATA: PER RIATTIVARE IL BROWSE                 
                 07  TWCOB-BRO-KEY-SELEZ        PIC X(60).              
                 07  TWCOB-BRO-FIRST-BKEY       PIC X(60).              
                 07  TWCOB-BRO-LAST-BKEY        PIC X(60).              
                 07  TWCOB-BRO-FIRST-VKEY       PIC X(60).              
                 07  TWCOB-BRO-LAST-VKEY        PIC X(60).              
                 07  TWCOB-BRO-FINE-DATI        PIC X.                  
      *    FINE-DATI: (S/N)                                             
                 07  TWCOB-BRO-PAG-CORR         PIC S9(3) COMP-3.       
                 07  TWCOB-BRO-XCTL-PF1         PIC X(8).               
                 07  TWCOB-BRO-XCTL-PF2         PIC X(8).               
                 07  TWCOB-BRO-XCTL-PF3         PIC X(8).               
                 07  TWCOB-BRO-XCTL-PF4         PIC X(8).               
                 07  TWCOB-BRO-FUNZ             PIC X(2).               
                 07  TWCOB-BRO-TIPO-POSIZ       PIC X.                  
                 07  FILLER                     PIC X.                  
             SKIP1                                                      
      *------------------------------------------------*                
      *   TWCOB-BROWSE:  AREA PER BROWSE LIVELLO 2     *                
      *------------------------------------------------*                
             05 TWCOB-BROWSE2                   PIC X(350).             
             05  FILLER  REDEFINES  TWCOB-BROWSE2.                      
                 07  TWCOB-BRO2-STATO           PIC X.                  
      *    STATO BROWSE ( 0 DISATTIVO; 1 ATTIVO )                       
                 07  TWCOB-BRO2-ARCH            PIC X(8).               
                 07  TWCOB-BRO2-LLKEY           PIC 99.                 
      *    CHIAVE SELEZIONATA: PER RIATTIVARE IL BROWSE                 
                 07  TWCOB-BRO2-KEY-SELEZ       PIC X(60).              
                 07  TWCOB-BRO2-FIRST-BKEY      PIC X(60).              
                 07  TWCOB-BRO2-LAST-BKEY       PIC X(60).              
                 07  TWCOB-BRO2-FIRST-VKEY      PIC X(60).              
                 07  TWCOB-BRO2-LAST-VKEY       PIC X(60).              
                 07  TWCOB-BRO2-FINE-DATI       PIC X.                  
      *    FINE-DATI: (S/N)                                             
                 07  TWCOB-BRO2-PAG-CORR        PIC S9(3) COMP-3.       
                 07  TWCOB-BRO2-XCTL-PF1        PIC X(8).               
                 07  TWCOB-BRO2-XCTL-PF2        PIC X(8).               
                 07  TWCOB-BRO2-XCTL-PF3        PIC X(8).               
                 07  TWCOB-BRO2-XCTL-PF4        PIC X(8).               
                 07  TWCOB-BRO2-FUNZ            PIC X(2).               
                 07  FILLER                     PIC X(2).               
      *---   FINE AREA BROWSE       ----------------------              
           SKIP1                                                        
             05 TWCOB-BROW-FIRST-VKEYPRIM       PIC X(40).
             05 TWCOB-BROW-LAST-VKEYPRIM        PIC X(40).
           SKIP1                                                        
      *---------------------------------------------------------*       
      * CAMPI PER GESTIONE ON-LINE VARIAZIONI CONTABILI                 
      *---------------------------------------------------------*       
             05 TWCOB-VARCONT.                                          
                07 TWCOB-VARCONT-NUMFUNZ        PIC X.                  
                07 TWCOB-VARCONT-TIPOVAR        PIC X.                  
                07 TWCOB-VARCONT-VOCE           PIC X(4).               
                07 TWCOB-VARCONT-VOCE-LIV4      PIC X(4).               
                07 TWCOB-VARCONT-PROGVOCE       PIC 9(3).               
                07 TWCOB-VARCONT-ANNO           PIC X(4).               
                07 TWCOB-VARCONT-MESE           PIC XX.                 
                07 TWCOB-VARCONT-TMENS          PIC X.                  
                07 TWCOB-VARCONT-NPAGINA        PIC S9(3) COMP-3.       
             SKIP1                                                      
                07 TWCOB-VARCONT-IMPI-DATA.                             
                   09 TWCOB-VARCONT-IMPI-GG         PIC XX.             
                   09 TWCOB-VARCONT-IMPI-MM         PIC XX.             
                   09 TWCOB-VARCONT-IMPI-AAAA       PIC X(4).           
             SKIP1                                                      
                07 TWCOB-VARCONT-IMPI-NGG           PIC 99.             
             SKIP1                                                      
                07 TWCOB-VARCONT-IMPI-PROVV.                            
                   09 TWCOB-VARCONT-IPROVV-TIPO     PIC XX.             
                   09 TWCOB-VARCONT-IPROVV-NUM      PIC X(20).          
             SKIP1                                                      
                   09 TWCOB-VARCONT-IPROVV-DATA.                        
                      11 TWCOB-VARCONT-IPROVV-GG    PIC X(2).           
                      11 TWCOB-VARCONT-IPROVV-MM    PIC X(2).           
                      11 TWCOB-VARCONT-IPROVV-AAAA  PIC X(4).           
             SKIP1                                                      
                07 TWCOB-VARCONT-CESS-DATA.                             
                   09 TWCOB-VARCONT-CESS-GG         PIC XX.             
                   09 TWCOB-VARCONT-CESS-MM         PIC XX.             
                   09 TWCOB-VARCONT-CESS-AAAA       PIC X(4).           
             SKIP1                                                      
                07 TWCOB-VARCONT-CESS-NGG           PIC 99.             
             SKIP1                                                      
                07 TWCOB-VARCONT-CESS-PROVV.                            
                   09 TWCOB-VARCONT-CPROVV-TIPO     PIC XX.             
                   09 TWCOB-VARCONT-CPROVV-NUM      PIC X(20).          
             SKIP1                                                      
                   09 TWCOB-VARCONT-CPROVV-DATA.                        
                      11 TWCOB-VARCONT-CPROVV-GG    PIC XX.             
                      11 TWCOB-VARCONT-CPROVV-MM    PIC XX.             
                      11 TWCOB-VARCONT-CPROVV-AAAA  PIC X(4).           
             SKIP1                                                      
                07 TWCOB-VARCONT-IRATA          PIC S9(9) COMP-3.       
                07 TWCOB-VARCONT-IULTRATA       PIC S9(9) COMP-3.       
                07 TWCOB-VARCONT-TOTPAG         PIC S9(3) COMP-3.       
                07 TWCOB-VARCONT-NOPELIV2       PIC X.                  
                07 FILLER                       PIC X(5).               
             SKIP1                                                      
             05 TWCOB-PDKTABE-IDTAB             PIC X.                  
             05 TWCOB-PDKTABE-NOME              PIC X(8).               
             05 TWCOB-PDKTABE-COD-ELEM          PIC X(20).              
             05 TWCOB-ASI-ANNO-COMPET           PIC X(4).               
             05 TWCOB-ASI-MATRICOLA             PIC X(6).               
             05 TWCOB-ASI-DOMANDA-ANNOPROT.                             
                10 TWCOB-ASI-DOMANDA-ANNO       PIC X(4).               
                10 TWCOB-ASI-DOMANDA-PROT       PIC X(6).               
             05 TWCOB-ASI-STATO-RIMBORSO        PIC X(1).               
             05 TWCOB-ASI-PROT-SUBNUM           PIC X(4).               
             05 TWCOB-ASI-RELAZ-PARENT          PIC X(1).               
                                                                        
             05 TWCOB-PARM-DATA2.                                       
                 10 TWCOB-PARM-DATA2-GG         PIC X(02).              
                 10 TWCOB-PARM-DATA2-MM         PIC X(02).              
                 10 TWCOB-PARM-DATA2-AAAA       PIC X(04).              
                                                                        
             05 TWCOB-ASI-SW-RIMB-OPERSAN       PIC X(1).               
             05 TWCOB-ASI-OPERSAN               PIC X(16).              
             05 TWCOB-ASI-SW-CONSOLIDAMENTO     PIC X(1).               
           SKIP1                                                        
             05 FILLER                          PIC X(19).              
      *---------------------------------------------------------*       
      *                    N O T E.                                     
      *                                                                 
      *  TWCOB-OPETIP-EL                                                
      *       6 SWITCH RELATIVI ALLE 6 TABELLE                          
      *       PER OGNUNO I VALORI SONO 1,2,3,4 (VEDI PDTAB02)           
      *                                                                 
      *---------------------------------------------------------*       
      *  TWCOB-AFM-FINE-DATA    DATA FINE MANDATO USATA PER             
      *                          .IMMISSIONE AFM                        
      *---------------------------------------------------------*       
      *  TWCOB-AMBIENTE-CICS    ('P' PROVA; 'O' OPERATIVO)              
      *                                                                 
      *---------------------------------------------------------*       
      *  TWCOB-PARTE-TERZA                                              
      *      SI PUO' USARE UNA VOLTA PIENA LA PARTE PRIMA               
      *---------------------------------------------------------*       
      *---------------------------------------------------------*       
      *        F I N E   T W A                                          
      *---------------------------------------------------------*       
