      *******************************************************           
      *  AREA COMUNICAZIONE PER GESTIONE CODE TS                        
      *-----------------------------------------------------*           
      *******************************************************           
           03  PDRGCODA-LUNGH               PIC S9(4) COMP              
                            VALUE +3100.                                
           03  PDRGCODA-FUNZIONE            PIC XX.                     
           03  PDRGCODA-RETURN              PIC X.                      
           03  PDRGCODA-LUNGH-REC           PIC S9(5) COMP-3.           
           03  PDRGCODA-PROG-REC            PIC S9(5) COMP-3.           
           03  PDRGCODA-NUMTOT-REC          PIC S9(5) COMP-3.           
           03  PDRGCODA-NOMECODA.                                       
               05  PDRGCODA-NOMETERM            PIC X(4).               
               05  PDRGCODA-KOST                PIC X(4).               
           03  FILLER                       PIC X(78).                  
           03  PDRGCODA-AREA-DATI           PIC X(3000).                
      *-----------------------------------------------------            
      * CODA TERMID+PD07: CREATA DA PDBTRAS                             
      *                   LETTA  DA PDBAF1                              
      * OGNI RECORD DELLA CODA CONTIENE 14 CHIAVI DI                    
      *   RECORDS AFM (PDRAL05)                                         
      *-----------------------------------------------------            
           03  FILLER REDEFINES PDRGCODA-AREA-DATI.                     
               05  PDRGCODA-PD07.                                       
                   07  PDRGCODA-PD07-ELEM OCCURS 14.                    
                       09  FILLER                     PIC X.            
                       09  PDRGCODA-PD07-KEYSP        PIC X(12).        
           SKIP1                                                        
      *-----------------------------------------------------            
      *   CODA  CHE INTERESSA IL RAMO DEPUTATI IN ATTESA  --            
      * CODA TERMID+PD08: CREATA DA                                     
      *                   LETTA  DA                                     
      * OGNI RECORD DELLA CODA CONTIENE  1 CHIAVE DI                    
      *   RECORDS CON CONTRIBUTI DEPUTATI IN ATTESA CON IMPORTI         
      *   IMPO1 :  CONTRIBUTI VERSATI                                   
      *   IMPO2 :  CONTRIBUTI DA VERSARE                                
      *   IMPO3 :  CONTRIBUTI RESIDUI                                   
      *-----------------------------------------------------            
           03  FILLER REDEFINES PDRGCODA-AREA-DATI.                     
               05  PDRGCODA-PD08.                                       
                   07  PDRGCODA-PD08-ELEM.                              
                     09  FILLER                     PIC X.              
                     09  PDRGCODA-PD08-KEYSP        PIC X(06).          
                     09  PDRGCODA-PD08-ANNO         PIC X(4).           
                     09  PDRGCODA-PD08-IMPO1        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PD08-IMPO2        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PD08-IMPO3        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PD08-FILLER       PIC X(21).          
           SKIP1                                                        
      *-----------------------------------------------------            
      *   CODA  PER GESTIRE RICERCHE SUI RIMBORSI TELEFONINI            
      * CODA TERMID+PD40: CREATA DA  PDB303/PDB304                      
      *   LUNG=60         LETTA  DA PDB305/PDB307                       
      *-----------------------------------------------------            
           03  FILLER REDEFINES PDRGCODA-AREA-DATI.                     
               05  PDRGCODA-PD40.                                       
                   07  PDRGCODA-PD40-ELEM.                              
                     09  PDRGCODA-PD40-CODDIP.                          
                         11  PDRGCODA-PD40-CODDIP-MATR  PIC X(5).       
                         11  PDRGCODA-PD40-CODDIP-PAD   PIC X.          
                     09  PDRGCODA-PD40-ANNO         PIC X(4).           
                     09  PDRGCODA-PD40-PROG         PIC X.              
                     09  PDRGCODA-PD40-SESSLIQ-ANNO PIC X(4).           
                     09  PDRGCODA-PD40-SESSLIQ-MESE PIC X(2).           
                     09  PDRGCODA-PD40-BOLLETTA-ANNO PIC X(4).          
                     09  PDRGCODA-PD40-BOLLETTA-BIM  PIC X(2).          
                     09  PDRGCODA-PD40-PROG-TELEF   PIC X(2).           
                     09  PDRGCODA-PD40-IMPO1        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PD40-IMPO2        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PD40-IMPO3        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PD40-IMPO4        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PD40-IMPO5        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PD40-TOPZ         PIC X.              
                     09  FILLER                     PIC X(4).           
           SKIP1                                                        
      *-----------------------------------------------------            
      *   CODA  PER GESTIRE RICERCHE SUI RIMBORSI TITOLI VIAGGIO        
      * CODA TERMID+PDTV: CREATA DA  PDB382                             
      *   LUNG=60         LETTA  DA PDB383                              
      *-----------------------------------------------------            
           03  FILLER REDEFINES PDRGCODA-AREA-DATI.                     
               05  PDRGCODA-PDTV.                                       
                   07  PDRGCODA-PDTV-ELEM.                              
                     09  PDRGCODA-PDTV-CODDIP.                          
                         11  PDRGCODA-PDTV-CODDIP-MATR  PIC X(5).       
                         11  PDRGCODA-PDTV-CODDIP-PAD   PIC X.          
                     09  PDRGCODA-PDTV-SESSLIQ-ANNO PIC X(4).           
                     09  PDRGCODA-PDTV-SESSLIQ-MESE PIC X(2).           
                     09  PDRGCODA-PDTV-ANNO         PIC X(4).           
                     09  PDRGCODA-PDTV-VETTORE      PIC X.              
                     09  PDRGCODA-PDTV-SOC          PIC X(3).           
                     09  PDRGCODA-PDTV-CRIM         PIC X.              
                     09  PDRGCODA-PDTV-IMPO1        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDTV-IMPO2        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDTV-IMPO3        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDTV-IMPO4        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDTV-IMPO5        PIC S9(11) COMP-3.  
                     09  FILLER                     PIC X(9).           
           SKIP1                                                        
      *-----------------------------------------------------            
      *   CODA  PER RIEPILOGHI SUI RIMBORSI VIAGGI STUDIO ESTERO        
      * CODA TERMID+PDVS: CREATA DA PDB393/394                          
      *   LUNG=60         LETTA  DA PDB397/395                          
      *-----------------------------------------------------            
           03  FILLER REDEFINES PDRGCODA-AREA-DATI.                     
               05  PDRGCODA-PDVS.                                       
                   07  PDRGCODA-PDVS-ELEM.                              
                     09  PDRGCODA-PDVS-CODDIP.                          
                         11  PDRGCODA-PDVS-CODDIP-MATR  PIC X(5).       
                         11  PDRGCODA-PDVS-CODDIP-PAD   PIC X.          
                     09  PDRGCODA-PDVS-ANNO         PIC X(4).           
                     09  PDRGCODA-PDVS-LEGIS        PIC X(2).           
                     09  PDRGCODA-PDVS-IMPO1        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDVS-IMPO2        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDVS-IMPO3        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDVS-IMPO4        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDVS-IMPO5        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDVS-AGGMASS      PIC X.              
                     09  PDRGCODA-PDVS-DATA         PIC X(10).          
                     09  PDRGCODA-PDVS-SESSLIQ-ANNO PIC X(4).           
                     09  PDRGCODA-PDVS-SESSLIQ-MESE PIC X(2).           
                     09  FILLER                     PIC X(01).          
           SKIP1                                                        
      *-----------------------------------------------------            
      *   CODA  PER RIEPILOGHI SUI RIMBORSI SPESE DI RAPPRESENTANZA     
      * CODA TERMID+PDSR: CREATA DA PDB373/374                          
      *   LUNG=60         LETTA  DA PDB377/375                          
      *-----------------------------------------------------            
           03  FILLER REDEFINES PDRGCODA-AREA-DATI.                     
               05  PDRGCODA-PDSR.                                       
                   07  PDRGCODA-PDSR-ELEM.                              
                     09  PDRGCODA-PDSR-CODDIP.                          
                         11  PDRGCODA-PDSR-CODDIP-MATR  PIC X(5).       
                         11  PDRGCODA-PDSR-CODDIP-PAD   PIC X.          
                     09  PDRGCODA-PDSR-ANNO         PIC X(4).           
                     09  PDRGCODA-PDSR-LEGIS        PIC X(2).           
                     09  PDRGCODA-PDSR-IMPO1        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDSR-IMPO2        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDSR-IMPO3        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDSR-IMPO4        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDSR-IMPO5        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDSR-MODPAG       PIC X.              
                     09  PDRGCODA-PDSR-DATA         PIC X(10).          
                     09  PDRGCODA-PDSR-SESSLIQ-ANNO PIC X(4).           
                     09  PDRGCODA-PDSR-SESSLIQ-MESE PIC X(2).           
                     09  FILLER                     PIC X(01).          
           SKIP1                                                        
      *-----------------------------------------------------            
      *   CODA  PER GESTIRE RICERCHE SUI RIMBORSI SPESE DI MISSIONE     
      * CODA TERMID+PDMS: CREATA DA  PDB362                             
      *   LUNG=60         LETTA  DA PDB363                              
      *-----------------------------------------------------            
           03  FILLER REDEFINES PDRGCODA-AREA-DATI.                     
               05  PDRGCODA-PDMS.                                       
                   07  PDRGCODA-PDMS-ELEM.                              
                     09  PDRGCODA-PDMS-CODDIP.                          
                         11  PDRGCODA-PDMS-CODDIP-MATR  PIC X(5).       
                         11  PDRGCODA-PDMS-CODDIP-PAD   PIC X.          
                     09  PDRGCODA-PDMS-SESSLIQ-ANNO PIC X(4).           
                     09  PDRGCODA-PDMS-SESSLIQ-MESE PIC X(2).           
                     09  PDRGCODA-PDMS-ANNO         PIC X(4).           
                     09  PDRGCODA-PDMS-DATAFINE.                        
                         11 PDRGCODA-PDMS-DATAFINE-GG   PIC  X(2).      
                         11 PDRGCODA-PDMS-DATAFINE-MM   PIC  X(2).      
                         11 PDRGCODA-PDMS-DATAFINE-AAAA PIC X(4).       
                     09  PDRGCODA-PDMS-LUOGO        PIC X(20).          
                     09  PDRGCODA-PDMS-IMPO1        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDMS-IMPO2        PIC S9(11) COMP-3.  
                     09  FILLER                     PIC X(4).           
           SKIP1                                                        
      *-----------------------------------------------------            
      *   CODA  PER GESTIRE RICERCHE SUI RIMBORSI SPESE ACC. VIAGGIO    
      * CODA TERMID+PDSV: CREATA DA  PDB354                             
      *   LUNG=60         LETTA  DA PDB353                              
      *-----------------------------------------------------            
           03  FILLER REDEFINES PDRGCODA-AREA-DATI.                     
               05  PDRGCODA-PDSV.                                       
                   07  PDRGCODA-PDSV-ELEM.                              
                     09  PDRGCODA-PDSV-CODDIP.                          
                         11  PDRGCODA-PDSV-CODDIP-MATR  PIC X(5).       
                         11  PDRGCODA-PDSV-CODDIP-PAD   PIC X.          
                     09  PDRGCODA-PDSV-SESSLIQ-ANNO PIC X(4).           
                     09  PDRGCODA-PDSV-SESSLIQ-MESE PIC X(2).           
                     09  PDRGCODA-PDSV-DATAINIZ     PIC X(8).           
                     09  PDRGCODA-PDSV-DATAFINE     PIC X(8).           
                     09  PDRGCODA-PDSV-PROGR        PIC X(1).           
                     09  PDRGCODA-PDSV-IMPO1        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDSV-IMPO2        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDSV-IMPO3        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDSV-IMPO4        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDSV-IMPO5        PIC S9(11) COMP-3.  
                     09  FILLER                     PIC X(1).           
           SKIP1                                                        
      *-----------------------------------------------------            
      *   CODA  PER RIEPILOGHI SUI RIMBORSI VIAGGI STUDIO ESTERO        
      * CODA TERMID+PDBE: CREATA DA PDB333/334                          
      *   LUNG=60         LETTA  DA PDB337/335                          
      *-----------------------------------------------------            
           03  FILLER REDEFINES PDRGCODA-AREA-DATI.                     
               05  PDRGCODA-PDBE.                                       
                   07  PDRGCODA-PDBE-ELEM.                              
                     09  PDRGCODA-PDBE-CODDIP.                          
                         11  PDRGCODA-PDBE-CODDIP-MATR  PIC X(5).       
                         11  PDRGCODA-PDBE-CODDIP-PAD   PIC X.          
                     09  PDRGCODA-PDBE-ANNO         PIC X(4).           
                     09  PDRGCODA-PDBE-LEGIS        PIC X(2).           
                     09  PDRGCODA-PDBE-IMPO1        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDBE-IMPO2        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDBE-IMPO3        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDBE-IMPO4        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDBE-IMPO5        PIC S9(11) COMP-3.  
                     09  PDRGCODA-PDBE-CALCMAN      PIC X.              
                     09  PDRGCODA-PDBE-DATA         PIC X(10).          
                     09  PDRGCODA-PDBE-SESSLIQ-ANNO PIC X(4).           
                     09  PDRGCODA-PDBE-SESSLIQ-MESE PIC X(2).           
                     09  FILLER                     PIC X(01).          
           SKIP1                                                        
      *******************************************************           
      *   PDRGCODA-FUNZIONE                                             
      *                                                                 
      *        '00'  -->  CANCELLAZIONE CODA                            
      *        '01'  -->  LETTURA DIRETTA DI UN RECORD DELLA CODA       
      *        '02'  -->  LETTURA SEQUENZIALE DELLA CODA                
      *        '03'  -->  AGGIUNTA DI UN RECORD NELLA CODA              
      *        '04'  -->  AGGIORNAMENTO DI UN RECORD                    
      *                                                                 
      *   PDRGCODA-RETURN                                               
      *                                                                 
      *         '0'  -->  TUTTO OK                                      
      *         '1'  -->  ELEMENTO INESISTENTE O FINE CODA              
      *         '2'  -->  CODA NON TROVATA                              
      *         'E'  -->  SITUAZIONE DI ERRORE GRAVE                    
      *                                                                 
      *                                                                 
      *---------------------------------------------------------        
      *                                                                 
      *******************************************************           
              SKIP1                                                     
