from Input_from_excel import Excel_processor
import copy
class ADMM:
    def __init__(self):
        #数据输入
        self.base_profit=-5   #multipliers
        data=Excel_processor(self.base_profit)
        self.node_list, self.g_number_of_nodes, self.link_list, self.g_number_of_links, self.task_list, \
        self.g_number_of_tasks,self.virtual_depot_id=data.read_links()
        # 输入车辆属性*5
        self.g_number_of_vehicles=6
        self.vehicle_capacity=100
        self.vehicle_departure_time_beginning=0
        self.vehicle_arrival_time_ending=200
        self.big_M=100
        #ADMM
        self.ADMM_iteration_times=100
        self.rpo=0.5 #惩罚参数

        # DP参数
        self.g_ending_state_vector = [None]*(self.g_number_of_vehicles+1)
        # self.g_ending_state_vector_for_lr = [None] * self.g_number_of_vehicles
        self.g_time_dependent_state_vector = []
        for v in range(self.g_number_of_vehicles+1):
            self.g_time_dependent_state_vector.append([])
            intervals = self.vehicle_arrival_time_ending-self.vehicle_departure_time_beginning
            for t in range(intervals+1):
                self.g_time_dependent_state_vector[v].append([None]*self.g_number_of_nodes)
        # beam searching：每个结点保留最多两个状态，成本最小
        self.Best_K_Size=2

        # SST路径
        self.path_space_seq = []
        self.path_time_seq  =[]
        self.path_state_seq = []

        # 统计误差、记录乘子
        self.served_time = []
        self.repeat_served = []
        self.un_served=[]
        self.record_profit = []
        self.max_label_cost = float("inf")

        # 上下界-ADMM
        self.ADMM_local_LB = [0] * self.ADMM_iteration_times
        self.ADMM_local_UB = [0] * self.ADMM_iteration_times
        self.ADMM_global_LB = [-self.max_label_cost] * self.ADMM_iteration_times
        self.ADMM_global_UB = [self.max_label_cost] * self.ADMM_iteration_times
        print("初始化完成！")

        #part 1 Column pool information
        self.column_pool_path_seq=[[] for i in range(self.g_number_of_vehicles)]
        self.column_pool_path_cost=[[] for i in range(self.g_number_of_vehicles)]
        self.column_pool_path_serving=[[] for i in range(self.g_number_of_vehicles)]
        # self.record_profit = []


    def g_Alternating_Direction_Method_of_Multipliers(self):
        for i in range(self.ADMM_iteration_times):
            # 增加存储空间
            self.path_space_seq.append([])
            self.path_time_seq.append([])
            self.path_state_seq.append([])
            #服务次数
            self.served_time.append([0]*self.g_number_of_tasks)
            self.repeat_served.append([])   #误差，从0到number_of_tasks-1
            self.un_served.append([])
            self.record_profit.append([])   #记录乘子
            print("开始ADMM算法的第{}次迭代".format(i+1))
