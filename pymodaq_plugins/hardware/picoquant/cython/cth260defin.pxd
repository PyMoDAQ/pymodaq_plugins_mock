# cth260defin.pxd

cdef extern from "th260defin.h":

    char * LIB_VERSION = "3.1"

    enum: MAXSTRLEN_LIBVER =8 # max string length of *version in TH260_GetLibraryVersion
    enum: MAXSTRLEN_ERRSTR  =    40 # max string length of *errstring in TH260_GetErrorString
    enum: MAXSTRLEN_SERIAL   =    8 # max string length of *serial in TH260_OpenDevice and TH260_GetSerialNumber
    enum: MAXSTRLEN_MODEL  =     16 # max string length of *model in TH260_GetHardwareInfo
    enum: MAXSTRLEN_PART   =      8 # max string length of *partno in TH260_GetHardwareInfo
    enum: MAXSTRLEN_VERSION =    16 # max string length of *version in TH260_GetHardwareInfo
    enum: MAXSTRLEN_WRNTXT =  16384 # max string length of *text in TH260_GetWarningsText

    char * HWIDENT_PICO  =  "TimeHarp 260 P" # as returned by TH260_GetHardwareInfo
    char * HWIDENT_NANO =   "TimeHarp 260 N" # as returned by TH260_GetHardwareInfo

    enum: MAXDEVNUM	= 4	    # max number of TH260 devices

    enum: MAXINPCHAN =  2	    # max number of detector input channels

    enum: MAXBINSTEPS=	22	    # get actual number via TH260_GetBaseResolution() !

    enum: MAXHISTLEN =  32768	# max number of histogram bins
    enum: MAXLENCODE=  5		# max length code histo mode

    enum: TTREADMAX  = 131072  # 128K event records can be read in one chunk
    enum: TTREADMIN =  128     # 128 records = minimum buffer size that must be provided

    enum: MODE_HIST=	0		# for TH260_Initialize
    enum: MODE_T2	=	2
    enum: MODE_T3	=	3

    enum: MEASCTRL_SINGLESHOT_CTC=		0 # for TH260_SetMeasControl, 0=default
    enum: MEASCTRL_C1_GATE	=		1
    enum: MEASCTRL_C1_START_CTC_STOP=	2
    enum: MEASCTRL_C1_START_C2_STOP=	3

    enum: EDGE_RISING  = 1			# for TH260_SetXxxEdgeTrg, TH260_SetMeasControl and TH260_SetMarkerEdges
    enum: EDGE_FALLING = 0

    enum: TIMINGMODE_HIRES = 0		# used by TH260_SetTimingMode
    enum: TIMINGMODE_LORES = 1		# used by TH260_SetTimingMode

    enum: FEATURE_DLL   =    0x0001  # DLL License available
    enum: FEATURE_TTTR   =   0x0002  # TTTR mode available
    enum: FEATURE_MARKERS =  0x0004  # Markers available
    enum: FEATURE_LOWRES  =  0x0008  # Long range mode available
    enum: FEATURE_TRIGOUT=   0x0010  # Trigger output available
    enum: FEATURE_PROG_TD =  0x0020  # Programmable deadtime available

    enum: FLAG_OVERFLOW  =   0x0001  # histo mode only
    enum: FLAG_FIFOFULL =    0x0002
    enum: FLAG_SYNC_LOST  =  0x0004  # T3 mode only
    enum: FLAG_EVTS_DROPPED= 0x0008  # dropped events due to high input rate
    enum: FLAG_SYSERROR =    0x0010  # hardware error, must contact support
    enum: FLAG_SOFTERROR =   0x0020  # software error, must contact support

    enum: SYNCDIVMIN	=	1		# for TH260_SetSyncDiv
    enum: SYNCDIVMAX=	8

    enum: TRGLVLMIN	=-1200		# mV  TH260 Nano only
    enum: TRGLVLMAX	= 1200		# mV  TH260 Nano only

    enum: CFDLVLMIN=	-1200		# mV  TH260 Pico only
    enum: CFDLVLMAX	=	0		# mV  TH260 Pico only
    enum: CFDZCMIN	=  -40		# mV  TH260 Pico only
    enum: CFDZCMAX	=	0		# mV  TH260 Pico only

    enum: CHANOFFSMIN= -99999		# ps, for TH260_SetSyncChannelOffset and TH260_SetInputChannelOffset
    enum: CHANOFFSMAX = 99999		# ps

    enum: OFFSETMIN=	0			# ns, for TH260_SetOffset
    enum: OFFSETMAX	=100000000	# ns

    enum: ACQTMIN	=	1			# ms, for TH260_StartMeas
    enum: ACQTMAX	=	360000000	# ms  (100*60*60*1000ms = 100h)

    enum: STOPCNTMIN = 1			# for TH260_SetStopOverflow
    enum: STOPCNTMAX = 4294967295  # 32 bit is mem max

    enum: TRIGOUTMIN = 0			# for TH260_SetTriggerOutput, 0=off
    enum: TRIGOUTMAX = 16777215	# in units of 100ns

    enum: HOLDOFFMIN = 0			# ns, for TH260_SetMarkerHoldoffTime
    enum: HOLDOFFMAX = 25500		# ns

    enum: TDCODEMIN=	0			# for TH260_SetDeadTime
    enum: TDCODEMAX	=7


    enum: WARNING_SYNC_RATE_ZERO			=	0x0001
    enum: WARNING_SYNC_RATE_VERY_LOW		=	0x0002
    enum: WARNING_SYNC_RATE_TOO_HIGH		=	0x0004
    enum: WARNING_INPT_RATE_ZERO			=	0x0010
    enum: WARNING_INPT_RATE_TOO_HIGH		=	0x0040
    enum: WARNING_INPT_RATE_RATIO			=	0x0100
    enum: WARNING_DIVIDER_GREATER_ONE		=	0x0200
    enum: WARNING_TIME_SPAN_TOO_SMALL		=	0x0400
    enum: WARNING_OFFSET_UNNECESSARY		=	0x0800
    enum: WARNING_DIVIDER_TOO_SMALL			=0x1000
    enum: WARNING_COUNTS_DROPPED			=	0x2000
