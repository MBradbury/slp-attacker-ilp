int num_nodes = ...; // Number of nodes in the network
float comms_range = ...; // The range of the nodes

float attacker_range = ...; // The distance the attacker can hear messages from

int source_id = ...; // The id of the source node
int attacker_start_pos = ...; // The id of the node the attacker starts at

int source_messages = ...; // Number of messages the source sends
//float safety = ...; // The distance the attacker can move

range Nodes = 1..num_nodes;
{int} NodeSet = asSet(Nodes);

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

Coords Coordinates[i in Nodes] = ...;

float Distance[i in Nodes][j in Nodes] = 
	sqrt((Coordinates[i].x - Coordinates[j].x)^2 +
	     (Coordinates[i].y - Coordinates[j].y)^2 +
	     (Coordinates[i].z - Coordinates[j].z)^2);

{Edge} Edges = { <u,v> | u,v in Nodes : Distance[u][v] <= comms_range };
{int} Neighbours[i in Nodes] = { j | <i,j> in Edges };

{Edge} AttackerEdges = { <u,v> | u,v in Nodes : Distance[u][v] <= attacker_range };
{int} AttackerNeighbours[i in Nodes] = { j | <i,j> in AttackerEdges };

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
	(sum(e in AttackerEdges : e.v == source_id) moves[source_messages][e]) == 1;
};

{Edge} Used[m in Messages] = {e | e in AttackerEdges : moves[m][e] == 1};

execute
{
	writeln("Used edges=", Used)
}
