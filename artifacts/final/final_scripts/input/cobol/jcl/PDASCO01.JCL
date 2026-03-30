//PDASCO01 JOB CLASS=G,MSGLEVEL=(1,1),MSGCLASS=X,
//****   TYPRUN=SCAN,
//****   RESTART=PDASCO01.PDHASS71,
//           COND=(0,LT)
//*
//*LIBPROC  JCLLIB  ORDER=SIUT0A.TPROC02.PROCLIB
//*-------------------------------------------------------------------
//*-------------------------------------------------------------------
//*-------------------------------------------------------------------
//* Acquisizione Assenze In Commissione su VSAM TEPDET.CXCB2S.ASSC
//*-------------------------------------------------------------------
//********************************************************************
//*
//PDASCO01  EXEC PDASCO01,
//          ANNO=2024,MESE=07    MESE DI RIFER.ASSENZE
//*
//********************************************************************
//* REQUISITI:
//*      - Esecuzione Procedura per aggiornamento archivi
//*        (TEPDET.BTRASFE.ASSCOMM.M&ANNO&MESE.CSV)
//*      - Archivi CXCB2P PDKASSC e PDKSIS Chiusi (chiusi da procedura)
//*-------------------------------------------------------------------
//* PRODOTTI :
//*      - Salva VSAM TEPDET.CXCB2S.ASSC prima degli aggiornamenti
//*      - Carica le Assenze in commissione  su TEPDET.CXCB2S.ASSC
//*      - Aggiorna la Data di Caricamento in TEPDET.CXCB2S.CONTROL
//*-------------------------------------------------------------------
//* RIESECUZIONE:
//*      - NON RIESEGUIBILE||||||||||||||||||||||
//*      - NON RIESEGUIBILE||||||||||||||||||||||
//*      - NON RIESEGUIBILE||||||||||||||||||||||
//*-------------------------------------------------------------------
//*******************************************************************
//* modificato PDASCO01.JCL  
