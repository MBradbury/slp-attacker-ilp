
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

range Nodes = 1..num_nodes;
//{int} NodeSet = asSet(Nodes);

Coords Coordinates[i in Nodes] = ...;

// Attacker
int attacker_start_pos = ...; // The id of the node the attacker starts at
float attacker_range = ...; // The distance the attacker can hear messages from

// Routing
int source_messages = ...; // Number of messages the source sends


float source_period = ...; // seconds between messages
float forwarding_delay = ...; // seconds
float safety_period = ...;

range AllMsgTimes = 0..ftoi(ceil((safety_period / forwarding_delay) * 10)); // One tenth of a second
range OneMsgTimes = 0..ftoi(ceil((safety_period / forwarding_delay) * 10) / (safety_period * source_period)); // One tenth of a second
int source_period_quantised = ftoi(ceil(source_period * 10));

int RoutingSendSeq[t in OneMsgTimes][i in Nodes] = ...;

// Network constructs

float Distance[i in Nodes][j in Nodes] = 
	sqrt((Coordinates[i].x - Coordinates[j].x)^2 +
	     (Coordinates[i].y - Coordinates[j].y)^2 +
	     (Coordinates[i].z - Coordinates[j].z)^2);

// Eliminate self-self moves as when a node bcasts it will not receive a message sent by itself
sorted {Edge} Edges = { <u,v> | u,v in Nodes : Distance[u][v] <= comms_range && u != v };
{int} Neighbours[i in Nodes] = { j | <i,j> in Edges };

{Edge} SourceSelfEdges = { <u,v> | u,v in SourceIDs : u == v };

// Eliminate self-self moves except for source-source. The attacker wants to reach the source asap.
// It will stay at the source node once it reaches it.
{Edge} AttackerEdges = { <u,v> | u,v in Nodes : Distance[u][v] <= attacker_range && u != v } union SourceSelfEdges;
{int} AttackerNeighbours[i in Nodes] = { j | <i,j> in AttackerEdges };

// Routing definitions

//{int} RoutingSend[i in Nodes] = ...; // When i sends a message, this is the set of nodes that will receive the message.
//{int} RoutingReceive[i in Nodes] = { j | j in Nodes : i in RoutingSend[j] }; // These are the nodes that could send a message to i.

//{Edge} RoutingSendEdges[i in Nodes] = { e | e in Edges : e.u == i && e.v in RoutingSend[i] };
//{Edge} RoutingReceiveEdges[i in Nodes] = { e | e in Edges : e.v == i && e.u in RoutingReceive[i] };

//{int} SourceBroadcastingAt[i in SourceIDs] = { t | t in Times : t % source_period_quantised == 0 };
//{int} BroadcastingAt[i in Nodes] = SourceBroadcastingAt[i] union { t | t in Times

//{int} ReceiveFromAt[i in Nodes][t in Times]

// Attacker

//{Edge} AttackerReceiveEdges[i in Nodes] = { e | e in AttackerEdges : e.u == i && e.v in RoutingReceive[i] };

// Others

// What is the cost to the attacker for moving from one node to another
float Cost[<i,j> in AttackerEdges] = Distance[i][j];

range Messages = 1..source_messages;

// The maximum number of moves that can be made
//range Safety = 1..ftoi(ceil(safety / (min(e in Edges) Cost[e])));

dvar boolean moves[Messages][AttackerEdges];

minimize
	sum(m in Messages) sum(e in AttackerEdges) Cost[e] * moves[m][e];

//minimize
//	sum(m in Messages) sum(e in AttackerEdges : e.u == e.v && e.u != source_id) moves[m][e];

subject to {
	// Only one move per message sent
	ct1:
	forall(m in Messages)
	  (sum(e in AttackerEdges) moves[m][e]) == 1;
	
	// Limit the moves that can be made
	ct2:
	forall(m in Messages)
	  // First message is from the starting position
	  if (m == 1)
	  	(sum(e in AttackerEdges : e.u == attacker_start_pos) moves[m][e]) == 1;
	  
	  // Subsequent messages can only start from the previous location
	  else
	  	(sum(e1 in AttackerEdges) sum(e2 in AttackerEdges : e2.u == e1.v)
	  		(moves[m-1][e1] + moves[m][e2] == 2)) == 1;
	
	// Must end at the source node
	ct3:
	(sum(e in AttackerEdges : e.v in SourceIDs) moves[source_messages][e]) == 1;
};

{Edge} Used[m in Messages] = {e | e in AttackerEdges : moves[m][e] == 1};

execute
{
	writeln("Used edges=", Used)
}
