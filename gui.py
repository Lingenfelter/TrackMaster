from dearpygui.core import *
from dearpygui.simple import *
import audioRecorder as aRec
from fileSystem import RecordFileSystem

currently_recording = False
x_range = [x for x in range(aRec.plotRecSize)]

# Filesystem head
file_head: RecordFileSystem

center_items = []
add_data('item_center_list', center_items)


def apply_centering():
    items = list(get_data("item_center_list"))
    if items:
        for item in items:
            container_width = get_item_rect_size(get_item_parent(item))[0]
            item_width, item_height = get_item_rect_size(item)
            set_item_height(f'{item}_container', int(item_height))
            pos = int((container_width / 2) - (item_width / 2))
            set_item_width(f'{item}_dummy', pos)


def center_item(name: str):
    with child(f'{name}_container', autosize_x=True, no_scrollbar=True, border=False):
        add_dummy(name=f'{name}_dummy')
        add_same_line(name=f'{name}_sameline')
        move_item(name, parent=f'{name}_container')
    items = list(get_data('item_center_list'))
    items.append(name)
    add_data('item_center_list', items)
    y_space = get_style_item_spacing()[1]
    set_item_style_var(f'{name}_container', mvGuiStyleVar_ItemSpacing, [0, y_space])


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
    data = aRec.get_plotRec()
    add_line_series('audio_plot', 'right channel', x_range, data[0], weight=2.5)
    add_line_series('audio_plot', 'left channel', x_range, data[1], weight=2.5, color=[155, 50, 50, 75])
    bounds = aRec.recording_threshold
    add_hline_series('audio_plot', 'bounds', [bounds, -bounds])


def get_song_info():
    data = aRec.song_info
    if data:
        set_value('artist', 'Artist:' + data[0])
        set_value('album', 'Album:' + data[1])
        set_value('song', 'Song:' + data[2])


def show_gui():
    with window('main'):
        with child('l_column', autosize_y=True):
            add_plot('audio_plot', label='', height=300, no_mouse_pos=True,
                     xaxis_no_tick_labels=True, yaxis_no_tick_labels=True, xaxis_no_tick_marks=True,
                     yaxis_no_tick_marks=True)
            set_plot_ylimits('audio_plot', -1, 1)

            add_button('rec/stop', label='Record', callback=toggle_recording, width=150, height=50)
            add_same_line()
            add_slider_float('volume', min_value=0, max_value=1, default_value=aRec.playbackVolume,
                             callback=send_volume, width=200)

        add_same_line()

        with child('r_column', autosize_x=True, autosize_y=True):
            with group('track_info'):
                add_drawing('album_image', width=200, height=200)
                draw_image('album_image', 'recordings/working/default.jpg', [0.0, 0.0], [200, 200])
                add_text('artist', default_value='Artist:')
                add_text('album', default_value='Album:')
                add_text('song', default_value='Song:')
            center_item('track_info')
            add_spacing(count=3)
            add_separator(name='r_panel_separator')
            add_spacing(count=3)
            with group('file_display'):
                add_text('File information')

    def resize(sender, data):
        x, y = get_main_window_size()
        l_column_width = int(x * 0.7)
        set_item_width('l_column', width=l_column_width)

    def on_close():
        if currently_recording:
            aRec.stop_recording()

    def update(sender, data):
        apply_centering()
        if currently_recording:
            get_plot_data()
            get_song_info()
            album_art = file_head.get_album_art()
            if album_art is not None:
                clear_drawing('album_image')
                draw_image('album_image', file_head.get_album_art(), [0.0, 0.0], [200, 200])
                file_head.album_art.updated = False

    # show_metrics()
    # show_documentation()

    set_render_callback(update)
    set_start_callback(resize)
    set_resize_callback(resize)
    set_exit_callback(on_close)

    set_main_window_size(1100, 700)
    set_main_window_pos(820, 0)
    set_main_window_title('Trackmaster')

    start_dearpygui(primary_window='main')