#step1:找上界
            if i!=0:
                self.served_time[i]=self.served_time[i-1]   #复制上次迭代的访问次数信息
            for v in range(self.g_number_of_vehicles):
                #更新成本
                if self.g_ending_state_vector[v]!=None:
                    for task_id in range(self.g_number_of_tasks):
                        self.served_time[i][task_id]-=self.g_ending_state_vector[v].VSStateVector[0].task_service_state[task_id]
                #更新三项
                for task_id in range(self.g_number_of_tasks):
                    #从0到任务数-1 映射到 原始的task_id，也就是路段ID
                    task_id_in_link_list=self.task_list[task_id]
                    #得到了任务路段的信息
                    self.link_list[task_id_in_link_list].base_profit_for_searching=self.link_list[task_id_in_link_list].base_profit_for_lagrangian+self.rpo*self.served_time[i][task_id]-self.rpo/2
                #Flag=1,ADMM成本；Flag=2,LR成本
                self.g_optimal_time_dependent_dynamic_programming(v,1)
                print(self.g_ending_state_vector[v].VSStateVector[0].task_service_state)
                # 更新ADMM的上界(将车辆v的可行解带入目标函数)
                self.ADMM_local_UB[i]+=self.g_ending_state_vector[v].VSStateVector[0].Primal_Label_cost
                # 记录SST路径
                self.path_space_seq[i].append(self.g_ending_state_vector[v].VSStateVector[0].m_visit_space_seq)
                self.path_time_seq[i].append(self.g_ending_state_vector[v].VSStateVector[0].m_visit_time_seq)
                self.path_state_seq[i].append(self.g_ending_state_vector[v].VSStateVector[0].m_visit_state_seq)

                # part 2 Column pool information record
                #------------------------------------------------------
                SST_path=[]
                SST_path.append(self.g_ending_state_vector[v].VSStateVector[0].m_visit_state_seq)
                SST_path.append(self.g_ending_state_vector[v].VSStateVector[0].m_visit_space_seq)
                SST_path.append(self.g_ending_state_vector[v].VSStateVector[0].m_visit_time_seq)
                self.column_pool_path_seq[v].append(SST_path)

                primal_cost_of_SST_path=self.g_ending_state_vector[v].VSStateVector[0].Primal_Label_cost
                self.column_pool_path_cost[v].append(primal_cost_of_SST_path)

                #serving state or served tasks
                serving_state=self.g_ending_state_vector[v].VSStateVector[0].task_service_state #all tasks
                self.column_pool_path_serving[v].append(serving_state)
                #------------------------------------------------------

               #还原车辆v的访问次数
                for task_id in range(self.g_number_of_tasks):
                    self.served_time[i][task_id]+=self.g_ending_state_vector[v].VSStateVector[0].task_service_state[task_id]
            #Check:Task有没有被重复访问或未访问呢？
            for task_id in range(self.g_number_of_tasks):
                # 从0到任务数-1 映射到 原始的task_id，也就是路段ID
                task_id_in_link_list = self.task_list[task_id]
                if self.served_time[i][task_id]>1:#repeat
                    self.repeat_served[i].append(task_id_in_link_list+1) #放实际路段ID，从1开始
                if self.served_time[i][task_id]==0:#un_served
                    self.un_served[i].append(task_id_in_link_list+1) #放实际路段ID，从1开始
                    self.ADMM_local_UB[i]+=self.big_M #虚拟车的成本
                self.record_profit[i].append(self.link_list[task_id_in_link_list].base_profit_for_lagrangian)

# step2:找下界
            print("LB")
            self.g_optimal_time_dependent_dynamic_programming(self.g_number_of_vehicles, 2)
            self.ADMM_local_LB[i]+=self.g_number_of_vehicles*self.g_ending_state_vector[self.g_number_of_vehicles].VSStateVector[0].Label_cost_for_lagrangian
            # for v in range(self.g_number_of_vehicles):
            #     self.g_optimal_time_dependent_dynamic_programming(v,2)
            #     self.ADMM_local_LB[i]+=self.g_ending_state_vector_for_lr[v].VSStateVector.Label_cost_for_lagrangian
            print(self.g_ending_state_vector[self.g_number_of_vehicles].VSStateVector[0].task_service_state)

            #加上乘子
            for task_id in range(self.g_number_of_tasks):
                # 从0到任务数-1 映射到 原始的task_id，也就是路段ID
                task_id_in_link_list=self.task_list[task_id]
                self.ADMM_local_LB[i]-=self.link_list[task_id_in_link_list].base_profit_for_lagrangian


# step3:更新乘子和惩罚参数
            for task_id in range(self.g_number_of_tasks):
                # 从0到任务数-1 映射到 原始的task_id，也就是路段ID
                task_id_in_link_list = self.task_list[task_id]
                self.link_list[task_id_in_link_list].base_profit_for_lagrangian+=self.rpo*(self.served_time[i][task_id]-1)
            if i>=10:
                if (len(self.un_served[i])+len(self.repeat_served[i]))**2>0.25*(len(self.un_served[i-1]) + len(self.repeat_served[i-1])) ** 2:
                    self.rpo+=0.5
                if (len(self.un_served[i])+len(self.repeat_served[i]))**2==0:
                    self.rpo=0.5
