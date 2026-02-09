import dearpygui.dearpygui as dpg
from dopplerguesser.ui.live_view_tab import draw_live_view_tab
from dopplerguesser.ui.settings_tab import draw_settings_tab
from dopplerguesser.ui.clock_correction_tab import draw_clock_correction_tab
from dopplerguesser.ui.processing_tab import draw_processing_tab

dpg.create_context()

with dpg.window(tag="Primary Window"):
    with dpg.tab_bar():
        draw_live_view_tab()
        draw_settings_tab()
        draw_clock_correction_tab()
        draw_processing_tab()

dpg.create_viewport(title='Doppler Guesser', width=400, height=800)
dpg.setup_dearpygui()
dpg.show_viewport()

dpg.set_primary_window("Primary Window", True)

dpg.start_dearpygui()
dpg.destroy_context()
