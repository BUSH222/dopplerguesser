# type: ignore

# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: frequency_estimator_v2
# GNU Radio version: 3.10.12.0

from gnuradio import analog
from gnuradio import blocks
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import network
from math import pi
import threading



class frequency_estimator_v2(gr.top_block):

    def __init__(self, remove_dc=1, samp_rate=5e6):
        gr.top_block.__init__(self, "frequency_estimator_v2", catch_exceptions=True)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Parameters
        ##################################################
        self.remove_dc = remove_dc
        self.samp_rate = samp_rate

        ##################################################
        # Variables
        ##################################################
        self.max_expected_doppler = max_expected_doppler = 70e3
        self.N = N = 1000

        ##################################################
        # Blocks
        ##################################################

        self.network_tcp_source_0 = network.tcp_source.tcp_source(itemsize=gr.sizeof_short*1,addr='127.0.0.1',port=12345,server=False)
        self.network_tcp_sink_0 = network.tcp_sink(gr.sizeof_float, 1, '127.0.0.1', 12346,2)
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_multiply_const_vxx_1_0 = blocks.multiply_const_cc(remove_dc)
        self.blocks_multiply_const_vxx_1 = blocks.multiply_const_cc(1-remove_dc)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_ff((samp_rate/(2*pi)))
        self.blocks_moving_average_xx_0 = blocks.moving_average_ff((int(samp_rate/N)), (1/int(samp_rate/N)), 4000, 1)
        self.blocks_keep_one_in_n_0 = blocks.keep_one_in_n(gr.sizeof_float*1, (int(samp_rate/N)))
        self.blocks_interleaved_short_to_complex_0 = blocks.interleaved_short_to_complex(False, False,2**15)
        self.blocks_correctiq_0 = blocks.correctiq()
        self.blocks_add_xx_0 = blocks.add_vcc(1)
        self.analog_pll_freqdet_cf_0 = analog.pll_freqdet_cf((pi/10000), (2*pi*max_expected_doppler/samp_rate), (-2*pi*max_expected_doppler/samp_rate))


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_pll_freqdet_cf_0, 0), (self.blocks_moving_average_xx_0, 0))
        self.connect((self.blocks_add_xx_0, 0), (self.analog_pll_freqdet_cf_0, 0))
        self.connect((self.blocks_correctiq_0, 0), (self.blocks_multiply_const_vxx_1_0, 0))
        self.connect((self.blocks_interleaved_short_to_complex_0, 0), (self.blocks_throttle2_0, 0))
        self.connect((self.blocks_keep_one_in_n_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.blocks_moving_average_xx_0, 0), (self.blocks_keep_one_in_n_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.network_tcp_sink_0, 0))
        self.connect((self.blocks_multiply_const_vxx_1, 0), (self.blocks_add_xx_0, 0))
        self.connect((self.blocks_multiply_const_vxx_1_0, 0), (self.blocks_add_xx_0, 1))
        self.connect((self.blocks_throttle2_0, 0), (self.blocks_correctiq_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.blocks_multiply_const_vxx_1, 0))
        self.connect((self.network_tcp_source_0, 0), (self.blocks_interleaved_short_to_complex_0, 0))


    def get_remove_dc(self):
        return self.remove_dc

    def set_remove_dc(self, remove_dc):
        self.remove_dc = remove_dc
        self.blocks_multiply_const_vxx_1.set_k(1-self.remove_dc)
        self.blocks_multiply_const_vxx_1_0.set_k(self.remove_dc)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.analog_pll_freqdet_cf_0.set_max_freq((2*pi*self.max_expected_doppler/self.samp_rate))
        self.analog_pll_freqdet_cf_0.set_min_freq((-2*pi*self.max_expected_doppler/self.samp_rate))
        self.blocks_keep_one_in_n_0.set_n((int(self.samp_rate/self.N)))
        self.blocks_moving_average_xx_0.set_length_and_scale((int(self.samp_rate/self.N)), (1/int(self.samp_rate/self.N)))
        self.blocks_multiply_const_vxx_0.set_k((self.samp_rate/(2*pi)))
        self.blocks_throttle2_0.set_sample_rate(self.samp_rate)

    def get_max_expected_doppler(self):
        return self.max_expected_doppler

    def set_max_expected_doppler(self, max_expected_doppler):
        self.max_expected_doppler = max_expected_doppler
        self.analog_pll_freqdet_cf_0.set_max_freq((2*pi*self.max_expected_doppler/self.samp_rate))
        self.analog_pll_freqdet_cf_0.set_min_freq((-2*pi*self.max_expected_doppler/self.samp_rate))

    def get_N(self):
        return self.N

    def set_N(self, N):
        self.N = N
        self.blocks_keep_one_in_n_0.set_n((int(self.samp_rate/self.N)))
        self.blocks_moving_average_xx_0.set_length_and_scale((int(self.samp_rate/self.N)), (1/int(self.samp_rate/self.N)))



def argument_parser():
    parser = ArgumentParser()
    parser.add_argument(
        "-d", "--remove-dc", dest="remove_dc", type=intx, default=1,
        help="Set remove_dc [default=%(default)r]")
    parser.add_argument(
        "-s", "--samp-rate", dest="samp_rate", type=eng_float, default=eng_notation.num_to_str(5e6),
        help="Set samp_rate [default=%(default)r]")
    return parser


def main(top_block_cls=frequency_estimator_v2, options=None):
    if options is None:
        options = argument_parser().parse_args()

    tb = top_block_cls(remove_dc=options.remove_dc, samp_rate=options.samp_rate)

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
