#include <windows.h>
#include <MMC413.H>

/* The two macros below are used as error return codes */
/* in case the DLL does not load, or is missing one or */
/* more functions, respectively.  You must define them */
/* to whatever values are meaningful for your DLL.     */
#define kFailedToLoadDLLError     ???
#define kCouldNotFindFunction     ???

static HINSTANCE DLLHandle;

/* Declare the variables that hold the addresses of the function   */
/* pointers.                                                       */
static int (__stdcall *MMC_COM_open_Ptr)(int PortNumber, int baudrate);
static int (__stdcall *MMC_COM_close_Ptr)(void);
static int (__stdcall *MMC_COM_setBuffer_Ptr)(void);
static int (__stdcall *MMC_COM_EOF_Ptr)(void);
static int (__stdcall *MMC_COM_clear_Ptr)(void);
static int (__stdcall *MMC_getChar_Ptr)(char *character);
static int (__stdcall *MMC_getDLLversion_Ptr)(void);
static int (__stdcall *MMC_getMacro_Ptr)(int macno, char *report);
static int (__stdcall *MMC_getPos_Ptr)(void);
static int (__stdcall *MDC_getPosErr_Ptr)(void);
static int (__stdcall *MMC_getReport_Ptr)(char *command, char *report);
static int (__stdcall *MMC_getSTB_Ptr)(int bytenumber);
static int (__stdcall *MMC_getString_Ptr)(char *report, WORD count);
static int (__stdcall *MMC_getStringCR_Ptr)(char *report);
static int (__stdcall *MMC_getVal_Ptr)(int command_ID);
static int (__stdcall *MMC_initNetwork_Ptr)(int maxAxis);
static int (__stdcall *MMC_moveA_Ptr)(int axis, int position);
static int (__stdcall *MMC_moveR_Ptr)(int axis, int shift);
static int (__stdcall *MDC_moving_Ptr)(void);
static int (__stdcall *MST_moving_Ptr)(void);
static int (__stdcall *MMC_setDevice_Ptr)(int axis);
static int (__stdcall *MMC_select_Ptr)(int axis);
static int (__stdcall *MMC_sendChar_Ptr)(char character);
static int (__stdcall *MMC_sendString_Ptr)(char *sendString);
static int (__stdcall *MMC_sendCommand_Ptr)(char *command);
static int (__stdcall *MDC_waitStop_Ptr)(void);
static int (__stdcall *MST_waitStop_Ptr)(void);
static int (__stdcall *RED_getJoy_Ptr)(int axis);
static int (__stdcall *RED_getSCC_Ptr)(int command_ID);
static int (__stdcall *RED_getReport_Ptr)(int axis, int command_ID,
                                          char *report);
static int (__stdcall *RED_moving_Ptr)(void);
static int (__stdcall *RED_waitStop_Ptr)(int axis);


