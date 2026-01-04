#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: clock drift estimator
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from gnuradio import analog
from gnuradio import blocks
import math
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import network
from math import pi
import sip
import threading



class clock_drift_estimator(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "clock drift estimator", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("clock drift estimator")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "clock_drift_estimator")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 6e6
        self.freqshift = freqshift = 0

        ##################################################
        # Blocks
        ##################################################

        self._freqshift_range = qtgui.Range(-50000, 50000, 1, 0, 200)
        self._freqshift_win = qtgui.RangeWidget(self._freqshift_range, self.set_freqshift, "'freqshift'", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._freqshift_win)
        self.qtgui_number_sink_0 = qtgui.number_sink(
            gr.sizeof_float,
            0,
            qtgui.NUM_GRAPH_HORIZ,
            1,
            None # parent
        )
        self.qtgui_number_sink_0.set_update_time(0.10)
        self.qtgui_number_sink_0.set_title("")

        labels = ['', '', '', '', '',
            '', '', '', '', '']
        units = ['', '', '', '', '',
            '', '', '', '', '']
        colors = [("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
            ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]

        for i in range(1):
            self.qtgui_number_sink_0.set_min(i, -1)
            self.qtgui_number_sink_0.set_max(i, 1)
            self.qtgui_number_sink_0.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.qtgui_number_sink_0.set_label(i, "Data {0}".format(i))
            else:
                self.qtgui_number_sink_0.set_label(i, labels[i])
            self.qtgui_number_sink_0.set_unit(i, units[i])
            self.qtgui_number_sink_0.set_factor(i, factor[i])

        self.qtgui_number_sink_0.enable_autoscale(False)
        self._qtgui_number_sink_0_win = sip.wrapinstance(self.qtgui_number_sink_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_number_sink_0_win)
        self.network_tcp_source_0 = network.tcp_source.tcp_source(itemsize=gr.sizeof_short*1,addr='127.0.0.1',port=12345,server=False)
        self.network_tcp_sink_0 = network.tcp_sink(gr.sizeof_float, 1, '127.0.0.1', 12346,2)
        self.low_pass_filter_0 = filter.fir_filter_ccf(
            1,
            firdes.low_pass(
                1,
                samp_rate,
                2.5e6,
                1e6,
                window.WIN_HAMMING,
                6.76))
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_gr_complex*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_ff((samp_rate/(2*pi)))
        self.blocks_moving_average_xx_0 = blocks.moving_average_ff(1000, (1/1000), 4000, 1)
        self.blocks_keep_one_in_n_0 = blocks.keep_one_in_n(gr.sizeof_float*1, 600000)
        self.blocks_interleaved_short_to_complex_0 = blocks.interleaved_short_to_complex(False, False,2**15)
        self.blocks_freqshift_cc_0 = blocks.rotator_cc(2.0*math.pi*freqshift/samp_rate)
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_float*1, '/Users/tedvtorov/Desktop/recordings/gr_scripts/clock_drift_out.txt', False)
        self.blocks_file_sink_0.set_unbuffered(False)
        self.blocks_correctiq_0 = blocks.correctiq()
        self.analog_pll_freqdet_cf_0 = analog.pll_freqdet_cf(0.0004, 0.2, (-0.2))


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_pll_freqdet_cf_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.blocks_correctiq_0, 0), (self.blocks_throttle2_0, 0))
        self.connect((self.blocks_freqshift_cc_0, 0), (self.low_pass_filter_0, 0))
        self.connect((self.blocks_interleaved_short_to_complex_0, 0), (self.blocks_correctiq_0, 0))
        self.connect((self.blocks_keep_one_in_n_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.blocks_keep_one_in_n_0, 0), (self.network_tcp_sink_0, 0))
        self.connect((self.blocks_moving_average_xx_0, 0), (self.blocks_keep_one_in_n_0, 0))
        self.connect((self.blocks_moving_average_xx_0, 0), (self.qtgui_number_sink_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.blocks_moving_average_xx_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.blocks_freqshift_cc_0, 0))
        self.connect((self.low_pass_filter_0, 0), (self.analog_pll_freqdet_cf_0, 0))
        self.connect((self.network_tcp_source_0, 0), (self.blocks_interleaved_short_to_complex_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "clock_drift_estimator")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_freqshift_cc_0.set_phase_inc(2.0*math.pi*self.freqshift/self.samp_rate)
        self.blocks_multiply_const_vxx_0.set_k((self.samp_rate/(2*pi)))
        self.blocks_throttle2_0.set_sample_rate(self.samp_rate)
        self.low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, 2.5e6, 1e6, window.WIN_HAMMING, 6.76))

    def get_freqshift(self):
        return self.freqshift

    def set_freqshift(self, freqshift):
        self.freqshift = freqshift
        self.blocks_freqshift_cc_0.set_phase_inc(2.0*math.pi*self.freqshift/self.samp_rate)




def main(top_block_cls=clock_drift_estimator, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
