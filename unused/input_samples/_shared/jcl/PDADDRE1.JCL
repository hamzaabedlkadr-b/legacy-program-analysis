//PDADDRE1 JOB CLASS=M,MSGCLASS=X,MSGLEVEL=(1,1)
//*
//*********************************************************************
//*  CALCOLO  ADDIZIONALE REGIONALE PER IP/AV
//*********************************************************************
//PDADDRE1 PROC
//*
//*********************************************************************
//* RIPRISTINO DATI 
//*--------------------------------------------------------------------
//* CANCELLAZIONE DALLA TABELLA PDKADR DEI SOLI RECORD PRODOTTI 
//* DALL'ELABORAZIONE PRECEDENTE (MODALITA' "D"=SOLO DELETE PUNTUALE)
//*********************************************************************
//DELADR   EXEC PGM=PDKADR,PARM='D'        <== ATTENZIONE PARAMETRO
//SYSPRINT DD SYSOUT=*
//SYSOUT   DD SYSOUT=*
//INPSEQ   DD DSN=TEPDET.PDADDRE1.ADRTOT.&CATEG..&TIPO,DISP=SHR
//SYSTSPRT DD SYSOUT=*
//*
//*
//SCRADDR EXEC PGM=IEFBR14
//*//DD0     DD  DSN=TEPDET.BSAVE.PDKADR.PDADDRE1.A&ANNOE,
//*//           DISP=(MOD,DELETE),SPACE=(TRK,1)
//DD1  DD  DSN=TEPDET.PDADDRE1.PDHADR00,DISP=(MOD,DELETE),
//        SPACE=(TRK,1)
//DD2  DD  DSN=TEPDET.PDADDRE1.ADDREG,DISP=(MOD,DELETE),
//        SPACE=(TRK,1)
//DD3  DD  DSN=TEPDET.PDADDRE1.ADRTOT.&CATEG..&TIPO,DISP=(MOD,DELETE),
//        SPACE=(TRK,1)
//DD4  DD DSN=TEPDET.B.ADRCES.&TIPO,DISP=(MOD,DELETE) 
//*
//*//*******************************************************************
//*   !!!! VERIFICARE SE PUO' SERIVRE E QUANDO FARLO !!!!
//*//*******************************************************************
//*//*******************************************************************
//*//*  SALVATAGGIO PREVENTIVO TABELLA ORACLE 'PDKADR' SU SEQUENZIALE
//*//*******************************************************************
//*//SAVE1    EXEC PGM=PDUNADR
//*//SYSPRINT DD SYSOUT=*
//*//SYSOUT   DD SYSOUT=*
//*//PDOUADR  DD DSN=TEPDET.BSAVE.PDKADR.PDADDRE1.A&ANNOE,
//*//            VOL=SER=TESP5A,SPACE=(CYL,(5,3),RLSE),DISP=(,CATLG),
//*//            DCB=(RECFM=FB,LRECL=100,DSORG=PS),UNIT=3390
//*//SYSTSPRT DD SYSOUT=*
//*-------------------------------------------------------------------
//PDHADR00 EXEC PGM=PDHADR00,PARM='&ANNO,&TIPOLIQ,&TIPO'
//*                   *** ESTRAE RECORD PDRM101 DELL'ANNO ***
//*STEPLIB  DD DSN=SISY2S.BATCHAM.LOADLIB,DISP=SHR
//***MIGR PDKTAB1  DD DSN=TEPDET.CXCB2S.PDKTAB1,DISP=SHR
//PDKM101  DD DSN=TEPDET.CXCB2S.PDKM101,DISP=SHR
//PDSM101  DD DSN=TEPDET.PDADDRE1.PDHADR00,DISP=(,CATLG),
//            DCB=(LRECL=900,DSORG=PS,RECFM=FB)
//STAMPA   DD SYSOUT=*,DCB=(LRECL=133,RECFM=FA)
//SYSOUT   DD SYSOUT=*
//SYSUDUMP DD SYSOUT=9
//*-------------------------------------------------------------------
//PDHADR01 EXEC PGM=PDHADR01,PARM='&ANNO,&SESSLIQ,&TIPOLIQ'
//*          ** CALCOLA ADDIZIONALE REGIONALE PER OGNI MATRICOLA **
//*STEPLIB  DD DSN=SISY2S.BATCHAM.LOADLIB,DISP=SHR
//**MIGR   PDKTAB1  DD DSN=TEPDET.CXCB2S.PDKTAB1,DISP=SHR
//**MIGR   PDKALQR  DD DSN=TEPDET.CXCB2S.PDKALQR,DISP=SHR
//**MIGR   PDKANAG0 DD DSN=TEPDET.CXCB2S.SPAL,DISP=SHR
//**MIGR   PDKDFCA0 DD DSN=TEPDET.CXCB2S.PDKDF,DISP=SHR
//**MIGR   PDKADR   DD DSN=TEPDET.CXCB2S.PDKADR,DISP=SHR
//***MIGR PDKIRPE0 DD DSN=TEPDET.CXCB2S.TIP,DISP=SHR
//**MIGR   PDKDF0   DD DSN=TEPDET.CXCB2S.PDKDF,DISP=SHR
//PDKM101  DD DSN=TEPDET.CXCB2S.PDKM101,DISP=SHR
//PDSM101  DD DSN=TEPDET.PDADDRE1.PDHADR00,DISP=OLD
//FADDIZ   DD DSN=TEPDET.PDADDRE1.ADDREG,DISP=(,CATLG),
//            DCB=(LRECL=100,DSORG=PS,RECFM=FB)
//FADRCES  DD DSN=TEPDET.B.ADRCES.&TIPO,DISP=(,CATLG),
//            DCB=(LRECL=100,DSORG=PS,RECFM=FB)
//*STAMPA   DD DUMMY,SYSOUT=*,DCB=(LRECL=133,RECFM=FA)
//STAMPA   DD DUMMY   Microfocus
//SYSOUT   DD SYSOUT=*
//SYSUDUMP DD SYSOUT=9
//*-------------------------------------------------------------------
//SKSADR   EXEC PGM=PARM2SK,                                            
//         PARM=' SORT FIELDS=(1,15,CH,A)'                              
//*STEPLIB  DD DSN=SISY2S.BATCHAM.LOADLIB,DISP=SHR                      
//SKEDA    DD DSN=&&INSADR,DISP=(,PASS),UNIT=3390,SPACE=(80,1)          
//*SYSOUT   DD DUMMY,SYSOUT=*
//SYSOUT   DD DUMMY  Microfocus
//*-----------------------------------------------------------------    
//SORADR   EXEC PGM=ICEMAN                                              
//SORTLIB  DD DSN=SYS1.SORTLIB,DISP=SHR                                 
//SYSOUT   DD SYSOUT=*                                                  
//SORTIN   DD DSN=TEPDET.PDADDRE1.ADDREG,DISP=OLD                        
//SORTOUT  DD DSN=TEPDET.PDADDRE1.ADRTOT.&CATEG..&TIPO,DISP=(,CATLG),                 
//            DCB=(LRECL=100,DSORG=PS,RECFM=FB)                 
//SYSIN    DD DSN=&&INSADR,DISP=(OLD,DELETE)                            
//*
//*******************************************************************
//* CARICAMENTO TABELLA PDKADR DEI SOLI RECORD PRODOTTI 
//* DALL'ELABORAZIONE (MODALITA' "I"=DELETE/INSERT)
//*******************************************************************
//CARADR   EXEC PGM=PDKADR,PARM='I'        <== ATTENZIONE PARAMETRO
//SYSPRINT DD SYSOUT=*
//SYSOUT   DD SYSOUT=*
//INPSEQ   DD DSN=TEPDET.PDADDRE1.ADRTOT.&CATEG..&TIPO,DISP=SHR
//SYSTSPRT DD SYSOUT=*
//*
//PDADDRE1 PEND
//*----------------------------------------------
//PDADDRE1  EXEC PDADDRE1,       
//*
//       ANNO=2019,            ANNO DEI REDDITI DA CERTIFICARE
//       SESSLIQ=202002,       SESSIONE DI LIQUIDAZIONE
//***       ANNOE=2020,           ANNO ELABORAZIONE (PER STEP SAVEADR0)
//       TIPOLIQ=F,            F: LIQ. FINALE; P: LIQ. PROVVISORIA
//       TIPO=IP,              IP - AV - CD (IP + AV)
//       CATEG=T               C (CESSATI)/T (ATTIVI) 
//*