/* Load the DLL and get the addresses of the functions */
static int LoadDLLIfNeeded(void)
{
    if (DLLHandle)
        return 0;

    DLLHandle = LoadLibrary("MMC410.DLL");
    if (DLLHandle == NULL) {
        return kFailedToLoadDLLError;
        }

    if (!(MMC_COM_open_Ptr = (void*) GetProcAddress(DLLHandle, "MMC_COM_open")))
        goto FunctionNotFoundError;

    if (!(MMC_COM_close_Ptr = (void*) GetProcAddress(DLLHandle, "MMC_COM_close")))
        goto FunctionNotFoundError;

    if (!(MMC_COM_setBuffer_Ptr = (void*) GetProcAddress(DLLHandle, 
         "MMC_COM_setBuffer")))
        goto FunctionNotFoundError;

    if (!(MMC_COM_EOF_Ptr = (void*) GetProcAddress(DLLHandle, "MMC_COM_EOF")))
        goto FunctionNotFoundError;

    if (!(MMC_COM_clear_Ptr = (void*) GetProcAddress(DLLHandle, "MMC_COM_clear")))
        goto FunctionNotFoundError;

    if (!(MMC_getChar_Ptr = (void*) GetProcAddress(DLLHandle, "MMC_getChar")))
        goto FunctionNotFoundError;

    if (!(MMC_getDLLversion_Ptr = (void*) GetProcAddress(DLLHandle, 
         "MMC_getDLLversion")))
        goto FunctionNotFoundError;

    if (!(MMC_getMacro_Ptr = (void*) GetProcAddress(DLLHandle, "MMC_getMacro")))
        goto FunctionNotFoundError;

    if (!(MMC_getPos_Ptr = (void*) GetProcAddress(DLLHandle, "MMC_getPos")))
        goto FunctionNotFoundError;

    if (!(MDC_getPosErr_Ptr = (void*) GetProcAddress(DLLHandle, "MDC_getPosErr")))
        goto FunctionNotFoundError;

    if (!(MMC_getReport_Ptr = (void*) GetProcAddress(DLLHandle, "MMC_getReport")))
        goto FunctionNotFoundError;

    if (!(MMC_getSTB_Ptr = (void*) GetProcAddress(DLLHandle, "MMC_getSTB")))
        goto FunctionNotFoundError;

    if (!(MMC_getString_Ptr = (void*) GetProcAddress(DLLHandle, "MMC_getString")))
        goto FunctionNotFoundError;

    if (!(MMC_getStringCR_Ptr = (void*) GetProcAddress(DLLHandle, 
         "MMC_getStringCR")))
        goto FunctionNotFoundError;

    if (!(MMC_getVal_Ptr = (void*) GetProcAddress(DLLHandle, "MMC_getVal")))
        goto FunctionNotFoundError;

    if (!(MMC_initNetwork_Ptr = (void*) GetProcAddress(DLLHandle, 
         "MMC_initNetwork")))
        goto FunctionNotFoundError;

    if (!(MMC_moveA_Ptr = (void*) GetProcAddress(DLLHandle, "MMC_moveA")))
        goto FunctionNotFoundError;

    if (!(MMC_moveR_Ptr = (void*) GetProcAddress(DLLHandle, "MMC_moveR")))
        goto FunctionNotFoundError;

    if (!(MDC_moving_Ptr = (void*) GetProcAddress(DLLHandle, "MDC_moving")))
        goto FunctionNotFoundError;

    if (!(MST_moving_Ptr = (void*) GetProcAddress(DLLHandle, "MST_moving")))
        goto FunctionNotFoundError;

    if (!(MMC_setDevice_Ptr = (void*) GetProcAddress(DLLHandle, "MMC_setDevice")))
        goto FunctionNotFoundError;

    if (!(MMC_select_Ptr = (void*) GetProcAddress(DLLHandle, "MMC_select")))
        goto FunctionNotFoundError;

    if (!(MMC_sendChar_Ptr = (void*) GetProcAddress(DLLHandle, "MMC_sendChar")))
        goto FunctionNotFoundError;

    if (!(MMC_sendString_Ptr = (void*) GetProcAddress(DLLHandle, 
         "MMC_sendString")))
        goto FunctionNotFoundError;

    if (!(MMC_sendCommand_Ptr = (void*) GetProcAddress(DLLHandle, 
         "MMC_sendCommand")))
        goto FunctionNotFoundError;

    if (!(MDC_waitStop_Ptr = (void*) GetProcAddress(DLLHandle, "MDC_waitStop")))
        goto FunctionNotFoundError;

    if (!(MST_waitStop_Ptr = (void*) GetProcAddress(DLLHandle, "MST_waitStop")))
        goto FunctionNotFoundError;

    if (!(RED_getJoy_Ptr = (void*) GetProcAddress(DLLHandle, "RED_getJoy")))
        goto FunctionNotFoundError;

    if (!(RED_getSCC_Ptr = (void*) GetProcAddress(DLLHandle, "RED_getSCC")))
        goto FunctionNotFoundError;

    if (!(RED_getReport_Ptr = (void*) GetProcAddress(DLLHandle, "RED_getReport")))
        goto FunctionNotFoundError;

    if (!(RED_moving_Ptr = (void*) GetProcAddress(DLLHandle, "RED_moving")))
        goto FunctionNotFoundError;

    if (!(RED_waitStop_Ptr = (void*) GetProcAddress(DLLHandle, "RED_waitStop")))
        goto FunctionNotFoundError;

    return 0;

FunctionNotFoundError:
    FreeLibrary(DLLHandle);
    DLLHandle = 0;
    return kCouldNotFindFunction;
}


