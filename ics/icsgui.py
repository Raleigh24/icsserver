
from Tkinter import *
from ttk import *
import network
from rpcinterface import RPCProxy


resource_dict = {'cg4529' : [
                    'vg-spell_server_4529_waterr',
                    'vg-opk_4529_waterr',
                    'vg-ope_4529_waterr',
                    'vg-opelistener_4529_waterr'],
                'site': ['vg-vcmu_4529_waterr',
                    'vg-vbfs1_4529_waterr'],
                'many':['test12345678901234567890']}




resource_list = []



default_attributes = [
    ['State', 'unknown'],
    ['TransState', 'not_waiting'],
    ['Enabled', 'true'],
    ['DesiredState', 'offline'],
    ['FaultCount', 0],
    ['Probed', 'false'],
    ['OnlineRetryLimit', 3],
    ['MonitorOnly', 'false'],
    ['MonitorInterval', 60],
    ['OfflineMonitorInterval', 120],
    ['LastPoll', 0],
    ['ActiveAction', 'false'],
    ['OnlineTimeout', 60],
    ['AutoRestart', 'true'],
    ['Group', 'none']]


class Application:

    def __init__(self, master):
        self.master = master
        self.master.title('icsgui')
        self.build_menu_bar()
        self.build_gui()

        self.connect_server()
        self.update_resource_tree()
        self.build_resource_view()




        self.resources = {}


    def connect_server(self):
        try:
            conn = network.connect('', 4040)
        except network.ConnectionError:
            pass
        self.rpc_proxy = RPCProxy(conn)

    def build_gui(self):

        self.paned_window = PanedWindow(self.master, orient=HORIZONTAL)
        self.paned_window.pack(fill=BOTH, expand=True)

        # Create resource navigation pane
        self.res_navigation = Frame(self.paned_window)
        self.paned_window.add(self.res_navigation, weight=0)
        #self.resNavigation.pack(side=LEFT, fill=BOTH, anchor='w', expand=True)
        self.res_navigation.pack(side=LEFT, fill=BOTH, expand=True)
        self.res_navigation.config(relief=SUNKEN, padding=(5, 5))
        self.res_navigation.rowconfigure(0, weight=1)
        self.res_navigation.columnconfigure(0, weight=1)

        # Create resource tree in navigation window
        self.res_navigation_tree = Treeview(self.res_navigation)
        #self.resNavigationTree.pack(anchor='nw', fill=BOTH, expand=True)
        self.res_navigation_tree.grid(row=0, column=0, sticky='nsew')
        self.res_navigation_tree.config(show='tree')
        self.res_navigation_tree.bind('<<TreeviewSelect>>', self.update_res_viewer)

        # Add scroll bar to navigation tree
        self.res_navtree_scrollbarY = Scrollbar(self.res_navigation, orient=VERTICAL, command=self.res_navigation_tree.yview)
        self.res_navtree_scrollbarY.grid(row=0, column=1, sticky='ns')
        self.res_navigation_tree.config(yscrollcommand=self.res_navtree_scrollbarY.set)

        self.res_navtree_scrollbarX = Scrollbar(self.res_navigation, orient=HORIZONTAL, command=self.res_navigation_tree.xview)
        self.res_navtree_scrollbarX.grid(row=1, column=0, sticky='ew')
        self.res_navigation_tree.config(xscrollcommand=self.res_navtree_scrollbarX.set)

        # Create resource viewer navigation pane
        self.res_viewer = Frame(self.paned_window)
        self.paned_window.add(self.res_viewer, weight=4)
        self.res_viewer.pack(expand=True, fill=BOTH, side=LEFT, anchor='e')
        self.res_viewer.config(relief=SUNKEN, padding=(5, 5))

        # Create tabbed view
        self.res_viewer_tabs = Notebook(self.res_viewer)
        self.res_viewer_tabs.pack(expand=True, fill=BOTH)

        # Create tabs in resource viewer window
        self.status_view_tab = Frame(self.res_viewer_tabs)
        self.res_viewer_tabs.add(self.status_view_tab, text='Status')

        self.resources_view_tab = Frame(self.res_viewer_tabs)
        self.res_viewer_tabs.add(self.resources_view_tab, text='Resources')

        self.properties_view_tab = Frame(self.res_viewer_tabs)
        self.res_viewer_tabs.add(self.properties_view_tab, text='Properties')



        # Create resource dependancy view
        self.res_link_view = Canvas(self.resources_view_tab)
        self.res_link_view.pack(expand=True, fill=BOTH)
        self.res_link_view.config(bg='green')
        self.line = self.res_link_view.create_line(0, 0, 100, 100)

        self.resource_icon = Label(self.res_link_view)
        self.resource_icon.pack()
        self.resource_icon.config(text='A')


        attributes = self.rpc_proxy.attr('proc-a1')
        self.create_table(self.properties_view_tab, attributes)#, header=['Attribute', 'Value'])


    def build_menu_bar(self):
        self.menu_bar = Menu(self.master)
        self.menu_bar.config(relief=FLAT)

        self.file_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label='File', menu=self.file_menu)
        self.file_menu.add_command(label='Connect', command=self.connect_server)
        self.file_menu.add_command(label='Exit', command=sys.exit)

        self.editMenu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label='Edit', menu=self.editMenu)
        self.editMenu.add_command(label='New Group')
        self.editMenu.add_command(label='New Resource')

        self.view_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label='View', menu=self.view_menu)

        self.help_menu = Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label='Help', menu=self.help_menu)
        self.help_menu.add_command(label='About')

        self.master.config(menu=self.menu_bar)

    def create_table(self, root, data, header=None):

        max_col_width = {}
        col_count = 0

        for row in data:
            col_count = len(row)

        # Initialize maximum column length
        if header is not None:
            for colNum in range(col_count):
                max_col_width[colNum] = len(header[colNum])
        else:
            for colNum in range(col_count):
                max_col_width[colNum] = 0

        # Determine column width
        for row in data:
            for colNum in range(col_count):
                if max_col_width[colNum] < len(str(row[colNum])):
                    max_col_width[colNum] = len(row[colNum])

        row_count = 0
        for row in data:
            col_count = 0
            for item in row:
                x = Label(root, text='{}'.format(item, row_count, col_count))
                x.grid(row=row_count, column=col_count)
                x.config(justify=LEFT, width=max_col_width[col_count], background='white')
                col_count += 1
            row_count += 1

    def update_data(self, event):
        selected_item = self.res_navigation_tree.selection()
        print(selected_item)
        self.update_prop_viewer()
        self.update_res_viewer()




    def update_prop_viewer(self, resource):
        self.create_table(self.properties_view_tab, [])



        print(selectedItem)


    def update_res_viewer(self, event):
        pass



    def update_resource_tree(self):

        resource_dict = {}
        groups = self.rpc_proxy.list_groups()
        for group in groups:
            resource_dict[group] = []
            resources = self.rpc_proxy.grp_resources(group)
            for resource in resources:
                resource_dict[group].append(resource)

        for group in resource_dict:
            self.res_navigation_tree.insert('', 'end', group, text=group)
            for resource in resource_dict[group]:
                self.res_navigation_tree.insert(group, 'end', resource, text=resource)

    def build_resource_view(self):
        self.resources_view_canvas = Canvas(self.status_view_tab)
        self.resources_view_canvas.pack()
        self.resources_view_canvas.config(width=600, height=600)

        self.test_line = self.resources_view_canvas.create_line(100, 100, 100, 100, fill='blue', width=5)
        self.resources_view_canvas.itemconfigure(self.test_line, fill='green')







        self.new_grp_button = Button()
        self.new_res_button = Button()
        self.online_res_button = Button()






    def update_resources(self):

        resource_dict = {}
        groups = self.rpc_proxy.list_groups()
        for group in groups:
            resource_dict[group] = []
            resources = self.rpc_proxy.grp_resources(group)
            for resource in resources:
                resource_dict[group].append(resource)






    def load_existing_config(self):
        pass

    def command(self):
        print('command')

if __name__ == '__main__':
    root = Tk()
    Application(root)
    root.mainloop()





