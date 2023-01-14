from libc.stdint cimport *
import time

cdef extern from "ikcp.h":
    # Structures
    struct IQUEUEHEAD:
        # Contents are unnecessary for our use case
        pass

    # KCP Control Object
    struct IKCPCB:
        uint32_t conv # Used to verify data is from the correct connection
        uint32_t mtu
        uint32_t mss
        uint32_t state
        uint32_t snd_una
        uint32_t snd_nxt
        uint32_t rcv_nxt
        uint32_t ts_recent
        uint32_t ts_lastack
        uint32_t ssthresh
        int32_t rx_rttval
        int32_t rx_srtt
        int32_t rx_rto
        int32_t rx_minrto
        uint32_t snd_wnd
        uint32_t rcv_wnd
        uint32_t rmt_wnd
        uint32_t cwnd
        uint32_t probe
        uint32_t current
        uint32_t interval
        uint32_t ts_flush
        uint32_t xmit
        uint32_t nrcv_buf
        uint32_t nsnd_buf
        uint32_t nrcv_que
        uint32_t nsnd_que
        uint32_t nodelay
        uint32_t updated
        uint32_t ts_probe
        uint32_t probe_wait
        uint32_t dead_link
        uint32_t incr
        IQUEUEHEAD snd_queue
        IQUEUEHEAD rcv_queue
        IQUEUEHEAD snd_buf
        IQUEUEHEAD rcv_buf
        uint32_t* acklist
        uint32_t ackcount
        uint32_t ackblock
        void* user # Just used to identify the connection it seems?
        char* buffer
        int32_t fastresend
        int32_t fastlimit
        int32_t nocwnd
        int32_t stream
        int32_t logmask
        int32_t (*output)(const char* buf, int len, IKCPCB* kcp, void *user)
        void (*writelog)(const char* log, IKCPCB* kcp, void* user);

    # Functions

    # Create KCP Control Object. User is passed to output callback.
    IKCPCB* ikcp_create(uint32_t conv, void* user)

    # Release KCP Control Object
    void ikcp_release(IKCPCB *kcp)

    # Sets the output callback function for KCP
    void ikcp_setoutput(IKCPCB *kcp, int32_t (*output)(const char *buf, int len, IKCPCB* kcp, void* user))

    # (User API) Handles received KCP data
    int32_t ikcp_recv(IKCPCB *kcp, char* buffer, int32_t len)

    # (User API) Send KCP data
    int32_t ikcp_send(IKCPCB *kcp, const char* buffer, int32_t len)

    # Update KCP timing.
    void ikcp_update(IKCPCB *kcp, uint32_t current)

    # Gives time till next ikcp_update() call in ms.
    uint32_t ikcp_check(IKCPCB *kcp, uint32_t current)

    # Low level UDP packet input, call it when you receive a low level UDP packet
    int32_t ikcp_input(IKCPCB *kcp, const char *data, long size)

    # Flush pending data
    void ikcp_flush(IKCPCB *kcp)

    # Checks the size of the next message in the recv queue
    int32_t ikcp_peeksize(IKCPCB *kcp)

    # Sets the MTU for KCP
    int32_t ikcp_setmtu(IKCPCB *kcp, int32_t mtu)

    # Checks how many packets are waiting to be sent
    int32_t ikcp_waitsnd(IKCPCB *kcp)

    # ?
    int32_t ikcp_nodelay(IKCPCB *kcp, int32_t nodelay, int32_t interval, int32_t resend, int32_t nc)

# OOP Python interface
cdef class KCPControl:
    cdef IKCPCB* kcp

    def __cinit__(self):
        # TODO: Randomise conv
        self.kcp = ikcp_create(32, NULL)

    def __dealloc__(self):
        ikcp_release(self.kcp)

    # Direct C APIs.
    cdef int32_t c_receive(self, char* buffer, int32_t length):
        return ikcp_recv(self.kcp, buffer, length)

    cdef int32_t c_send(self, const char* buffer, int32_t length):
        return ikcp_send(self.kcp, buffer, length)

    cdef void c_update(self, uint32_t current):
        ikcp_update(self.kcp, current)

    cdef void c_flush(self):
        ikcp_flush(self.kcp)

    # Python API
    cpdef int receive(self, bytes buffer):
        cdef int32_t length = len(buffer)
        cdef char* buf = <char*>buffer
        return self.c_receive(buf, length)

    cpdef int send(self, bytes buffer):
        cdef int32_t length = len(buffer)
        cdef char* buf = <char*>buffer
        return self.c_send(buf, length)

    cpdef void update_cur(self):
        # TODO: Use way faster clock
        self.c_update(time.time_ns() // 1000000)