#step4: 检测终止条件
            # if i==0:
            #     self.ADMM_global_UB[i]=self.ADMM_local_UB[i]
            #     self.ADMM_global_LB[i]=self.ADMM_local_LB[i]
            # else:
            #     self.ADMM_global_UB[i] = self.ADMM_local_UB[i]
            #     self.ADMM_global_LB[i] = self.ADMM_local_LB[i]

    def g_optimal_time_dependent_dynamic_programming(self,vehicle_id,Flag):
        #self.departure_time_beginning=0
        #self.arriving_time_ending=30
        self.origin_node=self.virtual_depot_id
        self.destination_node=self.virtual_depot_id
        for t in range(self.vehicle_departure_time_beginning, self.vehicle_arrival_time_ending+1):
            for n in range(self.g_number_of_nodes):
                #给每个时空点一个属性，并且有个更新成本的函数。
                self.g_time_dependent_state_vector[vehicle_id][t][n] = C_time_indexed_state_vector()
                self.g_time_dependent_state_vector[vehicle_id][t][n].Reset()
                self.g_time_dependent_state_vector[vehicle_id][t][n].current_time=t
                self.g_time_dependent_state_vector[vehicle_id][t][n].current_node=n

        self.g_ending_state_vector[vehicle_id]=C_time_indexed_state_vector()

        #初始化起点状态
        element = CVSState(self.g_number_of_tasks)
        element.current_node_id = self.origin_node
        element.m_visit_space_seq.append(self.origin_node)
        element.m_visit_time_seq.append(self.vehicle_departure_time_beginning)
        element.m_visit_state_seq.append(self.vehicle_capacity)
        self.g_time_dependent_state_vector[vehicle_id][self.vehicle_departure_time_beginning][self.origin_node].update_state(element,Flag)
        # DP
        for t in range(self.vehicle_departure_time_beginning, self.vehicle_arrival_time_ending):
            for n in range(self.g_number_of_nodes):
                self.g_time_dependent_state_vector[vehicle_id][t][n].Sort(Flag)
                for index in range(min(len(self.g_time_dependent_state_vector[vehicle_id][t][n].VSStateVector),self.Best_K_Size)):
                    pElement=self.g_time_dependent_state_vector[vehicle_id][t][n].VSStateVector[index]
                    from_node_id = pElement.current_node_id  #起点ID
                    from_node = self.node_list[from_node_id] #起点
                    for i in range(from_node.outbound_size): #邻接点
                        to_node_id = from_node.outbound_nodes_list[i] #从当前点可以到达哪些点ID
                        to_node = self.node_list[to_node_id] #邻接点
                        link_to = from_node.outbound_links_list[i] #邻接路段
                        next_time=t+link_to.travel_time
                        if next_time>self.vehicle_arrival_time_ending:
                            continue
                        if to_node_id==self.destination_node:
                            new_element = CVSState(self.g_number_of_tasks)
                            new_element.my_copy(pElement)
                            new_element.current_node_id = to_node_id  #当前点
                            # 运输弧
                            new_element.m_visit_space_seq.append(self.destination_node)
                            new_element.m_visit_time_seq.append(next_time)
                            new_element.m_visit_state_seq.append(copy.copy(pElement.m_visit_state_seq[-1]))
                            # 虚拟弧
                            new_element.m_visit_space_seq.append(self.destination_node)
                            new_element.m_visit_time_seq.append(self.vehicle_arrival_time_ending)
                            new_element.m_visit_state_seq.append(copy.copy(pElement.m_visit_state_seq[-1]))
                            # 计算成本
                            new_element.Calculate_Label_Cost(link_to)
                            self.g_ending_state_vector[vehicle_id].update_state(new_element,Flag)
                            continue
                        #判断是不是任务路段
                        if link_to.demand==0:#非任务路段
                            new_element = CVSState(self.g_number_of_tasks)
                            new_element.my_copy(pElement)
                            new_element.current_node_id = to_node_id  # 当前点
                            # 运输弧
                            new_element.m_visit_space_seq.append(to_node_id)
                            new_element.m_visit_time_seq.append(next_time)
                            new_element.m_visit_state_seq.append(copy.copy(pElement.m_visit_state_seq[-1]))
                            # 计算成本
                            new_element.Calculate_Label_Cost(link_to)
                            self.g_time_dependent_state_vector[vehicle_id][next_time][to_node_id].update_state(new_element,Flag)
                            continue
                        #判断水量是否充足
                        if pElement.m_visit_state_seq[-1] < link_to.demand:
                            continue
                        #判断车辆受否可以访问这个任务路段
                        #Task_id是多少呢？
                        link_id=self.link_list.index(link_to) #从0开始
                        task_id_from_0=self.task_list.index(link_id)
                        if pElement.task_service_state[task_id_from_0]==1:
                            continue
                        new_element = CVSState(self.g_number_of_tasks)
                        new_element.my_copy(pElement)
                        new_element.current_node_id = to_node_id  # 当前点
                        # 运输弧
                        new_element.m_visit_space_seq.append(to_node_id)
                        new_element.m_visit_time_seq.append(next_time)
                        new_element.m_visit_state_seq.append(copy.copy(pElement.m_visit_state_seq[-1])-link_to.demand)
                        #修改任务访问标识，0变成1
                        new_element.task_service_state[task_id_from_0]=1
                        # 计算成本
                        new_element.Calculate_Label_Cost(link_to)
                        self.g_time_dependent_state_vector[vehicle_id][next_time][to_node_id].update_state(new_element,Flag)
        self.g_ending_state_vector[vehicle_id].Sort(Flag)


    def output_to_file(self, spend_time):
        # SST路径
        with open("SST_path.csv", "w") as f:
            f.write("iteration,vehicle_id,path_space_seq,path_time_seq,path_state_seq\n")
            for i in range(self.ADMM_iteration_times):
                for v in range(self.g_number_of_vehicles):
                    f.write(str(i + 1) + ",")
                    f.write(str(v + 1) + ",")
                    str1 = ""
                    str2 = ""
                    str3 = ""
                    for s in range(len(self.path_space_seq[i][v])):
                        str1 += str(self.path_space_seq[i][v][s]+1) + "_"
                        str2 += str(self.path_time_seq[i][v][s]) + "_"
                        str3 += str(self.path_state_seq[i][v][s]) + "_"
                    f.write(str1 + "," + str2 + "," + str3 + "\n")
            print("已经将SST路径输出至output_SST_path.csv")
        # 乘子
        with open("Multipliers.csv", "w") as f:
            f.write("Iteration" + ",")
            for task_id in range(self.g_number_of_tasks):
                # 从0到任务数-1 映射到 原始的task_id，也就是路段ID
                task_id_in_link_list = self.task_list[task_id]
                f.write("TASK-{}".format(task_id_in_link_list) + ",")
            f.write("\n")
            for i in range(self.ADMM_iteration_times):
                f.write("iteration-{},".format(i+1))
                for n in range(self.g_number_of_tasks):
                    f.write(str(self.record_profit[i][n]) + ",")
                f.write("\n")
            print("已将ADMM的乘子输出到output_profit.csv")

        # ADMM误差
        with open("ADMM_gap.csv", "w") as f:
            f.write("iteration,local_LB,local_UB,repeat_served,miss_served\n")
            for i in range(self.ADMM_iteration_times):
                f.write(str(i + 1) + ",")
                f.write(str(self.ADMM_local_LB[i]) + ",")
                f.write(str(self.ADMM_local_UB[i]) + ",")
                for j in self.repeat_served[i]:
                    f.write(str(j) + ";")
                f.write(",")
                for k in self.un_served[i]:
                    f.write(str(k) + ";")
                f.write("\n")
            # # 我们还想要获得全局上下界，但是局部上界中有不可行的解，所以要剔除这些
            # global_LB = max(self.ADMM_local_LB)
            # index_LB = self.ADMM_local_LB.index(global_LB)
            # f.write("获得的全局最优下界为{}，发生在第{}次迭代下\n".format(global_LB, index_LB + 1))
            # global_UB = self.max_label_cost
            # index_UB = -1
            # for iteration in range(self.max_iteration_time):
            #     if self.repeat_served[iteration] == [] and self.un_served[iteration] == []:
            #         if self.ADMM_local_UB[iteration] < global_UB:
            #             global_UB = self.ADMM_local_UB[iteration]
            #             index_UB = iteration
            # if index_UB != -1:
            #     f.write("获得的全局最优上界为{}，发生在第{}次迭代下\n".format(global_UB, index_UB + 1))
            #     gap = (global_UB - global_LB) / global_UB
            #     f.write(str('%.2f%%' % (gap * 100)))
            # f.write("\n")
            f.write("计算总用时{}秒".format(spend_time))
            print("已将ADMM上下界及客户访问偏差输出到output_ADMM_gap.csv")

        #---------------------------------------------------
        print("Output column pools!")
        with open("Column_pools.csv","w") as f:
            #title
            f.write("vehicle_id,path_index,state_seq,space_seq,time_seq,cost,serving_state\n")
            for v in range(self.g_number_of_vehicles):
                for path_index in range(len(self.column_pool_path_seq[v])):
                    SST_path=self.column_pool_path_seq[v][path_index]
                    f.write(str(v)+",")
                    f.write(str(path_index)+",")
                    #write the SST path
                    str1 = ""
                    str2 = ""
                    str3 = ""
                    for s in range(len(SST_path[0])):
                        str1 += str(SST_path[0][s]) + "_"
                        str2 += str(SST_path[1][s]) + "_"
                        str3 += str(SST_path[2][s]) + "_"
                    f.write(str1 + "," + str2 + "," + str3 + ",")

                    path_cost=self.column_pool_path_cost[v][path_index]
                    f.write(str(path_cost)+",")

                    serving_state=self.column_pool_path_serving[v][path_index]
                    str4 = ""
                    for task in range(self.g_number_of_tasks):
                        str4+=str(serving_state[task])+"_"
                    f.write(str4+"\n")
        print("Column pool is output!")
        #output GAMS file
        with open("GAMS_no_symetry.txt","w") as fl:
            fl.write("set v vehicle index /\n")
            for v in range(self.g_number_of_vehicles):
                fl.write(str(v)+"\n")
            fl.write("/;\n")

            fl.write("set k path index /0*100000/;\n")

            fl.write("set p task index /\n")
            for p in range(self.g_number_of_tasks):
                fl.write(str(p)+"\n")
            fl.write("/;\n")

            fl.write("parameter path_cost(v,k) the cost of vehicle v choosing the path k /\n")
            for v in range(self.g_number_of_vehicles):
                for k in range(len(self.column_pool_path_seq[v])):
                    cost=self.column_pool_path_cost[v][k]
                    fl.write(str(v)+". "+str(k)+" "+ str(cost)+"\n")
            fl.write("/;\n")

            fl.write("parameter connection_matrix(v,k,p) task p is served vk? /\n")
            for v in range(self.g_number_of_vehicles):
                for k in range(len(self.column_pool_path_seq[v])):
                    serving_state = self.column_pool_path_serving[v][k]
                    for p in range(self.g_number_of_tasks):
                        # if serving_state[p]==1:
                        state=serving_state[p]
                        fl.write(str(v)+". "+str(k)+". "+str(p)+" "+str(state)+"\n")
            fl.write("/;\n")
        print("GAMS file_no_symetry is finished!")
        #---------------------------------------------------
        with open("GAMS_symetry.txt", "w") as fl:
            fl.write("set v vehicle index /\n")
            for v in range(self.g_number_of_vehicles):
                fl.write(str(v) + "\n")
            fl.write("/;\n")

            fl.write("set k path index /0*100000/;\n")

            fl.write("set p task index /\n")
            for p in range(self.g_number_of_tasks):
                fl.write(str(p) + "\n")
            fl.write("/;\n")

            fl.write("parameter path_cost(v,k) the cost of vehicle v choosing the path k /\n")
            for v in range(self.g_number_of_vehicles):
                path_index = 0
                for v_v in range(self.g_number_of_vehicles):
                    for k in range(len(self.column_pool_path_seq[v_v])):
                        cost = self.column_pool_path_cost[v_v][k]
                        fl.write(str(v) + ". " + str(path_index) + " " + str(cost) + "\n")
                        path_index += 1
            fl.write("/;\n")

            fl.write("parameter connection_matrix(v,k,p) task p is served vk? /\n")
            for v in range(self.g_number_of_vehicles):
                path_index = 0
                for v_v in range(self.g_number_of_vehicles):
                    for k in range(len(self.column_pool_path_seq[v_v])):
                        serving_state = self.column_pool_path_serving[v_v][k]
                        for p in range(self.g_number_of_tasks):
                            # if serving_state[p]==1:
                            state = serving_state[p]
                            fl.write(str(v) + ". " + str(path_index) + ". " + str(p) + " " + str(state) + "\n")
                        path_index += 1
            fl.write("/;\n")
        print("GAMS file_symetry is finished!")
        # ---------------------------------------------------

    def go_DW_column_pool_based_approximation_method(self):
        print("solve the DW_restrictive_main_problem by Cplex.")
        



