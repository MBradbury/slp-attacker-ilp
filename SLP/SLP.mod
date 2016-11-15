using CP;

tuple Coords
{
	float x;
	float y;
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

assert sink_id in Nodes;
assert forall (source_id in SourceIDs) source_id in Nodes;

Coords Coordinates[i in Nodes] = ...;

// Attacker
int attacker_start_pos = ...; // The id of the node the attacker starts at
float attacker_range = ...; // The distance the attacker can hear messages from
int attacker_move_history = ...; // The number of previous moves the attacker will consider when making the next move

assert attacker_start_pos in Nodes;

// Routing

float source_period = ...; // seconds between messages
float safety_period = ...;

int slots_per_second = ...;

// Time 0 is special, it is for setting the attacker's initial move
int max_time = ftoi(ceil(safety_period * slots_per_second));
range Times = 0..max_time; // One tenth of a second
int source_period_quantised = ftoi(ceil(source_period * slots_per_second));

range Messages = 1..ftoi(ceil(safety_period * source_period)); // Number of messages the source sends
int num_messages = card(Messages);

// Network constructs

float Distance[i in Nodes][j in Nodes] = 
	sqrt((Coordinates[i].x - Coordinates[j].x)^2 +
	     (Coordinates[i].y - Coordinates[j].y)^2);

// Eliminate self-self moves as when a node bcasts it will not receive a message sent by itself
sorted {Edge} Edges = { <u,v> | u,v in Nodes : Distance[u][v] <= comms_range && u != v };
{int} Neighbours[i in Nodes] = { j | <i,j> in Edges : i != j };

{Edge} SourceSelfEdges = { <u,v> | u,v in SourceIDs : u == v };

// It will stay at the source node once it reaches it.
sorted {Edge} AttackerEdges = { <u,v> | u,v in Nodes : Distance[u][v] <= attacker_range } diff
                              { <s,v> | s in SourceIDs, v in Nodes : s != v };
{int} AttackerNeighbours[i in Nodes] = { j | <i,j> in AttackerEdges : i != j };

// Others

// Which nodes broadcast which messages at which time.
dvar boolean broadcasts[Nodes][Messages][Times];

// What path does the attacker take
dvar boolean attacker_path[Times][AttackerEdges];

// Did the attacker move to n at t
dexpr int attacker_moved_to_at[n in Nodes][t in Times] =
	(sum (e in AttackerEdges : e.v == n) attacker_path[t][e]) == 1;

// Did the attacker do a self-self move at t
dexpr int attacker_self_move[t in Times] =
	(sum (e in AttackerEdges : e.u == e.v) attacker_path[t][e]) == 1;

// Did the attacker move because of the message m at t
dexpr int attacker_moved_because_at[m in Messages][t in Times] =
	(sum (e in AttackerEdges : e.u != e.v)
		(attacker_path[t][e] == 1 && broadcasts[e.v][m][t] == 1)) == 1;

maximize
	sum(s in SourceIDs) sum(e in AttackerEdges) (attacker_path[max_time][e] * Distance[s][e.v]);
  
//minimize
  	// Minimise the number of messages sent
	//sum(n in Nodes) sum(m in Messages) sum(t in Times) broadcasts[n][m][t];
	
	// Minimise the number of moves the attacker makes in response to a broadcast
	//sum(e in AttackerEdges) sum(m in Messages) sum(t in Times) (broadcasts[e.v][m][t] == attacker_path[t][e]);

subject to {

	ctR00: // No messages are sent at t=0
	forall (n in Nodes)
	  forall (m in Messages)
	    broadcasts[n][m][0] == 0;
	
	ctR01: // When do source nodes send messages
	forall (n in SourceIDs)
	  forall (m in Messages)
	    broadcasts[n][m][((m - 1) * source_period_quantised) + 1] == 1;
	
	ctR02: // No node sends more than one message concurrently
	forall (t in Times : t > 0) // Optimisation as t=0 no messages are sent
	  forall (n in Nodes)
	    (sum (m in Messages) broadcasts[n][m][t]) <= 1;
	
	ctR03: // Once a message is sent by one node it is never sent by that node again
	forall (m in Messages)
	  forall (n in Nodes)
	    forall (t1 in Times : t1 > 0)
	      (broadcasts[n][m][t1] == 1) => (sum (t2 in Times : t2 > t1) broadcasts[n][m][t2]) == 0;
	
	ctR04: // Messages can only be forwarded after a neighbour has sent it
	forall (n in Nodes : n not in SourceIDs) // Source nodes are exempt here, as they generate the message.
	  forall (m in Messages)
	    forall (t1 in Times : t1 > 0)
	      (broadcasts[n][m][t1] == 1) => 
	      	(sum (neigh in Neighbours[n]) sum(t2 in Times : 0 < t2 < t1) broadcasts[neigh][m][t2]) >= 1;
	
	ctR05: // Messages must reach the sink
	forall (m in Messages)
	  (sum (n in Neighbours[sink_id]) sum (t in Times : t > 0) broadcasts[n][m][t]) >= 1;
	
	// The first attacker move at the special time t=0 is the self-self move.
	ctA01:
	attacker_path[0][<attacker_start_pos,attacker_start_pos>] == 1;
	
	ctA02: // Attacker makes one move each time step (This may be the self-self move)
	forall (t in Times)
	  (sum (e in AttackerEdges) attacker_path[t][e]) == 1;
	
	ctA03: // Attacker must move from its current position (t > 0)
	forall (t in Times : t > 0)
	  (sum (e1, e2 in AttackerEdges : e1.v == e2.u)
	  	(attacker_path[t-1][e1] == 1 && attacker_path[t][e2] == 1)) == 1;
	
	// The attacker only moves when a message is broadcasted. It cannot move on its own.
	ctA04:
	forall (n in Nodes)
	  forall (t in Times : t > 0)
	    // If an attacker moves to n at t
	    ((sum (e in AttackerEdges : e.v == n && e.u != e.v) attacker_path[t][e]) == 1) =>
	      // Then it must be because n broadcasted m
	      (sum (m in Messages) broadcasts[n][m][t]) == 1;
	  	
	// The attacker only moves when a message is sent and that message has not been previously responded to
	ctA05: // Attacker can only move in response to sent messages
	forall (n in Nodes)
	  forall (m in Messages)
        forall (t in Times : t > 0)
		  // If the attacker moved to a neighbour of n at t-1
		  (sum (neigh in AttackerNeighbours[n]) attacker_moved_to_at[neigh][t-1]) == 1 &&
		  // and node n sent m at t
		  (broadcasts[n][m][t] == 1) &&
		  // and the attacker has never moved in response to m before
		  (sum (t2 in Times : 0 < t2 < t) (attacker_moved_because_at[m][t2] == 1)) == 0
		
		  // then the attacker moves in response to this message
		  => attacker_moved_to_at[n][t] == 1;
		  
	ctA06: // Attacker only moves once per message
	forall (t1 in Times : t1 > 0)
	  forall (m in Messages)
	    // If at t1 the attacker moved in response to the message m
	    attacker_moved_because_at[m][t1] == 1 =>
	      // Then at no subsequent time can the attacker move in response to m again
	      (sum (t2 in Times : t2 > t1) (attacker_moved_because_at[m][t2] == 1)) == 0;
	
	ctA07: // Attacker does not move when no neighbours send a message (t > 0)
	forall (t in Times : t > 0)
	  forall (e in AttackerEdges)
	    (attacker_path[t-1][e] == 1 && (sum (n in AttackerNeighbours[e.v]) sum (m in Messages) broadcasts[n][m][t]) == 0) =>
	      attacker_self_move[t] == 1;
	
	/*ctA08: // The attacker does not move back to the attacker_move_history previous locations
	if (attacker_move_history > 0)
	  forall (t in Times : t > attacker_move_history)
		forall (e in AttackerEdges : e.u != e.v)
		  // If the attacker moved to e.v at t
		  attacker_path[t][e] == 1 =>
		  	// Then the attacker shouldn't have moved to e.v on the past attacker_move_history moves
		  	(sum (t2 in Times : t-attacker_move_history <= t2 < t)
		  	  sum (e2 in AttackerEdges : e2.u != e2.v && e2.v == e.v)
		  	    attacker_path[t2][e2]) == 0;*/
};

{Edge} Used[t in Times] = {e | e in AttackerEdges : attacker_path[t][e] == 1};

{int} BroadcastsAt[n in Nodes][m in Messages] = {t | t in Times : broadcasts[n][m][t] == 1};

execute
{
	writeln("coords = ", Coordinates)
	writeln("neighbours = ", Neighbours)
	writeln("messages = ", num_messages)
	writeln("slots_per_second = ", slots_per_second)

	writeln("used_edges = \"\"\"", Used, "\"\"\"")
	writeln("broadcasted_at = \"\"\"", BroadcastsAt, "\"\"\"")
}
