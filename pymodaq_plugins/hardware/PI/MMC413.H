//------------------------------------------
// File     : MMC.H 
// Date     : 2007-12-12
//------------------------------------------
// add following include when using CVI LabWindows
// #include <cvidef.h>  

#ifdef __cplusplus
    extern "C" {
#endif

// This is the header that can be used with MMC.DLL
// for Mercury, Mercury-Step and RedStone controllers.
// To use the DLL, include the static import
// library MMC.LIB into the project

//-----------------------------------
// types
//-----------------------------------
typedef unsigned char BYTE;
typedef unsigned int WORD;

//-----------------------------------
// terminator characters
//-----------------------------------
#define LF 0x10;
#define CR 0x13;

//-----------------------------------
// Error Base Codes
//-----------------------------------
#define EBC_open         16;
#define EBC_setBuffer    32;
#define EBC_EOF          48;
#define EBC_getChar      64;
#define EBC_getString    80;
#define EBC_sendChar     96;
#define EBC_sendString  112;
#define EBC_sendStringE 128;
#define EBC_sendCommand 144;

//-----------------------------------
// Error offset codes
//-----------------------------------
#define ERR_readfile     1;
#define ERR_writefile    2;
#define ERR_timeout      3;
#define ERR_length       4;
#define ERR_content      5;
#define ERR_GetCommState 6;
#define ERR_SetCommState 7;
#define ERR_PurgeComm    8;
#define ERR_PortNumber   9;
#define ERR_handle      10;
#define ERR_axis        11;
#define ERR_parameter   12;

//-----------------------------------
// Function declarations 
//-----------------------------------

int __stdcall MMC_COM_open(int PortNumber, int baudrate);
int __stdcall MMC_COM_close(void);
int __stdcall MMC_COM_setBuffer(void);
int __stdcall MMC_COM_EOF(void);
int __stdcall MMC_COM_clear(void);
int __stdcall MMC_getChar(char *character);
int __stdcall MMC_getDLLversion(void);
int __stdcall MMC_getMacro(int macno,char *report);
int __stdcall MMC_getPos(void);
int __stdcall MDC_getPosErr(void);

int __stdcall MMC_getReport(char *command, char *report);
int __stdcall MMC_getSTB(int bytenumber);
int __stdcall MMC_getString(char *report, WORD count);
int __stdcall MMC_getStringCR(char *report);
int __stdcall MMC_getVal(int command_ID);
int __stdcall MMC_initNetwork(int maxAxis);
int __stdcall MMC_moveA(int axis, int position);
int __stdcall MMC_moveR(int axis, int shift);
int __stdcall MDC_moving(void);
int __stdcall MST_moving(void);

int __stdcall MMC_setDevice(int axis);
int __stdcall MMC_select(int axis);
int __stdcall MMC_sendChar(char character);
int __stdcall MMC_sendString(char *sendString);
int __stdcall MMC_sendCommand(char *command);
int __stdcall MDC_waitStop(void);
int __stdcall MST_waitStop(void);

int __stdcall RED_getJoy(int axis);
int __stdcall RED_getSCC(int command_ID);
int __stdcall RED_getReport(int axis, int command_ID, char *report);
int __stdcall RED_moving(void);
int __stdcall RED_waitStop(int axis);

#ifdef __cplusplus 
}
#endif
