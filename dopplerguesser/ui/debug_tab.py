import dearpygui.dearpygui as dpg
import dearpygui.demo as demo


def draw_debug_tab():
    with dpg.tab(label="Debug"):
        dpg.add_text("Show demo window")
        dpg.add_button(label="Open Demo", width=-1,
                       callback=lambda: demo.show_demo())

        with dpg.collapsing_header(label="Logs"):
            dpg.add_input_text(multiline=True, readonly=True, height=100,
                               default_value="[System] Ready.\n[System] Loaded modules.")
