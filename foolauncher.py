#!/usr/bin/env python
import i3
from gi.repository import Gtk, Gdk
from gio import app_info_get_all

I3_VETO_NAMES=("topdock","bottomdock","__i3_scratch")

def filter_func(model, treeiter, user_data):
    query = entry.get_text().lower()
    value = model.get_value(treeiter, 0).lower()
    for q in query.split(" "):
        if q not in value: return False
    return True

def sort_func(model, a, b, user_data):
    a_id, b_id = model.get_value(a,1), model.get_value(b,1)
    a_name, b_name = model.get_value(a,0), model.get_value(b,0)
    if a_id == -1 and b_id != -1:
        return -1
    elif a_id == -1 and b_id == -1 or (a_id > -1 and b_id > -1):
        if a_name.lower() == b_name.lower(): return 0
        elif a_name.lower() > b_name.lower(): return -1
        else: return 1
    elif a_id > -1 and b_id == -1:
        return 1

def selectFirst():
    if filterStore.get_iter_first():
        tree.get_selection().select_iter(filterStore.get_iter_first())
        tree.set_cursor( filterStore.get_path( filterStore.get_iter_first() ) )

def refilter(*_):
    filterStore.refilter()
    selectFirst()

def activate(*_):
    model, treeiter = tree.get_selection().get_selected()
    conid = model.get_value(treeiter, 1)
    if conid > -1:
        i3.command("[con_id={conid}] focus".format(conid=conid))
    else:
        app_id = model.get_value(treeiter, 2)
        i3.command("exec %s"%apps[app_id].get_executable())
    Gtk.main_quit()

def win_key_press(widget,event):
    if Gdk.keyval_name( event.keyval ) == "Escape":
        Gtk.main_quit()
    elif not entry.is_focus(): 
        if event.string:
            entry.grab_focus()

def tree_move_up(widget,event):
    if Gdk.keyval_name( event.keyval ) == "Up":
        (model, it) = widget.get_selection().get_selected()
        if model.get_string_from_iter(it) == "1":
            itFst = model.get_iter_first()
            tree.set_cursor( model.get_path( model.get_iter_first() ) )
            entry.grab_focus()

def entry_move_down(widget,event):
    if Gdk.keyval_name( event.keyval ) == "Down":
        (model, it) = tree.get_selection().get_selected()
        itNext = model.iter_next(it)
        path = model.get_path(itNext)
        tree.set_cursor(path)

win = Gtk.Window(title="foo Application Launcher")
box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
win.add(box)

entry = Gtk.Entry()
box.pack_start(entry, False, False, 0)

store = Gtk.ListStore(str,int,str,str)
apps = dict()

filterStore = Gtk.TreeModelFilter(child_model=store)
tree = Gtk.TreeView(filterStore)
tree.set_enable_search(False)
tree.set_headers_visible(False)
tree.append_column(Gtk.TreeViewColumn("", Gtk.CellRendererPixbuf(), stock_id=3))
tree.append_column(Gtk.TreeViewColumn("", Gtk.CellRendererText(), text=0))
box.pack_start(Gtk.ScrolledWindow(child=tree), True, True, 0)

store.set_sort_func(0, sort_func, None)
store.set_sort_column_id(0, Gtk.SortType.DESCENDING)
filterStore.set_visible_func(filter_func)

entry.connect("changed", refilter)
entry.connect("activate", activate)
entry.connect("key-press-event", entry_move_down)
tree.connect("row-activated", activate)
tree.connect("key-press-event", tree_move_up)
win.connect("key-press-event", win_key_press)
win.connect("delete-event", lambda *_: Gtk.main_quit())
win.connect("focus-out-event", lambda *_: Gtk.main_quit())

win.set_type_hint(Gdk.WindowTypeHint.DIALOG)
win.set_default_size(400,300)
win.show_all()

def fill_apps(*_):
    for con in i3.filter(type=4):
        if con['name'] in I3_VETO_NAMES: continue
        store.append(["Workspace: " + con['name'], con['id'], "","gtk-home"])
    for app in app_info_get_all():
        store.append([app.get_name(), -1, app.get_id(), "gtk-execute"])
        apps[app.get_id()]=app
    for con in i3.filter(type=2,nodes=[]):
        if con['name'] in I3_VETO_NAMES: continue
        store.append(["Window: " + con['name'], con['id'], "","gtk-fullscreen"])
    selectFirst()

Gdk.threads_add_idle(0, fill_apps, None)
Gtk.main()
