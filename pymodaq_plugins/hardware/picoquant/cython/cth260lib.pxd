# cth260lib.pxd

cdef extern from "th260lib.h":

    int __stdcall TH260_GetLibraryVersion(char* vers)
    int __stdcall TH260_GetErrorString(char* errstring, int errcode);

    int __stdcall TH260_OpenDevice(int devidx, char* serial); 
    int __stdcall TH260_CloseDevice(int devidx);  
    int __stdcall TH260_Initialize(int devidx, int mode);

    int __stdcall TH260_GetHardwareInfo(int devidx, char* model, char* partno, char* version);
    int __stdcall TH260_GetSerialNumber(int devidx, char* serial);
    int __stdcall TH260_GetFeatures(int devidx, int* features);
    int __stdcall TH260_GetBaseResolution(int devidx, double* resolution, int* binsteps);
    int __stdcall TH260_GetNumOfInputChannels(int devidx, int* nchannels);

    int __stdcall TH260_SetSyncDiv(int devidx, int div);
    int __stdcall TH260_SetSyncCFD(int devidx, int level, int zc);
    int __stdcall TH260_SetSyncEdgeTrg(int devidx, int level, int edge);
    int __stdcall TH260_SetSyncChannelOffset(int devidx, int value); 

    int __stdcall TH260_SetInputCFD(int devidx, int channel, int level, int zc);
    int __stdcall TH260_SetInputEdgeTrg(int devidx, int channel, int level, int edge);
    int __stdcall TH260_SetInputChannelOffset(int devidx, int channel, int value);
    int __stdcall TH260_SetInputChannelEnable(int devidx, int channel, int enable);
    int __stdcall TH260_SetInputDeadTime(int devidx, int channel, int tdcode);

    int __stdcall TH260_SetTimingMode(int devidx, int mode);
    int __stdcall TH260_SetStopOverflow(int devidx, int stop_ovfl, unsigned int stopcount);	
    int __stdcall TH260_SetBinning(int devidx, int binning);
    int __stdcall TH260_SetOffset(int devidx, int offset);
    int __stdcall TH260_SetHistoLen(int devidx, int lencode, int* actuallen); 
    int __stdcall TH260_SetMeasControl(int devidx, int control, int startedge, int stopedge);
    int __stdcall TH260_SetTriggerOutput(int devidx, int period);

    int __stdcall TH260_ClearHistMem(int devidx);
    int __stdcall TH260_StartMeas(int devidx, int tacq);
    int __stdcall TH260_StopMeas(int devidx);
    int __stdcall TH260_CTCStatus(int devidx, int* ctcstatus);

    int __stdcall TH260_GetHistogram(int devidx, unsigned int *chcount, int channel, int clear);
    int __stdcall TH260_GetResolution(int devidx, double* resolution); 
    int __stdcall TH260_GetSyncRate(int devidx, int* syncrate);
    int __stdcall TH260_GetCountRate(int devidx, int channel, int* cntrate);
    int __stdcall TH260_GetFlags(int devidx, int* flags);
    int __stdcall TH260_GetElapsedMeasTime(int devidx, double* elapsed);
    int __stdcall TH260_GetSyncPeriod(int devidx, double* period);

    int __stdcall TH260_GetWarnings(int devidx, int* warnings);
    int __stdcall TH260_GetWarningsText(int devidx, char* text, int warnings);
    int __stdcall TH260_GetHardwareDebugInfo(int devidx, char *debuginfo); 

    int __stdcall TH260_SetMarkerEdges(int devidx, int me1, int me2, int me3, int me4);
    int __stdcall TH260_SetMarkerEnable(int devidx, int en1, int en2, int en3, int en4);
    int __stdcall TH260_SetMarkerHoldoffTime(int devidx, int holdofftime);
    int __stdcall TH260_ReadFiFo(int devidx, unsigned int* buffer, int count, int* nactual);



