/* Functions exported by the TimeHarp 260 programming library TH260Lib
	
	Ver. 3.1.0.2     PicoQuant GmbH, May 2017
*/

#ifndef _WIN32
#define _stdcall
#endif

extern int _stdcall TH260_GetLibraryVersion(char* version);
extern int _stdcall TH260_GetErrorString(char* errstring, int errcode);

extern int _stdcall TH260_OpenDevice(int devidx, char* serial); 
extern int _stdcall TH260_CloseDevice(int devidx);  
extern int _stdcall TH260_Initialize(int devidx, int mode);

//all functions below can only be used after TH260_Initialize

extern int _stdcall TH260_GetHardwareInfo(int devidx, char* model, char* partno, char* version);
extern int _stdcall TH260_GetSerialNumber(int devidx, char* serial);
extern int _stdcall TH260_GetFeatures(int devidx, int* features);
extern int _stdcall TH260_GetBaseResolution(int devidx, double* resolution, int* binsteps);
extern int _stdcall TH260_GetNumOfInputChannels(int devidx, int* nchannels);

extern int _stdcall TH260_SetSyncDiv(int devidx, int div);
extern int _stdcall TH260_SetSyncCFD(int devidx, int level, int zc);         //TH 260 Pico only 
extern int _stdcall TH260_SetSyncEdgeTrg(int devidx, int level, int edge);   //TH 260 Nano only 
extern int _stdcall TH260_SetSyncChannelOffset(int devidx, int value); 

extern int _stdcall TH260_SetInputCFD(int devidx, int channel, int level, int zc);       //TH 260 Pico only 
extern int _stdcall TH260_SetInputEdgeTrg(int devidx, int channel, int level, int edge); //TH 260 Nano only 
extern int _stdcall TH260_SetInputChannelOffset(int devidx, int channel, int value);
extern int _stdcall TH260_SetInputChannelEnable(int devidx, int channel, int enable);
extern int _stdcall TH260_SetInputDeadTime(int devidx, int channel, int tdcode); //needs TH 260 Pico >= April 2015 

extern int _stdcall TH260_SetTimingMode(int devidx, int mode); //TH 260 Pico only 
extern int _stdcall TH260_SetStopOverflow(int devidx, int stop_ovfl, unsigned int stopcount);	
extern int _stdcall TH260_SetBinning(int devidx, int binning);
extern int _stdcall TH260_SetOffset(int devidx, int offset);
extern int _stdcall TH260_SetHistoLen(int devidx, int lencode, int* actuallen); 
extern int _stdcall TH260_SetMeasControl(int devidx, int control, int startedge, int stopedge);
extern int _stdcall TH260_SetTriggerOutput(int devidx, int period);

extern int _stdcall TH260_ClearHistMem(int devidx);
extern int _stdcall TH260_StartMeas(int devidx, int tacq);
extern int _stdcall TH260_StopMeas(int devidx);
extern int _stdcall TH260_CTCStatus(int devidx, int* ctcstatus);

extern int _stdcall TH260_GetHistogram(int devidx, unsigned int *chcount, int channel, int clear);
extern int _stdcall TH260_GetResolution(int devidx, double* resolution); 
extern int _stdcall TH260_GetSyncRate(int devidx, int* syncrate);
extern int _stdcall TH260_GetCountRate(int devidx, int channel, int* cntrate);
extern int _stdcall TH260_GetFlags(int devidx, int* flags);
extern int _stdcall TH260_GetElapsedMeasTime(int devidx, double* elapsed);
extern int _stdcall TH260_GetSyncPeriod(int devidx, double* period);

extern int _stdcall TH260_GetWarnings(int devidx, int* warnings);
extern int _stdcall TH260_GetWarningsText(int devidx, char* text, int warnings);
extern int _stdcall TH260_GetHardwareDebugInfo(int devidx, char *debuginfo); 

//for time tagging modes
extern int _stdcall TH260_SetMarkerEdges(int devidx, int me1, int me2, int me3, int me4);
extern int _stdcall TH260_SetMarkerEnable(int devidx, int en1, int en2, int en3, int en4);
extern int _stdcall TH260_SetMarkerHoldoffTime(int devidx, int holdofftime);
extern int _stdcall TH260_ReadFiFo(int devidx, unsigned int* buffer, int count, int* nactual);


