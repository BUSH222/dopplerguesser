# type: ignore

# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: clock drift estimator
# GNU Radio version: 3.10.12.0

from gnuradio import analog
from gnuradio import blocks
from gnuradio import gr
import sys
import signal
from gnuradio import network
from math import pi
import threading
from dopplerguesser.misc.rigctl_query import query_rigctl


class clock_drift_estimator(gr.top_block):

    def __init__(self, rigctl_samp_rate=2e6):
        gr.top_block.__init__(self, "clock drift estimator", catch_exceptions=True)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = int(rigctl_samp_rate)

        ##################################################
        # Blocks
        ##################################################

        self.network_tcp_source_0 = network.tcp_source.tcp_source(itemsize=gr.sizeof_short*1,
                                                                  addr='127.0.0.1',
                                                                  port=12345,
                                                                  server=False)
        self.network_tcp_sink_0 = network.tcp_sink(gr.sizeof_float,
                                                   1, '127.0.0.1', 12346, 2)
        self.blocks_throttle2_0 = blocks.throttle(gr.sizeof_gr_complex*1,
                                                  samp_rate, True,
                                                  0 if "auto" == "auto" else
                                                  max(int(float(0.1) * samp_rate)if "auto" == "time" else int(0.1), 1))
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_ff((samp_rate/(2*pi)))
        self.blocks_moving_average_xx_0 = blocks.moving_average_ff(1000, (1/1000), 4000, 1)
        self.blocks_keep_one_in_n_0 = blocks.keep_one_in_n(gr.sizeof_float*1, int(samp_rate/100))
        self.blocks_interleaved_short_to_complex_0 = blocks.interleaved_short_to_complex(False, False, 2**15)
        self.blocks_correctiq_0 = blocks.correctiq()
        self.analog_pll_freqdet_cf_0 = analog.pll_freqdet_cf(0.0004, 0.2, (-0.2))

        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_pll_freqdet_cf_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.blocks_correctiq_0, 0), (self.blocks_throttle2_0, 0))
        self.connect((self.blocks_interleaved_short_to_complex_0, 0), (self.blocks_correctiq_0, 0))
        self.connect((self.blocks_keep_one_in_n_0, 0), (self.network_tcp_sink_0, 0))
        self.connect((self.blocks_moving_average_xx_0, 0), (self.blocks_keep_one_in_n_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.blocks_moving_average_xx_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.analog_pll_freqdet_cf_0, 0))
        self.connect((self.network_tcp_source_0, 0), (self.blocks_interleaved_short_to_complex_0, 0))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_multiply_const_vxx_0.set_k((self.samp_rate/(2*pi)))
        self.blocks_throttle2_0.set_sample_rate(self.samp_rate)


def main(top_block_cls=clock_drift_estimator, options=None):
    frequency, bandwidth = query_rigctl()
    if frequency is None or bandwidth is None:
        print("Could not query rigctl for sample rate. Using default 2 MHz.")
        rigctl_samp_rate = 2e6
    else:
        rigctl_samp_rate = bandwidth
    tb = top_block_cls(rigctl_samp_rate=rigctl_samp_rate)

    tb.start()
    tb.flowgraph_started.set()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    tb.wait()


if __name__ == '__main__':
    main()