class C_time_indexed_state_vector:
    def __init__(self):
        self.current_time=0 #时间
        self.current_node=0 #空间
        self.VSStateVector=[] #SST结点的状态
        self.state_map=[]   #水量

    def Reset(self):
        self.current_time =0
        self.current_node =0
        self.VSStateVector=[]
        self.state_map=[]

    def m_find_state_index(self, string_key):  #tring_key为水量
        if string_key in self.state_map:
            return self.state_map.index(string_key)
        else:
            return -1

    def update_state(self, element, Flag):
        string_key = element.generate_string_key()
        state_index = self.m_find_state_index(string_key)
        if state_index==-1:
            self.VSStateVector.append(element)
            self.state_map.append(string_key)
        else:
            # Flag=1,ADMM成本；Flag=2,LR成本
            if Flag==2:
                if element.Label_cost_for_lagrangian<self.VSStateVector[state_index].Label_cost_for_lagrangian:
                    self.VSStateVector[state_index]=element
            if Flag==1:
                if element.Label_cost_for_searching<self.VSStateVector[state_index].Label_cost_for_searching:
                    self.VSStateVector[state_index]=element

    def Sort(self, Flag):
        if Flag == 1:
            self.VSStateVector = sorted(self.VSStateVector, key=lambda x: x.Label_cost_for_searching)
        if Flag == 2:
            self.VSStateVector = sorted(self.VSStateVector, key=lambda x: x.Label_cost_for_lagrangian)


