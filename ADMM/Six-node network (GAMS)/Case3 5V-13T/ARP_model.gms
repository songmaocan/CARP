*solving the arc routing problem
$include "C:\科研\备份文件夹\科研\博士研究进展汇报\2020-1(ARP)\GAMS\小网络\Case3 5V-13T\GAMS_input.txt"

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
task_satifaction(i,j)$task_arcs(i,j).. sum(v,sum((t,s)$(arcs(i,j,t,s)),x(v,i,j,t,s))) =e= 1;
capacity_constraints(v).. sum((i,j,t,s)$arcs(i,j,t,s),task_arcs(i,j)*x(v,i,j,t,s)) =l= capacity;
flow_on_node_origin(v,i,t)$(origin_node(v,i,t)).. sum((j,s)$(arcs(i,j,t,s)), x(v,i,j,t,s)) =e= 1;
flow_on_node_destination(v,i,t)$(destination_node(v,i,t))..  sum((j,s)$(arcs(j,i,s,t)), x(v,j,i,s,t))=e= 1;
flow_on_node_intermediate(v,i,t)$(intermediate_node(v,i,t)).. sum((j,s)$(arcs(i,j,t,s)), x(v,i,j,t,s))-sum((j,s)$(arcs(j,i,s,t)), x(v,j,i,s,t)) =e= 0;

Model ARP /ALL/;
ARP.optCR=0
Solve ARP using MIP minimizing z;

