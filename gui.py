from dearpygui.core import *
from dearpygui.simple import *
import audioRecorder as aRec

currently_recording = False


def toggle_recording():
    global currently_recording
    if currently_recording:
        set_item_label('rec/stop', 'Record')
        aRec.stop_recording()
        currently_recording = False
    else:
        set_item_label('rec/stop', 'Stop Recording')
        aRec.start_recording()
        currently_recording = True


def send_volume(sender, data):
    aRec.set_volume(get_value(sender))


def get_plot_data():
    if currently_recording:
        data = aRec.get_plotRec()
        set_value('ch_1', data[0])
        set_value('ch_2', data[1])
        x_range = [x for x in range(len(data[0]))]
        add_line_series('audio_plot', 'right channel', x_range, data[0], weight=2.5)
        add_line_series('audio_plot', 'left channel', x_range, data[1], weight=2.5, color=[155,50,50,75])


def show_gui():
    with window('main'):
        with child('l_column', autosize_y=True):
            add_plot('audio_plot', label='', height=300, no_mouse_pos=True,
                     xaxis_no_tick_labels=True, yaxis_no_tick_labels=True, xaxis_no_tick_marks=True, yaxis_no_tick_marks=True)
            set_plot_ylimits('audio_plot', -1, 1)

            add_button('rec/stop', label='Record', callback=toggle_recording, width=150, height=50)
            add_same_line()
            add_slider_float('volume', min_value=0, max_value=1, default_value=0.0,
                             callback=send_volume, width=200)

        add_same_line()

        with child('r_column', autosize_x=True, autosize_y=True):
            add_text('File side')

    def resize():
        l_column_width = int(get_main_window_size()[0] * (2 / 3))
        set_item_width('l_column', width=l_column_width)

    def on_close():
        if currently_recording:
            aRec.stop_recording()

    #show_metrics()
    #show_documentation()

    set_render_callback(get_plot_data)
    set_start_callback(resize)
    set_resize_callback(resize)
    set_exit_callback(on_close)

    start_dearpygui(primary_window='main')