class CVSState:
    def __init__(self, g_number_of_tasks):
        self.current_node_id=0
        self.task_service_state = [0] * g_number_of_tasks
        # 记录SST轨迹
        self.m_visit_space_seq = []
        self.m_visit_time_seq = []
        self.m_visit_state_seq = []
        # 标号成本
        self.Primal_Label_cost=0 #一项
        self.Label_cost_for_lagrangian=0#两项
        self.Label_cost_for_searching=0 #四项

    def generate_string_key(self):
        str = self.m_visit_state_seq[-1]
        return str

    def my_copy(self, pElement):
        self.current_node_id = copy.copy(pElement.current_node_id)
        self.task_service_state = []
        self.task_service_state = copy.copy(pElement.task_service_state)
        self.m_visit_space_seq = []
        self.m_visit_space_seq = copy.copy(pElement.m_visit_space_seq)
        self.m_visit_time_seq = []
        self.m_visit_time_seq = copy.copy(pElement.m_visit_time_seq)
        self.m_visit_state_seq = []
        self.m_visit_state_seq = copy.copy(pElement.m_visit_state_seq)

        self.Primal_Label_cost= copy.copy(pElement.Primal_Label_cost)
        self.Label_cost_for_lagrangian = copy.copy(pElement.Label_cost_for_lagrangian)
        self.Label_cost_for_searching = copy.copy(pElement.Label_cost_for_searching)

    def Calculate_Label_Cost(self, link_information):
        #判断路段是不是TASK路段
        if link_information.demand==0:
            self.Primal_Label_cost +=link_information.travel_time
            self.Label_cost_for_lagrangian+=link_information.travel_time
            self.Label_cost_for_searching+=link_information.travel_time
        else:
            self.Primal_Label_cost += link_information.travel_time
            self.Label_cost_for_lagrangian += link_information.travel_time+link_information.base_profit_for_lagrangian
            self.Label_cost_for_searching += link_information.travel_time+link_information.base_profit_for_searching