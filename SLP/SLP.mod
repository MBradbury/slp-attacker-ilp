
tuple Coords
{
	float x;
	float y;
	float z;
}

tuple Edge
{
	int u;
	int v;
}

// Network
int num_nodes = ...; // Number of nodes in the network
float comms_range = ...; // The range of the nodes
{int} SourceIDs = ...; // The ids of the source nodes
int sink_id = ...;

range Nodes = 1..num_nodes;
//{int} NodeSet = asSet(Nodes);

Coords Coordinates[i in Nodes] = ...;

// Attacker
int attacker_start_pos = ...; // The id of the node the attacker starts at
float attacker_range = ...; // The distance the attacker can hear messages from

// Routing

float source_period = ...; // seconds between messages
float forwarding_delay = ...; // seconds
float safety_period = ...;

int slots_per_second = ...;

int max_time = ftoi(ceil(safety_period * slots_per_second)) - 1; // "-1" to avoid an extra slot
range Times = 0..max_time; // One tenth of a second
int source_period_quantised = ftoi(ceil(source_period * slots_per_second));

range Messages = 1..ftoi(ceil(safety_period * source_period)); // Number of messages the source sends

// Network constructs

float Distance[i in Nodes][j in Nodes] = 
	sqrt((Coordinates[i].x - Coordinates[j].x)^2 +
	     (Coordinates[i].y - Coordinates[j].y)^2 +
	     (Coordinates[i].z - Coordinates[j].z)^2);

// Eliminate self-self moves as when a node bcasts it will not receive a message sent by itself
sorted {Edge} Edges = { <u,v> | u,v in Nodes : Distance[u][v] <= comms_range && u != v };
{int} Neighbours[i in Nodes] = { j | <i,j> in Edges };

{Edge} SourceSelfEdges = { <u,v> | u,v in SourceIDs : u == v };

// It will stay at the source node once it reaches it.
{Edge} AttackerEdges = { <u,v> | u,v in Nodes : Distance[u][v] <= attacker_range } diff
                       { <s,v> | s in SourceIDs, v in Nodes : s != v };
{int} AttackerNeighbours[i in Nodes] = { j | <i,j> in AttackerEdges };

// Others

// Which nodes broadcast which messages at which time.
dvar boolean broadcasts[Nodes][Messages][Times];

// What path does the attacker take
dvar boolean attacker_path[Times][AttackerEdges];

//dexpr int receives[n in Nodes][m in Messages][t in Times] = sum(n1 in Neighbours[n]) broadcasts[n1][m][t-1];

maximize
	sum(s in SourceIDs) sum(e in AttackerEdges) (attacker_path[max_time][e] * Distance[s][e.v]);
  
  	// Minimise the number of messages sent
	//sum(n in Nodes) sum(m in Messages) sum(t in Times) broadcasts[n][m][t];
	
	// Minimise the number of moves the attacker makes in response to a broadcast
	//sum(e in AttackerEdges) sum(m in Messages) sum(t in Times) (broadcasts[e.v][m][t] == attacker_path[t][e]);

subject to {
	ct1: // When do source nodes send messages
	forall (n in SourceIDs)
	  forall (m in Messages)
	    broadcasts[n][m][(m - 1) * source_period_quantised] == 1;
	
	ct21: // No node sends more than one message at once
	forall (t in Times)
	  forall (n in Nodes)
	    (sum (m in Messages) broadcasts[n][m][t]) <= 1;
	
	ct22: // Once a message is sent by one node it is never sent by that node again
	forall (m in Messages)
	  forall (n in Nodes)
	    (sum (t in Times) broadcasts[n][m][t]) <= 1;
	
	ct3: // Messages can only be forwarded after a neighbour has sent it
	forall (n in Nodes : n not in SourceIDs) // Source nodes are exempt here, as they generate the message.
	  forall (m in Messages)
	    forall (t1 in Times)
	      broadcasts[n][m][t1] == 1 => 
	      	(sum (neigh in Neighbours[n]) sum(t2 in Times : t2 < t1) broadcasts[neigh][m][t2]) >= 1;
	
	ct4: // Messages must reach the sink
	forall (m in Messages)
	  (sum (n in Neighbours[sink_id], t in Times) broadcasts[n][m][t]) >= 1;
	
	ct5: // Attacker makes one move each time step (This may be the self-self move)
	forall (t in Times)
	  (sum (e in AttackerEdges) attacker_path[t][e]) == 1;
	
	ct6: // First attacker move must be from its starting position (t = 0)
	sum(e in AttackerEdges : e.u != attacker_start_pos) attacker_path[0][e] == 0;
	
	ct7: // Attacker must move from its current position
	forall (t in Times : t > 0)
	  (sum(e1,e2 in AttackerEdges : e1.v == e2.u)
	  	(attacker_path[t-1][e1] + attacker_path[t][e2] == 2)) == 1;
	
	ct8: // Attacker can only move in response to sent messages
	// If a message is sent by n at t, then at t+1 the attacker cannot move to a node other than n.
	forall (m in Messages)
	  forall (n in Nodes)
		forall (t in Times : t > 0)
		  // If n broadcasts at t and the attacker moved to a neighbour of n at t-1
		  broadcasts[n][m][t] == 1 && (sum (e in AttackerEdges : e.v in Neighbours[n]) attacker_path[t-1][e]) == 1 =>
		    // then the attacker can either move to n /*or stay where it is*/
		  	sum (e in AttackerEdges : e.v == n /*|| e.u == e.v*/) attacker_path[t][e] == 1;
	
	ct9: // Attacker only moves once per message
	forall (t1 in Times)
	  forall (m in Messages)
	    forall (e1 in AttackerEdges : e1.u != e1.v)
	      (attacker_path[t1][e1] == 1 && broadcasts[e1.v][m][t1] == 1) =>
	      	sum (t2 in Times : t1 != t2)
	      	  sum (e2 in AttackerEdges : e2.u != e2.v)
	      	    (broadcasts[e2.v][m][t2] + attacker_path[t2][e2] == 2) == 0;
};

{Edge} Used[t in Times] = {e | e in AttackerEdges : attacker_path[t][e] == 1};

execute
{
	writeln("Used edges=", Used)
}
