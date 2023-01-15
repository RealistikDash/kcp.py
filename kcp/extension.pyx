from libc.stdint cimport *
from cpython.bytes cimport PyBytes_FromStringAndSize
from cpython cimport bool

from .exceptions import *

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
    void ikcp_setoutput(IKCPCB *kcp, int32_t (*output)(const char* buf, int32_t len, IKCPCB* kcp, void* user))

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

    void ikcp_wndsize(IKCPCB *kcp, int32_t sndwnd, int32_t rcvwnd)

cdef int32_t set_outbound_data(const char* buf, int32_t len, IKCPCB* kcp, void* user) with gil:
    cdef OldKCPControl control = <OldKCPControl>user

    # Convert buffer to bytes
    cdef bytes data = PyBytes_FromStringAndSize(buf, len)
    control.outbound = data

cdef bytearray receive_full_data(OldKCPControl control):
    cdef bytearray data = bytearray()
    cdef char buffer[1024]
    cdef int32_t length

    while True:
        length = ikcp_recv(control.kcp, buffer, 1024)
        if length < 0:
            break

        if length != 1024:
            data.extend(buffer[:length])
            break

        data.extend(buffer)

    return data

# OOP Python interface

# DEPRECATED
cdef class OldKCPControl:
    cdef IKCPCB* kcp
    cdef bytes outbound
    cdef public str token

    def __init__(self, str token, int32_t conv):
        self.kcp = ikcp_create(conv, <void*>self)
        ikcp_setoutput(self.kcp, set_outbound_data)
        self.outbound = b""
        self.token = token

    def __dealloc__(self):
        ikcp_release(self.kcp)

    # Direct C APIs.
    cdef int32_t c_send(self, const char* buffer, int32_t length):
        return ikcp_send(self.kcp, buffer, length)

    cdef int32_t c_receive(self, char* buffer, int32_t length):
        return ikcp_input(self.kcp, buffer, length)

    cdef void c_update(self, uint32_t current):
        ikcp_update(self.kcp, current)

    cdef void c_flush(self):
        ikcp_flush(self.kcp)

    cdef int32_t c_wait_send(self):
        return ikcp_waitsnd(self.kcp)

    # Sets the MTU for KCP (I dont know what this is)
    cdef int32_t c_set_mtu(self, int32_t mtu):
        return ikcp_setmtu(self.kcp, mtu)

    # Sets the window size for KCP
    cdef void c_set_window_size(self, int32_t send, int32_t receive):
        ikcp_wndsize(self.kcp, send, receive)

    # Sets the delay mode for KCP
    cdef void c_set_nodelay(self, int32_t nodelay, int32_t interval, int32_t resend, int32_t nc):
        ikcp_nodelay(self.kcp, nodelay, interval, resend, nc)

    cdef make_outbound_copy(self):
        # Dont do antything if there is no outbound data
        if not self.outbound:
            return None
        cdef bytes data = self.outbound
        self.outbound = b""
        return data

    # Python APIs
    cpdef void send(self, bytes buffer):
        cdef int32_t length = len(buffer)
        cdef char* buf = <char*>buffer
        cdef int32_t res = self.c_send(buf, length)

        if res == -1:
            raise KCPBufferError
        elif res < -1:
            raise KCPException(res)

    cpdef void receive(self, bytes buffer):
        cdef int32_t length = len(buffer)
        cdef char* buf = <char*>buffer
        cdef int32_t res = self.c_receive(buf, length)

        if res == -1:
            raise KCPConvMismatchError
        elif res < 0:
            raise KCPInputError(res)

    # This MAY return outbound
    cpdef bytes update(self, ts_ms: Optional[int] = None):
        # TODO: Use way faster clock
        if ts_ms is None:
            ts_ms = time.perf_counter_ns() // 1000000
        self.c_update(ts_ms)

        return self.make_outbound_copy()

    cpdef int get_queued_packets(self):
        return self.c_wait_send()

    cpdef bytes read_outbound(self):
        self.c_flush()
        return self.make_outbound_copy()

    cpdef bytearray read_inbound(self):
        return receive_full_data(self)

    cpdef no_delay(self, bool nodelay, int32_t interval, int32_t resend, int32_t nc):
        self.c_set_nodelay(<int32_t>nodelay, interval, resend, nc)

    # Maximum Transmission Unit
    cpdef set_mtu(self, int32_t mtu):
        self.c_set_mtu(mtu)


## NEW KCP
import time

#OutboundDataHandler = Callable[[KCP, bytes], None]

# Internally used in KCP whenever data is ready to be sent.
cdef int32_t pending_outbound_data(const char* buf, int32_t len, IKCPCB* kcp, void* user) with gil:
    cdef KCP control = <KCP>user
    control.handle_output(buf, len)

