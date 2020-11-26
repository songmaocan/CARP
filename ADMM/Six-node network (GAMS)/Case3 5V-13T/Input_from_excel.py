#Functions: Generate GAMS file
#Author: Maocan Song
#Date:2020/7/17
import xlrd
class Excel_processor:
    def __init__(self,based_profit):
        self.based_profit=based_profit
        self.network_workbooks = xlrd.open_workbook("input_physical_network.xlsx")
        self.physical_depot_id = 5  # 从1开始
        print("读取数据中....")

    def read_nodes(self):
        input_physical_node_workbook = self.network_workbooks.sheet_by_index(0)
        self.node_list=[]
        self.g_number_of_nodes=0
        self.g_number_of_physical_nodes=0
        # 读取物理路网结点
        for row in range(1, input_physical_node_workbook.nrows):
            node=Node()
            node.node_id=self.g_number_of_nodes
            node.node_type=1
            self.node_list.append(node)
            self.g_number_of_nodes+=1
            self.g_number_of_physical_nodes+=1

    def read_links(self):
        self.read_nodes()
        input_physical_link_workbook=self.network_workbooks.sheet_by_index(1)
        self.link_list=[]
        self.g_number_of_links=0
        self.g_number_of_physical_links=0
        self.g_number_of_dummy_links=0
        self.task_list=[] #我们在里面装了task在link list里面的ID
        self.g_number_of_tasks=0
        for row in range(1, input_physical_link_workbook.nrows):
            if int(input_physical_link_workbook.cell_value(row, 4)==0):
                link=Link()
                link.link_id=self.g_number_of_physical_links
                link.link_type=1
                link.from_node_id = int(input_physical_link_workbook.cell_value(row, 1))-1
                link.to_node_id = int(input_physical_link_workbook.cell_value(row, 2))-1
                link.travel_time = int(input_physical_link_workbook.cell_value(row, 3))
                link.demand=0
                self.link_list.append(link)
                self.g_number_of_links+=1
                self.g_number_of_physical_links+=1
                # 临界结点/邻接路段
                self.node_list[link.from_node_id].outbound_nodes_list.append(link.to_node_id)
                self.node_list[link.from_node_id].outbound_links_list.append(link)
                self.node_list[link.from_node_id].outbound_size = len(self.node_list[link.from_node_id].outbound_nodes_list)
            else:

                #step1:添加任务路段（加乘子）
                self.g_number_of_tasks+=1
                link = Link()
                link.link_id = self.g_number_of_links
                link.link_type = 1
                link.from_node_id = int(input_physical_link_workbook.cell_value(row, 1)) - 1
                link.to_node_id = int(input_physical_link_workbook.cell_value(row, 2)) - 1
                link.travel_time = int(input_physical_link_workbook.cell_value(row, 3))
                link.demand=int(input_physical_link_workbook.cell_value(row, 4))
                link.base_profit_for_lagrangian=self.based_profit
                link.base_profit_for_searching=self.based_profit
                self.link_list.append(link)
                self.task_list.append(link.link_id)
                self.g_number_of_links += 1
                self.g_number_of_physical_links += 1
                # 临界结点/邻接路段
                self.node_list[link.from_node_id].outbound_nodes_list.append(link.to_node_id)
                self.node_list[link.from_node_id].outbound_links_list.append(link)
                self.node_list[link.from_node_id].outbound_size = len(self.node_list[link.from_node_id].outbound_nodes_list)
                #step2:虚拟结点
                node=Node()
                node.node_id=self.g_number_of_nodes
                node.node_type=0
                self.node_list.append(node)
                #step3:虚拟路段1（起点=Task_origin,终点是虚拟结点）
                link=Link()
                link.link_id=self.g_number_of_links
                link.link_type=0
                link.travel_time=1
                link.demand=0
                link.from_node_id=int(input_physical_link_workbook.cell_value(row, 1))-1
                link.to_node_id=self.g_number_of_nodes
                self.g_number_of_links+=1
                self.link_list.append(link)
                # 临界结点/邻接路段
                self.node_list[link.from_node_id].outbound_nodes_list.append(link.to_node_id)
                self.node_list[link.from_node_id].outbound_links_list.append(link)
                self.node_list[link.from_node_id].outbound_size = len(self.node_list[link.from_node_id].outbound_nodes_list)
                #step4: 虚拟结点-Task——destination
                link = Link()
                link.link_id = self.g_number_of_links
                link.link_type = 0
                link.travel_time = int(input_physical_link_workbook.cell_value(row, 3))-1
                link.demand = 0
                link.from_node_id = self.g_number_of_nodes
                link.to_node_id =int(input_physical_link_workbook.cell_value(row, 2)) - 1
                self.g_number_of_links += 1
                self.link_list.append(link)
                # 临界结点/邻接路段
                self.node_list[link.from_node_id].outbound_nodes_list.append(link.to_node_id)
                self.node_list[link.from_node_id].outbound_links_list.append(link)
                self.node_list[link.from_node_id].outbound_size = len(self.node_list[link.from_node_id].outbound_nodes_list)

                self.g_number_of_nodes+=1

        #添加虚拟场站和路段
        self.virtual_depot_id_depart=self.g_number_of_nodes
        node=Node()
        node.node_id=self.g_number_of_nodes
        node.node_type=100
        self.node_list.append(node)

        #虚拟路段-1(虚拟场站→实际场站)
        link = Link()
        link.link_id = self.g_number_of_links
        link.link_type = 0
        link.travel_time =1
        link.demand = 0
        link.from_node_id = self.g_number_of_nodes
        link.to_node_id =self.physical_depot_id-1
        self.g_number_of_links+=1
        self.link_list.append(link)
        # 临界结点/邻接路段
        self.node_list[link.from_node_id].outbound_nodes_list.append(link.to_node_id)
        self.node_list[link.from_node_id].outbound_links_list.append(link)
        self.node_list[link.from_node_id].outbound_size = len(self.node_list[link.from_node_id].outbound_nodes_list)

        self.g_number_of_nodes += 1


        self.virtual_depot_id_back = self.g_number_of_nodes
        node = Node()
        node.node_id = self.g_number_of_nodes
        node.node_type = 100
        self.node_list.append(node)

        # 虚拟路段-2(实际场站→虚拟场站)
        link = Link()
        link.link_id = self.g_number_of_links
        link.link_type = 0
        link.travel_time = 1
        link.demand = 0
        link.from_node_id = self.physical_depot_id - 1
        link.to_node_id = self.g_number_of_nodes
        self.g_number_of_links += 1
        self.link_list.append(link)
        # 临界结点/邻接路段
        self.node_list[link.from_node_id].outbound_nodes_list.append(link.to_node_id)
        self.node_list[link.from_node_id].outbound_links_list.append(link)
        self.node_list[link.from_node_id].outbound_size = len(self.node_list[link.from_node_id].outbound_nodes_list)

        self.g_number_of_nodes+=1

    def generate_GAMS_file(self):
        number_of_vehicles = 5
        time_horizon = 30
        capacity = 50
        with open("GAMS_input.txt","w") as fl:
            #index
            fl.write("set t time id /0*{}/;\n".format(time_horizon))
            fl.write("set i node id /0*{}/;\n".format(self.g_number_of_nodes))
            fl.write("alias(i,j);\n")
            fl.write("alias(t,s);\n")
            #parameters-capcaity
            fl.write("parameter capacity vehicle capacity /{}/;\n".format(capacity))
            # parameters-arc cost
            fl.write("parameter arcs(i,j,t,s) arc cost ;\n")
            for link in self.link_list:
                arc_cost=link.travel_time
                from_node = "'" + str(link.from_node_id) + "',"
                to_node = "'" + str(link.to_node_id) + "',"
                if arc_cost!=0:
                    fl.write("arcs(" + from_node + to_node + "t,t+{})={};\n".format(arc_cost,arc_cost))
                else:
                    fl.write("arcs(" + from_node + to_node + "t,t+{})={};\n".format(arc_cost, 0.001))
            for node in range(self.g_number_of_nodes):
                node="'" + str(node) + "',"
                fl.write("arcs(" + node + node + "t,t+{})={};\n".format(1, 0.001))
            #task_arcs
            fl.write("parameter task_arcs(i,j) task arcs and demand;\n")
            for task_id in range(self.g_number_of_tasks):
                task_id_in_link=self.task_list[task_id]
                task_link=self.link_list[task_id_in_link]
                from_node="'"+str(task_link.from_node_id)+"',"
                to_node="'"+str(task_link.to_node_id)+"')="
                demand=task_link.demand
                fl.write("task_arcs(" + from_node + to_node + "{};\n".format(demand))
            #flow balance
            fl.write("set v vehicle id /1*{}/;\n".format(number_of_vehicles))
            fl.write("parameter origin_node(v,i,t)  origin nodes and departure time; \n")
            fl.write("origin_node(v,'{}','{}') = 1;\n".format(self.virtual_depot_id_depart,0))

            fl.write("parameter destination_node(v,i,t);\n")
            fl.write("destination_node(v,'{}','{}') = 1;\n".format(self.virtual_depot_id_back,time_horizon))

            fl.write("parameter intermediate_node(v,i,t);\n")
            fl.write("intermediate_node(v,i,t) = (1- origin_node(v,i,t))*(1- destination_node(v,i,t));\n")
            print("OK!")


class Node:
    def __init__(self):
        self.node_id=None
        self.node_type=None             #物理结点-1，虚拟结点0，场站结点-100
        self.outbound_nodes_list=[]
        self.outbound_size=0
        self.outbound_links_list=[]

class Link:
    def __init__(self):
        self.link_id=None
        self.link_type=None     #物理路段-1、虚拟路段-0
        self.from_node_id=None
        self.to_node_id=None
        self.travel_time=None
        self.demand=None
        self.base_profit_for_searching=None     #三项之力
        self.base_profit_for_lagrangian=None    #乘子

mod=Excel_processor(0)
mod.read_links()
mod.generate_GAMS_file()

