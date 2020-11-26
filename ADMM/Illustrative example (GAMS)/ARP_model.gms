*solving the arc routing problem(the illustrative exzample in the ADMM_arp paper)

*index
set v vehicle id /1,2/;
*set task task id /1*20/;
set i node id /0*5/;
set t time id /1*10/;
set depot(i) depot /1/;
alias(i,j);
alias(t,s);

*parameter
parameter capacity vehicle capcity /4/;
*parameter demand(task) task demand;
parameter arcs(i,j,t,s) arc cost;
arcs("4","5",t,t+1)=1;
arcs('0',"1",t,t+1)=1;
arcs("0","3",t,t+1)=1;
arcs("1","2",t,t+2)=2;
arcs("3","4",t,t+3)=3;
arcs("2","5",t,t+1)=1;

arcs(i,i,t,t+1)=0.01;

parameter task_arcs(i,j) task arcs and demand;
task_arcs("1","2")=2;
task_arcs("3","4")=3;

*flow balance
parameter origin_node(v,i,t)  origin nodes and departure time;
origin_node(v,"0",'1') = 1;

parameter destination_node(v,i,t);
destination_node(v,'5','10') = 1;

parameter intermediate_node(v,i,t);
intermediate_node(v,i,t) = (1- origin_node(v,i,t))*(1- destination_node(v,i,t));

*model
binary variables x(v,i,j,t,s);
variable z;

equations
obj    the objective function
task_satifaction(i,j) the task satifaction constraints
flow_on_node_origin(v,i,t)         origin node flow on node i at time t
capacity_constraints(v)         vehicle capacity
flow_on_node_intermediate(v,i,t)   intermediate node flow on node i at time t
flow_on_node_destination(v,i,t)      destination node flow on node i at time t
;
obj.. z =e= sum(v,sum((i,j,t,s)$arcs(i,j,t,s),arcs(i,j,t,s)*x(v,i,j,t,s)));
task_satifaction(i,j)$task_arcs(i,j).. sum(v,sum((t,s),x(v,i,j,t,s))) =e= 1;
capacity_constraints(v).. sum((i,j,t,s)$arcs(i,j,t,s),task_arcs(i,j)*x(v,i,j,t,s)) =l= capacity;
flow_on_node_origin(v,i,t)$(origin_node(v,i,t)).. sum((j,s)$(arcs(i,j,t,s)), x(v,i,j,t,s)) =e= 1;
flow_on_node_destination(v,i,t)$(destination_node(v,i,t))..  sum((j,s)$(arcs(j,i,s,t)), x(v,j,i,s,t))=e= 1;
flow_on_node_intermediate(v,i,t)$(intermediate_node(v,i,t)).. sum((j,s)$(arcs(i,j,t,s)), x(v,i,j,t,s))-sum((j,s)$(arcs(j,i,s,t)), x(v,j,i,s,t)) =e= 0;

Model ARP /ALL/;
Solve ARP using MIP minimizing z;