cpdef get_current_time_ms():
    # Use perf counter as it isnt affected by system time changes.
    return time.perf_counter_ns() // 1000000


cdef class KCP:
    cdef IKCPCB* kcp
    # Correctly annotating this causes a cython compiler crash LOL
    cdef _data_handler # type: Optional[OutboundDataHandler]
    cdef public identity_token

    def __init__(
        self,
        int conv_id,
        int max_transmission = 1400,
        bool no_delay = False,
        int update_interval = 100,
        int resend_count = 2,
        bool no_congestion_control = False,
        identity_token = None,
    ):
        self._data_handler = None # Set by decorator.
        # Create base KCP object, passing self as the user data to be passed to the callback.
        self.kcp = ikcp_create(
            conv_id,
            <void*>self,
        )

        ikcp_setoutput(self.kcp, pending_outbound_data)

        # Set the perf config
        self.set_performance_options(
            no_delay,
            update_interval,
            resend_count,
            no_congestion_control
        )

        self.set_maximum_transmission(max_transmission)

        self.identity_token = identity_token

    cdef handle_output(self, const char* buf, int32_t len):
        # Create a bytes object from the buffer.
        cdef bytes data = PyBytes_FromStringAndSize(buf, len)
        self._data_handler(self, data)

    # Setting the handler for outbound data.
    def include_outbound_handler(self, handler):
        self._data_handler = handler

    # Decorator
    def outbound_handler(self, handler):
        self.include_outbound_handler(handler)
        return handler

    # I/O functions
    cpdef enqueue(self, bytes data):
        if self._data_handler is None:
            raise KCPException(
                "No outbound handler set. Cannot enqueue data. "
                "Try using the outbound_handler decorator."
            )

        cdef int32_t length = len(data)
        cdef char* buf = <char*>data
        cdef int32_t res = ikcp_send(self.kcp, buf, length)

        # Error handling
        if res == -1:
            raise KCPBufferError("Buffer enqueued is empty.")

        # TODO: Add exceptions for other errors.
        elif res < -1:
            raise KCPException(res)

    cpdef receive(self, bytes data):
        cdef int32_t length = len(data)
        cdef char* buf = <char*>data
        cdef int32_t res = ikcp_input(self.kcp, buf, length)

        # Error handling
        if res == -1:
            # TODO: This can also mean just invalid data.
            raise KCPConvMismatchError("The conversation ID does not match.")
        elif res < -1:
            raise KCPException(res)

    # Gets the raw data received by KCP.
    cpdef bytearray get_received(self):
        # Check if there is any data to be received.
        cdef int length = ikcp_peeksize(self.kcp)
        if length == -1:
            return bytearray()

        # Create a buffer to store the data.
        cdef buf = bytearray(length)

        # Receive the data.
        cdef int32_t res = ikcp_recv(self.kcp, buf, length)
        if res < 0:
            # Theoretically this should never happen.
            raise KCPException(res)

        return buf


    # Updates timing information for KCP, may call the outbound handler. Should be regularly called.
    cpdef update(self, ts_ms: Optional[int] = None):
        # Use python's time module if no timestamp is provided.
        if ts_ms is None:
            ts_ms = get_current_time_ms()

        ikcp_update(self.kcp, ts_ms)

    # Checks when the next update should be called (in ms).
    cpdef int32_t update_check(self, ts_ms: Optional[int] = None):
        # Use python's time module if no timestamp is provided.
        if ts_ms is None:
            ts_ms = get_current_time_ms()

        return ikcp_check(self.kcp, ts_ms)

    # Flushes the outbound data, calling the outbound handler if there is data.
    cpdef flush(self):
        ikcp_flush(self.kcp)

    # Connection settings functions
    # Sets the size of the max packet size that can be sent.
    cpdef set_maximum_transmission(self, int max_transmission):
        ikcp_setmtu(self.kcp, max_transmission)

    # Sets performance options for KCP.
    cpdef set_performance_options(
        self,
        bool no_delay,
        int update_interval,
        int resend_count,
        bool no_congestion_control,
    ):
        ikcp_nodelay(
            self.kcp,
            <int32_t>no_delay,
            update_interval,
            resend_count,
            <int32_t>no_congestion_control
        )

    # Statistics functions
    # Returns the number of packets waiting to be sent.
    cpdef int32_t get_outbound_packets(self):
        return ikcp_waitsnd(self.kcp)

    # Returns the size of the next packet to be received.
    cpdef int32_t get_next_packet_size(self):
        return ikcp_peeksize(self.kcp)

    cpdef update_loop(self):
        # TODO: Perhaps add a way to stop the loop.
        cdef int32_t next_update
        while True:
            next_update = self.update_check()
            time.sleep(next_update / 1000)
            self.update()