/* Glue Code for each of the DLL functions */



int __stdcall MMC_COM_open(int PortNumber, int baudrate)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_COM_open_Ptr)(PortNumber, baudrate);
}


int __stdcall MMC_COM_close(void)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_COM_close_Ptr)();
}


int __stdcall MMC_COM_setBuffer(void)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_COM_setBuffer_Ptr)();
}


int __stdcall MMC_COM_EOF(void)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_COM_EOF_Ptr)();
}


int __stdcall MMC_COM_clear(void)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_COM_clear_Ptr)();
}


int __stdcall MMC_getChar(char *character)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_getChar_Ptr)(character);
}


int __stdcall MMC_getDLLversion(void)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_getDLLversion_Ptr)();
}


int __stdcall MMC_getMacro(int macno, char *report)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_getMacro_Ptr)(macno, report);
}


int __stdcall MMC_getPos(void)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_getPos_Ptr)();
}


int __stdcall MDC_getPosErr(void)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MDC_getPosErr_Ptr)();
}


int __stdcall MMC_getReport(char *command, char *report)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_getReport_Ptr)(command, report);
}


int __stdcall MMC_getSTB(int bytenumber)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_getSTB_Ptr)(bytenumber);
}


int __stdcall MMC_getString(char *report, WORD count)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_getString_Ptr)(report, count);
}


int __stdcall MMC_getStringCR(char *report)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_getStringCR_Ptr)(report);
}


int __stdcall MMC_getVal(int command_ID)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_getVal_Ptr)(command_ID);
}


int __stdcall MMC_initNetwork(int maxAxis)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_initNetwork_Ptr)(maxAxis);
}


int __stdcall MMC_moveA(int axis, int position)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_moveA_Ptr)(axis, position);
}


int __stdcall MMC_moveR(int axis, int shift)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_moveR_Ptr)(axis, shift);
}


int __stdcall MDC_moving(void)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MDC_moving_Ptr)();
}


int __stdcall MST_moving(void)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MST_moving_Ptr)();
}


int __stdcall MMC_setDevice(int axis)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_setDevice_Ptr)(axis);
}


int __stdcall MMC_select(int axis)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_select_Ptr)(axis);
}


int __stdcall MMC_sendChar(char character)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_sendChar_Ptr)(character);
}


int __stdcall MMC_sendString(char *sendString)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_sendString_Ptr)(sendString);
}


int __stdcall MMC_sendCommand(char *command)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MMC_sendCommand_Ptr)(command);
}


int __stdcall MDC_waitStop(void)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MDC_waitStop_Ptr)();
}


int __stdcall MST_waitStop(void)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*MST_waitStop_Ptr)();
}


int __stdcall RED_getJoy(int axis)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*RED_getJoy_Ptr)(axis);
}


int __stdcall RED_getSCC(int command_ID)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*RED_getSCC_Ptr)(command_ID);
}


int __stdcall RED_getReport(int axis, int command_ID, char *report)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*RED_getReport_Ptr)(axis, command_ID, report);
}


int __stdcall RED_moving(void)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*RED_moving_Ptr)();
}


int __stdcall RED_waitStop(int axis)
{
    int dllLoadError;

    if (dllLoadError = LoadDLLIfNeeded())
        return dllLoadError;
    return (*RED_waitStop_Ptr)(axis);
}

